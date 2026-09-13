"""Static checks on submitted proof text, and the anonymised track's placeholder substitution.

Everything here runs BEFORE Lean and may only reject what it can justify from the text alone. The
authoritative checks -- what the proof names, what it declares, which axioms it rests on -- are
made by the elaborator in `scmd_bench.verify`; these exist because a few cheats leave no trace an
elaborator reports (`unsafe`, `implemented_by`, `set_option debug.skipKernelTC`).
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Final, Sequence

#: Tokens that may not appear in a submission outside comments and string literals.
#:  * `sorry`/`admit`: an incomplete proof (also caught by the REPL and by `sorryAx`).
#:  * `native_decide`: trusts the compiler (`Lean.ofReduceBool`; also caught by `#print axioms`).
#:  * `unsafe`, `implemented_by`, `extern`: replace a definition's kernel meaning with compiled code,
#:    which `#print axioms` does NOT see (SafeVerify's documented blind spot).
#:  * `run_tac`, `run_cmd`, `run_elab`, `run_meta`, `#eval`, `#exit`: arbitrary metaprograms, which
#:    could print a forged report line or mutate the environment.
#:  * command keywords that only make sense outside a proof body.
BANNED_TOKENS: Final[tuple[str, ...]] = (
    "sorry", "admit", "native_decide", "unsafe", "implemented_by", "extern",
    "run_tac", "run_cmd", "run_elab", "run_meta", "#eval", "#exit", "#print", "#check",
    "import", "axiom", "macro", "macro_rules", "syntax", "elab", "elab_rules", "notation",
    "attribute", "initialize", "builtin_initialize", "sb_check", "sb_uses",
)

#: `set_option NAME` prefixes a submission may not set. Everything that changes the budget (so the
#: deterministic limit stays the benchmark's), the kernel's trust, or the elaborator's internals.
#: Other options (`push_neg.use_distrib`, `linter.*`, `pp.*`) are harmless and appear in mathlib
#: proofs, so they are allowed.
BANNED_OPTION_PREFIXES: Final[tuple[str, ...]] = (
    "maxHeartbeats", "maxRecDepth", "synthInstance", "debug", "trust", "backward", "compiler",
    "Elab", "internal", "interpreter", "exponentiation", "profiler", "tactic.skipAssignedInstances",
    "autoImplicit", "relaxedAutoImplicit", "maxSynthPendingDepth", "warningAsError",
)

_PLACEHOLDER: Final = re.compile(r"⟪p(\d+)⟫")


def mask_comments_and_strings(text: str) -> str:
    """`text` with every comment and string literal replaced by spaces, offsets preserved.

    Nested block comments (`/- /- -/ -/`) are tracked, as Lean nests them. Character literals are
    not: `'` is also an identifier character (`h'`), and no banned token fits in one anyway.
    """
    out = list(text)
    i, n, depth = 0, len(text), 0
    in_str = False
    while i < n:
        if depth:
            if text.startswith("/-", i):
                depth += 1; out[i] = out[i + 1] = " "; i += 2; continue
            if text.startswith("-/", i):
                depth -= 1; out[i] = out[i + 1] = " "; i += 2; continue
            if text[i] != "\n":
                out[i] = " "
            i += 1
            continue
        if in_str:
            if text[i] == "\\" and i + 1 < n:
                out[i] = out[i + 1] = " "; i += 2; continue
            if text[i] == '"':
                in_str = False
            if text[i] != "\n":
                out[i] = " "
            i += 1
            continue
        if text.startswith("/-", i):
            depth = 1; out[i] = out[i + 1] = " "; i += 2; continue
        if text.startswith("--", i):
            j = text.find("\n", i)
            j = n if j < 0 else j
            for q in range(i, j):
                out[q] = " "
            i = j
            continue
        if text[i] == '"':
            in_str = True
            out[i] = " "
        i += 1
    return "".join(out)


def _word_re(tok: str) -> re.Pattern[str]:
    # An identifier character on either side means the token is part of a longer name
    # (`sorry_lemma`, `h.sorry`, `Foo.extern_bar`).
    return re.compile(r"(?<![\w.'#])" + re.escape(tok) + r"(?![\w'])")


_BANNED_RES: Final = [(t, _word_re(t)) for t in BANNED_TOKENS]
_SET_OPTION: Final = re.compile(r"(?<![\w.'])set_option\s+([\w.]+)")


def static_violations(proof: str) -> list[str]:
    """Human-readable rule violations found in the text. Empty means "go to Lean"."""
    masked = mask_comments_and_strings(proof)
    found = [f"forbidden token `{t}`" for t, rx in _BANNED_RES if rx.search(masked)]
    for m in _SET_OPTION.finditer(masked):
        opt = m.group(1)
        if any(opt == p or opt.startswith(p + ".") or opt.startswith(p) for p in BANNED_OPTION_PREFIXES):
            found.append(f"forbidden option `set_option {opt}`")
    return found


@dataclass
class Substituted:
    """The anonymised track's substitution result."""

    text: str
    #: `(start, end)` character spans in `text` that came from a placeholder.
    spans: list[tuple[int, int]] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)


def substitute_placeholders(proof: str, names: Sequence[str]) -> Substituted:
    """`⟪p17⟫` -> `_root_.<real name of slot 17>`, recording where each substitution landed.

    `_root_.` so the reference is ABSOLUTE: a proof elaborates inside the target's namespaces and
    opens, where a bare `Foo.bar` can resolve to `Baz.Foo.bar`. Placeholders inside comments and
    strings are left alone -- they are not references.
    """
    masked = mask_comments_and_strings(proof)
    out: list[str] = []
    spans: list[tuple[int, int]] = []
    errors: list[str] = []
    last, pos = 0, 0
    for m in _PLACEHOLDER.finditer(proof):
        if masked[m.start():m.end()].strip() == "":
            continue                       # inside a comment or string
        slot = int(m.group(1))
        out.append(proof[last:m.start()])
        pos += m.start() - last
        if slot >= len(names):
            errors.append(f"placeholder ⟪p{slot}⟫ is out of range for K={len(names)}")
            rep = m.group(0)
        else:
            rep = "_root_." + names[slot]
            spans.append((pos, pos + len(rep)))
        out.append(rep)
        pos += len(rep)
        last = m.end()
    out.append(proof[last:])
    return Substituted("".join(out), spans, errors)


def spells(ident: str, const: str) -> bool:
    """Does the identifier TEXT spell the constant, i.e. is it a trailing run of its components?

    `Finset.sum_comm` and `sum_comm` spell `Finset.sum_comm`; `h.trans` does not spell `Eq.trans`
    (that is generalized field notation, the constant reached through a local's type).
    """
    raw = ident.lstrip("@")
    if raw.startswith("_root_."):
        raw = raw[len("_root_."):]
    rc = raw.split(".")
    cc = const.split(".")
    return len(rc) <= len(cc) and cc[-len(rc):] == rc
