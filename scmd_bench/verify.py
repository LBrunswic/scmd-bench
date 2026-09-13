"""The grader: one Lean session, one item's prefix environment at a time, and the verification contract.

THE CONTRACT (RULES.md section 3, and this is its implementation)
------------------------------------------------------------------
An attempt is SOLVED iff all of these hold:

  1. it passes the static checks (`scmd_bench.submission`);
  2. `theorem <ns>.sb_target <signature> := <proof>` elaborates with no error and no `sorry` in the
     item's FILE-PREFIX environment, under mathlib's lakefile options and the default heartbeat
     budget -- the target and everything after it in its file do not exist there;
  3. the command declares that constant, and nothing follows it (a second command is refused by
     position, and the declaration keywords a proof body could smuggle are refused statically);
  4. its axioms (Lean's `collectAxioms`, what `#print axioms` prints) are only `propext`,
     `Classical.choice`, `Quot.sound`;
  5. every constant the proof NAMES (an identifier in the proof's own source that elaborates to a
     constant and spells it) that is a THEOREM is in BASE, or is ambient -- defined outside
     `Mathlib.*`, or private, or already named by the target's own signature. Definitions,
     structures, instances and structure/class projections -- including projections onto Prop
     fields, the laws of a class -- are vocabulary, not premises;
  6. anonymised track only: a BASE premise the proof names by its REAL name must be a name some
     prompt text showed. Otherwise the system could only have known it from memorising mathlib.

What a tactic REACHES without naming it (`simp`'s default set, instance search, `exact?`) is not
forbidden -- the default simp set alone is 97,393 lemmas and no real proof avoids it -- and is
reported per attempt as `reach_outside_base`. The ambient floor (`meta.ambient_solvable`) is what
keeps that reach from being mistaken for the task: the headline is scored on items no
zero-parameter tactic closes.

ONE SESSION, RETIRED OFTEN
--------------------------
The REPL retains every environment it elaborates, and a file prefix is a large one (LeanDLLM
measured node1 going from 90 GB available to 2 GB elaborating one prefix per target). The session
is replaced after `prefix_budget` prefixes. A wall-clock timeout POISONS the session by design
(a late reply is indistinguishable from the next request's), so it is also replaced then -- only
between attempts, never inside one.
"""

from __future__ import annotations

import re
import secrets
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Final, Iterable

from scmd_bench.context import declaration_context, render_declaration
from scmd_bench.repl import LeanPaths, ReplResult, ReplSession
from scmd_bench.schema import Attempt, Fault, Item, Outcome
from scmd_bench.submission import spells, static_violations, substitute_placeholders

PREAMBLE: Final[Path] = Path(__file__).parent / "lean" / "preamble.lean"

STANDARD_AXIOMS: Final[frozenset[str]] = frozenset({"propext", "Classical.choice", "Quot.sound"})

#: Wall-clock guard per command. NOT the budget a proof is held to -- that is Lean's deterministic
#: `maxHeartbeats` (mathlib's default, or what the declaration's own `set_option ... in` sets). A
#: wall-clock limit depends on machine load, so a firing is charged to the harness and re-run.
DEFAULT_CMD_TIMEOUT_S: Final[int] = 300
DEFAULT_PREFIX_TIMEOUT_S: Final[int] = 1200

_SYNTAX_MARKERS: Final = ("unexpected token", "unexpected identifier", "expected term",
                          "unexpected end of input", "expected command", "unterminated comment",
                          "no space before", "expected ':='")
_HEARTBEAT_MARKERS: Final = ("(deterministic) timeout", "maximum recursion depth",
                             "maxRecDepth", "heartbeats")


@dataclass
class _Report:
    #: `(line, col, constant, module or "_", private, is_theorem, identifier text)`
    cited: list[tuple[int, int, str, str, bool, bool, str]]
    decls: list[str]
    end: tuple[int, int] | None
    axioms: list[str] | None = None
    uses: set[str] | None = None


def _parse_report(r: ReplResult, tag: str) -> _Report:
    #: `(line, col, constant, module or "_", private, is_theorem, identifier text)`
    cited: list[tuple[int, int, str, str, bool, bool, str]] = []
    decls: list[str] = []
    end = None
    axioms: list[str] | None = None
    uses: set[str] | None = None
    pc, pd, pe = f"SB_{tag}_CITED ", f"SB_{tag}_DECL ", f"SB_{tag}_END "
    pan, pa = f"SB_{tag}_AXIOMS_N ", f"SB_{tag}_AXIOM "
    pun, pu = f"SB_{tag}_USES_N ", f"SB_{tag}_USES "
    for m in r.infos:
        data = str(m.get("data", ""))
        if data.startswith(pc):
            parts = data[len(pc):].split(" ", 6)
            if len(parts) == 7:
                cited.append((int(parts[0]), int(parts[1]), parts[2], parts[3],
                              parts[4] == "1", parts[5] == "t", parts[6]))
        elif data.startswith(pd):
            decls.append(data[len(pd):].strip())
        elif data.startswith(pe):
            a, b = data[len(pe):].split()
            end = (int(a), int(b))
        elif data.startswith(pan):
            axioms = [] if axioms is None else axioms
        elif data.startswith(pa):
            axioms = (axioms or []) + [data[len(pa):].strip()]
        elif data.startswith(pun):
            uses = set() if uses is None else uses
        elif data.startswith(pu):
            uses = (uses or set()) | {data[len(pu):].strip()}
    return _Report(cited, decls, end, axioms, uses)


def _line_col(text: str, offset: int) -> tuple[int, int]:
    """Lean's `(line, column)` for a character offset: 1-based line, 0-based codepoint column."""
    before = text[:offset]
    line = before.count("\n") + 1
    col = offset - (before.rfind("\n") + 1)
    return line, col


def _errtext(r: ReplResult) -> str:
    return " || ".join(str(e.get("data", "")) for e in r.errors)[:1500]


class Grader:
    """A live Lean session plus the verification contract. One per worker process."""

    def __init__(self, paths: LeanPaths | None = None, *, mathlib_root: str | Path | None = None,
                 cmd_timeout_s: int = DEFAULT_CMD_TIMEOUT_S,
                 prefix_timeout_s: int = DEFAULT_PREFIX_TIMEOUT_S, prefix_budget: int = 6,
                 max_rss_gb: float = 6.0):
        self.paths = paths or LeanPaths.discover()
        root = mathlib_root or self.paths.mathlib_root
        if root is None:
            raise ValueError("no mathlib source root: set SCMD_BENCH_LIBRARY")
        self.mathlib_root = Path(root)
        self.cmd_timeout_s = cmd_timeout_s
        self.prefix_timeout_s = prefix_timeout_s
        self.prefix_budget = prefix_budget
        #: The session is ALSO retired when its resident memory passes this. Measured 2026-09-13:
        #: with a count budget of 12, eight workers reached 13-16 GB RSS each on mathlib prefixes and
        #: pushed a shared 94 GB host into swap. A count cannot bound a quantity that varies 10x per
        #: prefix; the process's own RSS can.
        self.max_rss_gb = max_rss_gb
        #: Per-session secret. A submission cannot print a report line it cannot spell.
        self.tag = "N" + secrets.token_hex(8)
        self._preamble = PREAMBLE.read_text(encoding="utf-8")
        self.session: ReplSession | None = None
        self._env: dict[str, int] = {}
        self._built = 0
        self.restarts = 0
        self.prefix_s = 0.0

    # ── session and environments ────────────────────────────────────────────────────────────────
    def _new_session(self) -> None:
        if self.session is not None:
            try:
                self.session.close()
            except Exception:  # noqa: BLE001 -- a poisoned session is the expected case
                pass
            self.restarts += 1
        self.session = ReplSession(self.paths)
        self._env.clear()
        self._built = 0

    def _alive(self) -> bool:
        return (self.session is not None and self.session.poisoned is None
                and self.session.alive)

    def env_for(self, item: Item) -> tuple[int | None, str]:
        """The item's prefix environment with the preamble established on top. Cached per session."""
        g = item.grading
        key = f"{g['file']}::{g['char_start']}"
        if not self._alive():
            self._new_session()
        if key in self._env:
            return self._env[key], ""
        if self._built >= self.prefix_budget or self._rss_gb() > self.max_rss_gb:
            self._new_session()
        path = self.mathlib_root / g["file"]
        try:
            source = path.read_text(encoding="utf-8")
        except OSError as exc:
            return None, f"cannot read {path}: {exc}"
        ctx = declaration_context(source, int(g["char_start"]), g.get("prefix_source") or "")
        t0 = time.perf_counter()
        assert self.session is not None
        r = self.session.send({"cmd": ctx}, timeout_s=self.prefix_timeout_s)
        self.prefix_s += time.perf_counter() - t0
        self._built += 1
        if not r.ok or r.env is None:
            if not self._alive():
                self._new_session()
            return None, f"prefix {r.outcome.value}: {(r.error or '')[:300]}"
        # Errors inside a mathlib file prefix are not fatal: 177 mathlib files do not elaborate
        # cleanly under the REPL at all, and what matters is whether the target then does. The item
        # builder keeps only items whose gold proof verifies here, which is the real test.
        pre = self.session.run(self._preamble, env=r.env, timeout_s=self.cmd_timeout_s)
        if not pre.ok or pre.errors or pre.env is None:
            return None, f"preamble did not elaborate in the prefix env: {_errtext(pre)[:300]}"
        self._env[key] = pre.env
        return pre.env, ""

    def _rss_gb(self) -> float:
        proc = getattr(self.session, "_proc", None)
        if proc is None:
            return 0.0
        try:
            for line in Path(f"/proc/{proc.pid}/status").read_text().splitlines():
                if line.startswith("VmRSS:"):
                    return int(line.split()[1]) / 1e6
        except OSError:
            pass
        return 0.0

    # ── the contract ────────────────────────────────────────────────────────────────────────────
    def grade(self, item: Item, proof: str, *, track: str, k: int,
              sample_idx: int = 0) -> Attempt:
        t0 = time.perf_counter()
        a = Attempt(item_id=item.item_id, sample_idx=sample_idx, outcome=Outcome.ERROR)
        try:
            self._grade(a, item, proof, track=track, k=k)
        finally:
            a.verify_s = round(time.perf_counter() - t0, 3)
        return a

    def _grade(self, a: Attempt, item: Item, proof: str, *, track: str, k: int) -> None:
        base = item.base(k)
        base_names = [s["name"] for s in base]
        body = (proof or "").strip()
        if not body:
            a.outcome, a.fault, a.detail = Outcome.ABSTAINED, Fault.MODEL, "empty proof"
            return
        bad = static_violations(body)
        if bad:
            a.outcome, a.fault, a.detail = Outcome.ILLEGAL, Fault.MODEL, "; ".join(bad)
            return
        spans: list[tuple[int, int]] = []
        if track == "anon":
            sub = substitute_placeholders(body, base_names)
            if sub.errors:
                a.outcome, a.fault, a.detail = Outcome.ILLEGAL, Fault.MODEL, "; ".join(sub.errors)
                return
            body, spans = sub.text, sub.spans

        env, why = self.env_for(item)
        if env is None:
            a.outcome, a.fault, a.detail = Outcome.VOID, Fault.ITEM, why
            return
        g = item.grading
        src, _name, proof_off = render_declaration(g["stmt_source"], g.get("prefix_source") or "",
                                                   body)
        # SYNCHRONOUS ELABORATION. Lean 4.31 elaborates a theorem's proof asynchronously by default,
        # so when `sb_check`'s own code runs the constant may not be in the environment yet --
        # measured: a correct gold proof (`expMulMulExp_eq_expUnitary_mul_mul_expUnitary`) came
        # back with no declaration while `#check` in the reply environment found it. A verdict read
        # before the proof has finished elaborating is not a verdict.
        head = f"sb_check {self.tag} set_option Elab.async false in\n"
        cmd = head + src
        proof_start = len(head) + proof_off
        assert self.session is not None
        r = self.session.run(cmd, env=env, timeout_s=self.cmd_timeout_s)
        if not r.ok:
            a.outcome = Outcome.TIMEOUT if r.outcome.value == "timeout" else Outcome.ERROR
            a.fault, a.detail = Fault.HARNESS, f"{r.outcome.value}: {(r.error or '')[:300]}"
            if not self._alive():
                self._new_session()
            return
        if r.errors:
            txt = _errtext(r)
            low = txt.lower()
            if any(m in low for m in _HEARTBEAT_MARKERS):
                a.outcome = Outcome.TIMEOUT
            elif any(m in low for m in _SYNTAX_MARKERS):
                a.outcome = Outcome.MALFORMED
            else:
                a.outcome = Outcome.REJECTED
            a.fault, a.detail = Fault.MODEL, txt
            return
        if r.sorries:
            a.outcome, a.fault, a.detail = Outcome.REJECTED, Fault.MODEL, "proof leaves `sorry`"
            return
        rep = _parse_report(r, self.tag)
        if rep.end is None:
            a.outcome, a.fault = Outcome.ERROR, Fault.HARNESS
            a.detail = "no report from sb_check (preamble missing from the environment?)"
            return
        if rep.end < _line_col(cmd, len(cmd.rstrip())):
            a.outcome, a.fault = Outcome.ILLEGAL, Fault.MODEL
            a.detail = "text follows the declaration: a submission is ONE proof body"
            return
        if len(rep.decls) != 1 or rep.axioms is None:
            a.outcome, a.fault = Outcome.ERROR, Fault.HARNESS
            a.detail = f"elaborated cleanly but the declaration was not reported ({rep.decls})"
            return
        extra = sorted(set(rep.axioms) - STANDARD_AXIOMS)
        a.evidence["axioms_extra"] = extra
        if extra:
            a.outcome, a.fault = ((Outcome.REJECTED, Fault.MODEL) if extra == ["sorryAx"]
                                  else (Outcome.ILLEGAL, Fault.MODEL))
            a.detail = f"non-standard axioms: {extra}"
            return

        start_lc = _line_col(cmd, proof_start)
        stmt_named = {row[2] for row in rep.cited if (row[0], row[1]) < start_lc}
        shown = _shown_text(item, k)
        base_set = set(base_names)
        outside: list[str] = []
        memorised: list[str] = []
        cited_base: set[str] = set()
        span_lc = [(_line_col(cmd, proof_start + s), _line_col(cmd, proof_start + e))
                   for s, e in spans]
        for ln, col, c, module, private, is_thm, raw in rep.cited:
            if (ln, col) < start_lc:
                continue
            ambient = module != "_" and not module.startswith("Mathlib.")
            # Only THEOREMS are premises a proof can be charged for naming. A definition, structure,
            # projection or instance is the language a statement is written in -- `Star.star`,
            # `colimit.isColimit` -- and naming one proves nothing by itself; anything it unfolds
            # to that IS a lemma still has to be named or reached.
            if ambient or private or not is_thm or not spells(raw, c):
                continue
            if c in base_set:
                cited_base.add(c)
                if track == "anon" and not any(lo <= (ln, col) < hi for lo, hi in span_lc):
                    if not _shown(c, raw, shown):
                        memorised.append(c)
                continue
            if c in stmt_named:
                continue
            outside.append(c)
        a.evidence["cited_base"] = sorted(cited_base)
        if outside:
            a.outcome, a.fault = Outcome.ILLEGAL, Fault.MODEL
            a.evidence["outside_base_named"] = sorted(set(outside))
            a.detail = f"names constants outside BASE: {sorted(set(outside))[:8]}"
            return
        if memorised:
            a.outcome, a.fault = Outcome.ILLEGAL, Fault.MODEL
            a.evidence["unshown_real_names"] = sorted(set(memorised))
            a.detail = ("anonymised track: names BASE premises by real names no prompt text "
                        f"showed: {sorted(set(memorised))[:8]}")
            return

        used = rep.uses or set()
        reach = sorted(u for u in used - base_set - stmt_named if not _obviously_ambient(u))
        a.evidence["n_used"] = len(used)
        a.evidence["reach_outside_base"] = reach[:50]
        a.evidence["n_reach_outside_base"] = len(reach)
        a.outcome, a.fault = Outcome.SOLVED, Fault.NONE
        a.detail = "verified"

    def unresolvable(self, item: Item, k: int) -> list[str] | str:
        """BASE names of this K that do NOT exist in the item's environment. A harness check.

        Every eval BASE is drawn in-closure, so this should always be empty; the item builder keeps
        only items for which it is, and the count of drops is reported rather than assumed zero.
        """
        env, why = self.env_for(item)
        if env is None:
            return f"void: {why}"
        names = [s["name"] for s in item.base(k)]
        assert self.session is not None
        code = "\n".join(f"#check @_root_.{n}" for n in names)
        r = self.session.run(code, env=env, timeout_s=self.cmd_timeout_s)
        if not r.ok:
            return f"{r.outcome.value}"
        bad = []
        for e in r.errors:
            line = int((e.get("pos") or {}).get("line", 0))
            if 1 <= line <= len(names):
                bad.append(names[line - 1])
        return sorted(set(bad))

    def close(self) -> None:
        if self.session is not None:
            self.session.close()

    def __enter__(self) -> Grader:
        return self

    def __exit__(self, *exc: Any) -> None:
        self.close()


def _shown_text(item: Item, k: int) -> str:
    return "\n".join([item.prompt["target"], *(s["rest"] for s in item.base(k))])


def _shown(const: str, raw: str, shown: str) -> bool:
    for needle in {const, raw.lstrip("@").removeprefix("_root_.")}:
        if re.search(r"(?<![\w.'])" + re.escape(needle) + r"(?![\w'])", shown):
            return True
    return False


_AMBIENT_ROOTS: Final = ("Eq.", "Iff.", "And.", "Or.", "Not.", "Nat.", "Int.", "List.", "Array.",
                         "Bool.", "Decidable.", "True.", "False.", "HEq.", "Exists.", "Classical.",
                         "Function.", "Lean.", "Std.", "Init.", "instDecidable", "of_eq_true",
                         "eq_self", "congrArg", "id", "rfl")


def _obviously_ambient(name: str) -> bool:
    """A cheap, REPORT-ONLY filter so `reach_outside_base` is readable. Never part of a verdict."""
    return name.startswith(_AMBIENT_ROOTS) or "._" in name or name.startswith("_")


def grade_many(grader: Grader, item: Item, proofs: Iterable[tuple[int, str]], *, track: str,
               k: int) -> list[Attempt]:
    return [grader.grade(item, p, track=track, k=k, sample_idx=i) for i, p in proofs]
