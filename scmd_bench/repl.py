"""A persistent Lean REPL session. VENDORED from LeanBench `leanbench/repl.py`, itself vendored from
LeanDLLM `scmd/lean/repl.py` (both at the pins below).

scmd-bench is standalone by design, so it cannot import `scmd`. But this file is the one place
where "write it fresh" is the wrong call: every guard below is a *measured* failure, not a
defensive habit, and a clean reimplementation would rediscover each of them as a silently wrong
verdict. Vendored verbatim except for the couplings listed under VENDOR DELTA, so a diff against
the upstream file stays readable.

VENDOR DELTA vs LeanDLLM@3616c91 `scmd/lean/repl.py`:
  * the three pins are local constants (below) instead of `scmd.common.schemas` imports;
  * `LeanPaths.from_host` / `.from_source` -- which took SCMD `HostConfig` / `CorpusSource`
    objects -- are replaced by `LeanPaths.discover()`, which reads SCMD_BENCH_* env vars and
    falls back to the container layout, then to node1's frozen library. Nothing else is changed.

Upstream provenance is preserved below; it was itself ported from `LeanAI/benchmark/lean_repl.py`.

UPSTREAM DOCSTRING FOLLOWS
--------------------------
A persistent Lean REPL session. Ported from `LeanAI/benchmark/lean_repl.py`, with two changes.

PROVENANCE
──────────
Ported from LeanAI `benchmark/lean_repl.py` (stdlib-only, ~260 lines). Kept: the
`ReplResult` shape, `clean()`'s deliberate strictness, `lean_path()` asking *lake itself* rather than
hand-assembling, and the `PINNED_REPL_COMMIT` rationale. Two substantive changes:

1. **Paths are injected** via `LeanPaths` instead of derived from `Path(__file__).parent.parent`.
   The original resolved `_LIBRARY = _REPO/"library"` and `REPL_DIR = _REPO/"deps/tools/repl"`, which
   works in exactly one repo layout. Here mathlib lives in another project's tree on the laptop and
   in a frozen copy on `/data` on node1, and the two hosts agree about neither path.

2. **A timeout poisons the session** — GAP-M1-001. See below; this is the important one.

GAP-M1-001, MEASURED
────────────────────
The original spawned a reader thread per request and, on timeout, returned while leaving that thread
blocked on `self._proc.stdout`:

    t = threading.Thread(target=_read, daemon=True); t.start()
    if not done.wait(timeout_s):
        return ReplResult(False, error=f"REPL timed out after {timeout_s}s")   # thread still alive

The abandoned reader keeps consuming stdout. Measured: after one 3 s timeout on
`#eval (IO.sleep 12000 : IO Unit)`, the next command returned the *correct* answer but took
**9.16 s instead of 0.08 s** — it was served the tail of the previous reply. With two abandoned
readers the reply/request pairing can cross outright, which is silent data corruption: a verdict
attributed to the wrong proof. That is the exact failure `_lock` was there to prevent, reintroduced
by the timeout path.

Two changes fix it structurally rather than by patching the symptom:

  * **One reader thread for the session's lifetime**, feeding a `queue.Queue`. There is no
    per-request thread to abandon, and the reader ends when the process does.
  * **A timeout kills the process and marks the session poisoned.** Every later call raises
    `ReplPoisoned`. This is deliberately unforgiving: we cannot distinguish "hung" from "slow", and a
    reply still in flight for a request we gave up on is indistinguishable from the next request's
    reply. `ReplPool` catches `ReplPoisoned` and replaces the worker, so bulk callers never see it.

WHAT THIS IS NOT
────────────────
Not a tier authority and not a certificate. `clean()` reports what the elaborator said. §3's task
definition also requires every reference to come from `BASE ∪ A`, and that admissibility check lives
in `scmd.lean.verify` — a REPL "no errors" is evidence, not a verdict about the task.
"""

from __future__ import annotations

import collections
import json
import os
import queue
import subprocess
import threading
import time
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Final

#: The substrate the benchmark is graded against. These are LeanDLLM's pins and
#: LeanAI's alike -- node1's `/data/scmd/lean/library-v4.31.0` is a frozen `cp -a` of
#: `~/LeanAI/library` -- which is the fact that lets one benchmark serve both projects. A
#: benchmark whose verifier drifts is a benchmark whose old results are uncomparable, so these
#: are asserted at session start (`verify_pins`), never assumed.
PINNED_MATHLIB_REV: Final[str] = "fabf563a7c95a166b8d7b6efca11c8b4dc9d911f"
PINNED_LEAN_TOOLCHAIN: Final[str] = "leanprover/lean4:v4.31.0"
PINNED_REPL_COMMIT: Final[str] = "0cc6026"

#: A first command carrying `import Mathlib` pays the full elaboration (~13.8 s measured on both
#: hosts); later commands reuse that environment by id and cost ~0.08 s.
DEFAULT_IMPORT_TIMEOUT_S: Final[int] = 900
DEFAULT_CMD_TIMEOUT_S: Final[int] = 300


class ReplUnavailable(RuntimeError):
    """The REPL binary is absent or at the wrong revision.

    Raised rather than silently degrading to one-shot `lake env lean`. A harness that thinks it has a
    session but does not would be ~15 s slower per call in a way that is very hard to attribute.
    """


class ReplPoisoned(RuntimeError):
    """This session timed out or crashed and can no longer be trusted. GAP-M1-001.

    Not recoverable by design: the request→reply stream may be desynchronised, and continuing would
    risk attributing one proof's verdict to another. Construct a new session — or use `ReplPool`,
    which does that for you.
    """


class ReplOutcome(str, Enum):
    """What happened, as a total and disjoint classification.

    The distinction that matters is between the first three and the last three. `CLEAN`, `ERROR` and
    `SORRY` are statements about the *mathematics*. `TIMEOUT`, `CRASH` and `UNPARSEABLE` are
    statements about our *infrastructure*, and collapsing them into "did not prove it" is how a flaky
    machine turns into a claim about a model's ability. `is_verdict` is the guard.
    """

    CLEAN = "clean"
    ERROR = "error"
    SORRY = "sorry"
    TIMEOUT = "timeout"
    CRASH = "crash"
    UNPARSEABLE = "unparseable"

    @property
    def is_verdict(self) -> bool:
        """True only for outcomes that say something about the Lean source we submitted."""
        return self in (ReplOutcome.CLEAN, ReplOutcome.ERROR, ReplOutcome.SORRY)


def _first_dir(*cands: str | None) -> Path:
    """The first candidate that is an existing directory; the first non-empty one otherwise.

    Returning a path that does not exist (rather than raising here) keeps the error where it is
    informative: `ReplSession` refuses with the missing binary's full path.
    """
    given = [c for c in cands if c]
    for c in given:
        if Path(c).is_dir():
            return Path(c)
    return Path(given[0])


@dataclass(frozen=True)
class LeanPaths:
    """Where Lean, mathlib and the pinned REPL live. Injected, never inferred."""

    library: Path            # the lake project holding lean-toolchain + lake-manifest.json
    repl_dir: Path
    toolchain_bin: Path | None = None       # ~/.elan/bin — absent from node1's non-interactive PATH
    mathlib_root: Path | None = None
    mathlib_rev: str | None = None
    #: What THIS workspace is expected to be pinned at. `None` means "the project pins in
    #: `scmd.common.schemas`", which is every existing call site and is why this lands inert. A
    #: corpus_v3 source at another toolchain sets them, and `verify_pins` compares against these
    #: rather than against the global constants — otherwise a second workspace fails at session
    #: start for being what it is supposed to be.
    expect_toolchain: str | None = None
    expect_rev: str | None = None

    @property
    def repl_bin(self) -> Path:
        return self.repl_dir / ".lake" / "build" / "bin" / "repl"

    @classmethod
    def discover(cls) -> LeanPaths:
        """Where Lean is, from the environment, with node1's frozen library as the fallback.

        scmd-bench deliberately does NOT adopt SCMD's `config/hosts/<hostname>.toml` hard-error
        discipline. That rule exists because SCMD builds corpora, where an unknown host silently
        pointing at the wrong mathlib would poison artifacts that outlive the session. A benchmark
        run instead *records* its substrate in every result row and refuses at session start if the
        pins do not match -- so a wrong library cannot be mistaken for the right one either way, and
        a new host needs no config file to run the suite.
        """
        lib = _first_dir(os.environ.get("SCMD_BENCH_LIBRARY"), "/opt/lean/library",
                         "/data/scmd/lean/library-v4.31.0")
        repl = _first_dir(os.environ.get("SCMD_BENCH_REPL_DIR"), "/opt/lean/repl",
                          "/data/scmd/tools/repl")
        elan = Path(os.environ.get("SCMD_BENCH_TOOLCHAIN_BIN", str(Path.home() / ".elan" / "bin")))
        return cls(library=lib, repl_dir=repl,
                   toolchain_bin=elan if elan.is_dir() else None,
                   mathlib_root=lib / ".lake" / "packages" / "mathlib")

    def env(self) -> dict[str, str]:
        """A subprocess environment with elan on PATH.

        node1's non-interactive PATH does not include `~/.elan/bin`, so `lake` and `lean` resolve to
        nothing there — a failure that looks like a missing toolchain rather than a missing PATH.
        """
        e = dict(os.environ)
        if self.toolchain_bin is not None:
            e["PATH"] = f"{self.toolchain_bin}{os.pathsep}{e.get('PATH', '')}"
        return e


@dataclass
class ReplResult:
    ok: bool
    raw: dict = field(default_factory=dict)
    error: str = ""
    outcome: ReplOutcome = ReplOutcome.CLEAN
    elapsed_s: float = 0.0

    @property
    def env(self) -> int | None:
        return self.raw.get("env")

    @property
    def messages(self) -> list[dict]:
        return self.raw.get("messages") or []

    @property
    def errors(self) -> list[dict]:
        return [m for m in self.messages if m.get("severity") == "error"]

    @property
    def infos(self) -> list[dict]:
        """`info` messages — where `simp?` puts its `Try this: simp only [...]` suggestion.

        That is the mechanism §3.1's canonicalisation runs on (whitepaper §3.1 says "with the
        dependencies made explicit" without saying where they come from; harvesting the `?` variant's
        suggestion is the pin).
        """
        return [m for m in self.messages if m.get("severity") == "info"]

    @property
    def sorries(self) -> list[dict]:
        return self.raw.get("sorries") or []

    @property
    def tactics(self) -> list[dict]:
        """Per-tactic records when `allTactics` was requested.

        Each carries `pos`, `endPos`, `goals`, `tactic` (the source text) and `usedConstants`. The
        `tactic` text is a free exact oracle for span extraction, and `usedConstants` is a mechanical
        detector for the Appendix-A dependency over-count.
        """
        return self.raw.get("tactics") or []

    @property
    def infotree(self) -> list[dict]:
        return self.raw.get("infotree") or []

    def clean(self) -> bool:
        """No errors AND no `sorry` holes.

        Deliberately stricter than `ok`: `ok` means the REPL answered, `clean` means the elaborator
        was happy — and a `sorry` is not happy, it is the precise thing a repair loop goes looking
        for. Note a timeout is also not clean, which is correct but insufficient: use `outcome` to
        tell "the proof is wrong" from "our machine gave up".
        """
        return self.ok and not self.errors and not self.sorries

    def first_error_pos(self) -> tuple[int, int] | None:
        """`(line, column)` of the first error, which the repair loop maps to a tactic span.

        Lean reports 1-indexed lines and 0-indexed columns, in CODEPOINTS rather than bytes.
        """
        for m in self.errors:
            pos = m.get("pos") or {}
            if "line" in pos:
                return int(pos["line"]), int(pos.get("column", 0))
        return None

    @staticmethod
    def classify(raw: dict) -> ReplOutcome:
        if [m for m in (raw.get("messages") or []) if m.get("severity") == "error"]:
            return ReplOutcome.ERROR
        if raw.get("sorries"):
            return ReplOutcome.SORRY
        return ReplOutcome.CLEAN


def repl_revision(paths: LeanPaths) -> str:
    """The checked-out REPL revision, short form, or `"?"` if it cannot be determined."""
    try:
        out = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=str(paths.repl_dir),
                             capture_output=True, text=True, timeout=30)
    except (OSError, subprocess.TimeoutExpired):
        return "?"
    return out.stdout.strip() if out.returncode == 0 else "?"


def available(paths: LeanPaths) -> tuple[bool, str]:
    """`(usable, detail)` — is a REPL present at the pinned revision?

    A wrong revision is reported as UNUSABLE, not as a warning: `master` does not compile at v4.31.0,
    so if a differently-revisioned binary exists it was built against another toolchain and its
    behaviour is not the behaviour under test.
    """
    if not paths.repl_bin.is_file():
        return False, (
            f"no REPL binary at {paths.repl_bin}. Build it:\n"
            f"    git clone https://github.com/leanprover-community/repl {paths.repl_dir}\n"
            f"    cd {paths.repl_dir} && git checkout {PINNED_REPL_COMMIT} && lake build"
        )
    rev = repl_revision(paths)
    if rev != "?" and not (PINNED_REPL_COMMIT.startswith(rev) or rev.startswith(PINNED_REPL_COMMIT)):
        return False, (
            f"REPL at {rev}, not the pinned {PINNED_REPL_COMMIT}. `master` targets v4.33.0-rc1 and "
            f"does NOT compile at {PINNED_LEAN_TOOLCHAIN}; if this built, it built against a "
            "different toolchain and is not the substrate under test."
        )
    return True, f"repl @ {rev}"


_lean_path_cache: dict[Path, str] = {}


def lean_path(paths: LeanPaths, *, timeout_s: int = 300) -> str:
    """`LEAN_PATH` for the pinned mathlib, from lake itself — never hand-assembled.

    Cached per library root: the call costs ~1 s and every session in a 16-worker pool needs it.
    """
    if (hit := _lean_path_cache.get(paths.library)) is not None:
        return hit
    try:
        p = subprocess.run(["lake", "env", "printenv", "LEAN_PATH"], cwd=str(paths.library),
                           capture_output=True, text=True, timeout=timeout_s, env=paths.env())
    except (subprocess.TimeoutExpired, OSError) as exc:
        raise ReplUnavailable(
            f"`lake env printenv LEAN_PATH` failed in {paths.library}: {exc}. "
            "On node1, check that lean.toolchain_bin is configured — elan is not on the "
            "non-interactive PATH."
        ) from exc
    out = (p.stdout or "").strip()
    if not out:
        raise ReplUnavailable(
            f"`lake env printenv LEAN_PATH` returned nothing in {paths.library} "
            f"(exit {p.returncode}): {(p.stderr or '').strip()[:400]}"
        )
    _lean_path_cache[paths.library] = out
    return out


def verify_pins(paths: LeanPaths) -> list[str]:
    """Check the frozen library really is the revision every `[m]` figure was measured against.

    Returns a list of problems, empty if all good. Called at pool start rather than trusted: the
    whole reason node1 reads a frozen copy is that the original is another project's live tree, and
    the check is what makes "frozen" verifiable rather than aspirational.

    THE EXPECTED VALUES COME FROM THE PATHS WHEN THEY CARRY THEM, and from `scmd.common.schemas`
    otherwise. Reading only the module constants made the check un-satisfiable for any corpus_v3
    source at another toolchain: the pin is a property of the workspace, not of the project, and a
    second workspace would have failed at session start for correctly being what it says it is. The
    default is still the project pin, so every existing caller sees the identical check.
    """
    want_tc = paths.expect_toolchain or PINNED_LEAN_TOOLCHAIN
    want_rev = paths.expect_rev or PINNED_MATHLIB_REV
    problems: list[str] = []
    tc = paths.library / "lean-toolchain"
    if tc.is_file():
        got = tc.read_text(encoding="utf-8").strip()
        if got != want_tc:
            problems.append(f"lean-toolchain is {got!r}, expected {want_tc!r}")
    else:
        problems.append(f"no lean-toolchain at {tc}")

    if paths.mathlib_root is not None and (paths.mathlib_root / ".git").exists():
        try:
            out = subprocess.run(["git", "rev-parse", "HEAD"], cwd=str(paths.mathlib_root),
                                 capture_output=True, text=True, timeout=30)
            rev = out.stdout.strip() if out.returncode == 0 else ""
        except (OSError, subprocess.TimeoutExpired):
            rev = ""
        if rev and rev != want_rev:
            problems.append(
                f"package root is at {rev}, expected {want_rev}. Every §3.2 [m] figure was "
                "measured against the pinned revision; a corpus built here would be attributable "
                "to an unrecorded one."
            )
    ok, detail = available(paths)
    if not ok:
        problems.append(detail)
    return problems


class StreamDrain:
    """Consume a pipe forever, in bounded memory. The thing that stops `stderr=PIPE` deadlocking.

    THE BUG THIS PREVENTS
    ─────────────────────
    A `Popen` with `stderr=PIPE` and no reader gives the child a 64 KiB kernel pipe buffer and nothing
    more. Past that the child's next write to stderr BLOCKS — mid-elaboration, holding the reply that
    `send` is waiting for — and `send` then waits out its whole timeout and poisons the session for a
    reason unrelated to the request. `subprocess.run`/`communicate` drain both streams for exactly
    this reason; a hand-rolled Popen has to do it itself.
    Measured during the corpus pass: the pinned REPL writes **0 bytes** to stderr in normal operation,
    because Lean captures `#eval` output and reports it as a message instead. So this is defence in
    depth against a panic or a toolchain change, not a fix for an observed hang — and it is worth
    having precisely because the failure mode is a silent timeout rather than an error.

    Bounded because the point is to keep the PIPE empty, not to keep the text: an unbounded buffer
    would trade a deadlock for a slow leak in a session that lives for thousands of commands.
    """

    def __init__(self, stream: Any, *, name: str = "drain", maxlines: int = 200):
        self.tail: collections.deque[str] = collections.deque(maxlen=maxlines)
        self.n_bytes = 0
        self._stream = stream
        self.thread = threading.Thread(target=self._loop, daemon=True, name=name)
        self.thread.start()

    def _loop(self) -> None:
        try:
            if self._stream is None:
                return
            for line in self._stream:
                self.n_bytes += len(line)
                self.tail.append(line.rstrip("\n"))
        except (ValueError, OSError):
            pass          # stream closed under us: the process is gone, which `poll()` reports

    def text(self) -> str:
        return "\n".join(self.tail)

    def join(self, timeout: float = 5.0) -> None:
        self.thread.join(timeout=timeout)


class ReplSession:
    """One long-lived REPL process. `import Mathlib` once, then reuse the environment by id.

    Not shareable across threads for *concurrency* — the REPL speaks one JSON object at a time over
    stdin/stdout, so concurrent writers would interleave and desynchronise. `_lock` serialises
    `send`, because the failure mode (a reply matched to the wrong request) is silent and would
    corrupt a measurement rather than crash it. Use `ReplPool` for parallelism: N processes, not N
    threads on one.
    """

    def __init__(self, paths: LeanPaths, *, env_path: str | None = None,
                 check_pins: bool = True):
        ok, detail = available(paths)
        if not ok:
            raise ReplUnavailable(detail)
        if check_pins and (problems := verify_pins(paths)):
            raise ReplUnavailable("; ".join(problems))

        self.paths = paths
        self.detail = detail
        self._lock = threading.Lock()
        self._poisoned: str | None = None
        self._base_env: int | None = None
        self._spent = False
        self.jobs_served = 0

        env = paths.env()
        env["LEAN_PATH"] = env_path if env_path is not None else lean_path(paths)
        self._proc = subprocess.Popen(
            [str(paths.repl_bin)], cwd=str(paths.repl_dir), env=env,
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            text=True, bufsize=1)

        # ONE reader for the session's lifetime (GAP-M1-001). Replies are blank-line delimited, so
        # the reader assembles a whole reply before handing it over; there is no per-request thread
        # that a timeout could abandon on the shared stream.
        self._replies: queue.Queue[str] = queue.Queue()
        self._reader = threading.Thread(target=self._read_loop, daemon=True,
                                        name="repl-reader")
        self._reader.start()

        # Nobody reads stderr otherwise, and an unread pipe is a 64 KiB deadlock. See `StreamDrain`.
        self._stderr = StreamDrain(self._proc.stderr, name="repl-stderr")

    # ── plumbing ─────────────────────────────────────────────────────────────────────────────────
    def _read_loop(self) -> None:
        buf: list[str] = []
        try:
            assert self._proc.stdout is not None
            for line in self._proc.stdout:
                if line.strip() == "" and buf:
                    self._replies.put("".join(buf))
                    buf = []
                else:
                    buf.append(line)
        except (ValueError, OSError):
            pass          # stream closed under us: the process is gone, which `poll()` reports
        finally:
            if buf:
                self._replies.put("".join(buf))
            self._replies.put("")     # sentinel: EOF, so a waiting `send` is not stuck for its
                                      # whole timeout when the process has already died

    @property
    def stderr_tail(self) -> str:
        """The last ~200 lines the REPL wrote to stderr. Diagnostics only, never parsed."""
        return self._stderr.text()

    @property
    def stderr_bytes(self) -> int:
        """Total bytes seen on stderr. Above ~64 KiB an undrained pipe would have deadlocked."""
        return self._stderr.n_bytes

    def _poison(self, why: str) -> None:
        """Mark the session unusable and kill the process. Idempotent."""
        if self._poisoned is None:
            self._poisoned = why
        try:
            self._proc.kill()
        except Exception:  # noqa: BLE001 — already dead is the common case
            pass

    @property
    def poisoned(self) -> str | None:
        return self._poisoned

    def retire(self) -> None:
        """Close this session and mark the closure DELIBERATE rather than a failure.

        For a caller that knows the session is spent — after elaborating a 75 KB module whose 2-3 GB
        environment it will never reuse, say. `ReplPool` caps *failure* restarts per worker; without
        this distinction a job that frees its own memory would spend that budget and the pool would
        declare a perfectly healthy environment broken. Measured: 7,674 of 8,100 corpus files failed
        that way before the two were separated.
        """
        self._spent = True
        self.close()

    @property
    def spent(self) -> bool:
        """The caller declared this session done with. `ReplPool` reads it, never sets it."""
        return self._spent

    @property
    def alive(self) -> bool:
        return self._poisoned is None and self._proc.poll() is None

    def rss_bytes(self) -> int:
        """Proportional set size of the REPL process, for pool sizing.

        `Pss`, not `Rss`: mathlib's ~5.8 GB of oleans are mmapped and therefore SHARED between
        sessions, and Rss double-counts them — which would make a pool look 2-3x more expensive than
        it is and cap the worker count far below what 94 GB actually supports. Falls back to Rss
        where smaps_rollup is unavailable.
        """
        for name, key, scale in (("smaps_rollup", "Pss:", 1024), ("status", "VmRSS:", 1024)):
            try:
                text = Path(f"/proc/{self._proc.pid}/{name}").read_text(encoding="utf-8")
            except OSError:
                continue
            for line in text.splitlines():
                if line.startswith(key):
                    return int(line.split()[1]) * scale
        return 0

    # ── the wire ─────────────────────────────────────────────────────────────────────────────────
    def send(self, payload: dict, *, timeout_s: int = DEFAULT_CMD_TIMEOUT_S) -> ReplResult:
        """One request → one reply.

        On timeout the session is POISONED and the process killed (GAP-M1-001). We cannot distinguish
        "hung" from "merely slow", and a reply arriving after we gave up is indistinguishable on the
        wire from the *next* request's reply — so the conservative choice is the only safe one. A
        `ReplPool` worker is replaced transparently, so bulk callers pay a restart, not a wrong
        answer.
        """
        if self._poisoned is not None:
            raise ReplPoisoned(
                f"session poisoned: {self._poisoned}. Not recoverable — the request/reply stream "
                "may be desynchronised, and continuing risks attributing one proof's verdict to "
                "another. Construct a new session, or use ReplPool."
            )
        t0 = time.perf_counter()
        if (rc := self._proc.poll()) is not None:
            self._poison(f"process exited with code {rc}")
            return ReplResult(False, error=f"REPL exited with code {rc}",
                              outcome=ReplOutcome.CRASH, elapsed_s=time.perf_counter() - t0)

        with self._lock:
            try:
                assert self._proc.stdin is not None
                self._proc.stdin.write(json.dumps(payload) + "\n\n")
                self._proc.stdin.flush()
            except (BrokenPipeError, OSError) as exc:
                self._poison(f"write failed: {exc}")
                return ReplResult(False, error=f"write failed: {exc}",
                                  outcome=ReplOutcome.CRASH,
                                  elapsed_s=time.perf_counter() - t0)
            try:
                text = self._replies.get(timeout=timeout_s).strip()
            except queue.Empty:
                self._poison(f"timed out after {timeout_s}s")
                return ReplResult(False, error=f"REPL timed out after {timeout_s}s",
                                  outcome=ReplOutcome.TIMEOUT,
                                  elapsed_s=time.perf_counter() - t0)

        elapsed = time.perf_counter() - t0
        self.jobs_served += 1
        if not text:
            self._poison("REPL closed its output stream")
            # THE CHILD'S LAST WORDS ARE THE ONLY EVIDENCE OF WHY IT DIED, and until 2026-08-18 they
            # were dropped here. A SIGABRT writes its reason to stderr and nothing to stdout, so the
            # caller saw "stream closed" for every fatal cause alike -- an OOM, a kill, and
            # GAP-M1-013's `[init]` abort, whose repair keys on that exception TEXT and therefore
            # never fired on the one file it was written for (`Mathlib.Data.Prod.Basic`: the pass
            # landed, the ledger said LANDED, and the module stayed missing from records.jsonl).
            # The tail is APPENDED, never substituted: "stream closed" remains the outcome and this
            # is the reason for it. `stderr_tail` stays diagnostics-only in the sense that matters --
            # nothing branches on its structure -- but a substring test on a fatal error is not
            # parsing, and refusing to look at it cost a module.
            tail = self.stderr_tail.strip()
            return ReplResult(False, outcome=ReplOutcome.CRASH, elapsed_s=elapsed,
                              error="REPL returned nothing (stream closed)"
                                    + (f"; stderr: {tail[-600:]}" if tail else ""))
        try:
            raw = json.loads(text)
        except ValueError as exc:
            # NOT poisoned: a malformed reply is still a complete, delimited reply, so the stream is
            # in a known state. The caller learns the payload was unusable and can carry on.
            return ReplResult(False, error=f"unparseable REPL reply: {exc}; raw={text[:300]}",
                              outcome=ReplOutcome.UNPARSEABLE, elapsed_s=elapsed)
        if isinstance(raw, dict) and raw.get("message") and "env" not in raw:
            # The REPL reports its own top-level failures this way (e.g. an unknown environment id).
            return ReplResult(False, raw=raw, error=str(raw["message"]),
                              outcome=ReplOutcome.ERROR, elapsed_s=elapsed)
        return ReplResult(True, raw=raw, outcome=ReplResult.classify(raw), elapsed_s=elapsed)

    # ── the verbs SCMD actually needs ────────────────────────────────────────────────────────────
    #: Resolvable in any environment that has core `Init`, and in none that does not. `Nat` is the
    #: cheapest such name: it is in `Prelude`, so a probe that cannot see it saw no core at all.
    _CORE_PROBE: Final[str] = "#check Nat"

    def import_mathlib(self, *, extra: str = "", with_mathlib: bool = True,
                       timeout_s: int = DEFAULT_IMPORT_TIMEOUT_S) -> ReplResult:
        """Pay the mathlib elaboration ONCE and remember the environment id (~13.8 s measured).

        `with_mathlib=False` builds the header out of `extra` ALONE, for a workspace where
        `import Mathlib` is not merely unnecessary but wrong: 11 of corpus_v3's 79 sources have no
        mathlib in their workspace (`unknown module prefix 'Mathlib'`) and 6 more collide with it
        (`import PFR` after `import Mathlib` fails on a backported declaration the environment
        already contains). Everything else about the call is unchanged — the probe below is what
        makes either header safe. See `scmd.lean.cli.cmd_env_names` for the full measurement.

        AN UNRESOLVABLE IMPORT COMES BACK AS SUCCESS, WHICH IS WHY `extra` IS PROBED. Lean's
        `processHeader` answers an import it cannot resolve with a near-empty fallback environment
        plus a diagnostic in the header's own `messages`; the pinned REPL (`0cc6026`) threads that
        value into `Command.mkState` and never copies it into the reply, whose `messages` describe
        only the commands AFTER the header — and when the whole `cmd` is import lines there are
        none. So the caller sees `ok=True`, `errors=[]`, and a real environment id for an
        environment that does not even contain `Nat`.

        Measured, 2026-08-14 on node1: `import Mathlib\\nimport AlgoleanTests` (whose `.olean` was
        never built, because its package's `lakefile.toml` leaves it out of `defaultTargets`)
        returned exactly that, and `import ThisModuleDoesNotExistAtAll` reproduced it identically —
        so the shape is "module absent", not anything about the source. `dump_env_names` then died
        at `#[]` with `expected token`, four frames and one file away from the cause.

        The probe therefore runs ONLY when `extra` is given: a bare `import Mathlib` cannot be
        silently absent (nothing downstream would work at all), and every corpus pass that opens a
        session per job would otherwise pay a round trip for a case it cannot be in. A header with
        `with_mathlib=False` always carries `extra`, so it is always probed.
        """
        lines = (["import Mathlib"] if with_mathlib else []) + ([extra] if extra else [])
        if not lines:
            raise ValueError("import_mathlib(with_mathlib=False) needs `extra`: an empty header "
                             "would establish an empty environment and report success.")
        cmd = "\n".join(lines)
        r = self.send({"cmd": cmd}, timeout_s=timeout_s)
        if not (r.ok and r.env is not None):
            return r
        if extra:
            probe = self.send({"cmd": self._CORE_PROBE, "env": r.env})
            if not probe.ok or probe.errors:
                why = probe.errors[:1] or probe.error
                return ReplResult(
                    False, raw=r.raw, outcome=ReplOutcome.ERROR, elapsed_s=r.elapsed_s,
                    error=(f"the import reported success but its environment cannot resolve "
                           f"`Nat`, so a module in {extra.splitlines()!r} did not resolve and "
                           f"Lean fell back to an empty environment (the header's own diagnostic "
                           f"is dropped by the pinned REPL). Probe said: {why}. If this is a "
                           f"library target, its .olean is probably missing — build it "
                           f"(`lake build <Lib>` in its workspace) rather than trusting this env."))
        self._base_env = r.env
        return r

    @property
    def base_env(self) -> int | None:
        return self._base_env

    def run(self, code: str, *, env: int | None = None, all_tactics: bool = False,
            infotree: str | None = None,
            timeout_s: int = DEFAULT_CMD_TIMEOUT_S) -> ReplResult:
        """Elaborate `code` in a previously established environment (defaults to the mathlib one).

        `all_tactics=True` makes the reply carry a `tactics` array with exact `(line, col)` spans,
        each tactic's source text, and its `usedConstants`. That single flag is simultaneously the
        source for §6's tactic-granular masking, the repair loop's span map, and the over-count
        detector for §3.1 dependency extraction.
        """
        payload: dict[str, object] = {"cmd": code}
        e = env if env is not None else self._base_env
        if e is not None:
            payload["env"] = e
        if all_tactics:
            payload["allTactics"] = True
        if infotree is not None:
            payload["infotree"] = infotree
        return self.send(payload, timeout_s=timeout_s)

    def run_file(self, path: str | Path, *, all_tactics: bool = True,
                 infotree: str | None = "original",
                 timeout_s: int = DEFAULT_IMPORT_TIMEOUT_S) -> ReplResult:
        """Process a whole `.lean` file in its TRUE prefix environment.

        This is what makes declaration extraction principled rather than heuristic: each declaration
        is elaborated in the environment it was actually written in, with its own `import`s and
        `open`s in scope, so there is no bracket-depth scan and no `DECL` regex. The measurement
        scripts' regex extractor parsed 182,250 of 183,683 headers (99.2%); that number is a FLOOR
        this path must beat, not a target.
        """
        payload: dict[str, object] = {"path": str(path)}
        if all_tactics:
            payload["allTactics"] = True
        if infotree is not None:
            payload["infotree"] = infotree
        return self.send(payload, timeout_s=timeout_s)

    def header_env(self, header: str, *, timeout_s: int = DEFAULT_IMPORT_TIMEOUT_S) -> ReplResult:
        """Elaborate a file's prefix — everything above a declaration — yielding a LEAK-FREE environment.

        The target theorem does not exist in such an environment, which is a strictly better eval
        substrate than "import Mathlib and rename the target": there, a sampled proof could cite the
        target itself and score. Combined with `scmd.lean.verify`'s admissibility check, §9's
        "verified pass@k" measures the task §3 actually defines.
        """
        return self.send({"cmd": header}, timeout_s=timeout_s)

    # ── lifecycle ────────────────────────────────────────────────────────────────────────────────
    def close(self) -> None:
        """Terminate the process and REAP it. Every step is independently guarded.

        The reaping is the part that is easy to lose. An earlier version wrapped stdin-close,
        terminate and wait in one `try`, so on an already-killed process — which is precisely the
        state `_poison` leaves — `stdin.close()` raised `BrokenPipeError`, control jumped to the
        handler, and `wait()` never ran. The child then sat as a **zombie**: `kill()` had been
        called, so nothing was consuming memory, but the pid was still in the process table and
        `ReplPool.orphan_pids()` reported a leak that could not be explained. Caught by
        `test_the_pool_transparently_replaces_a_timed_out_worker`.
        """
        self._poisoned = self._poisoned or "closed"
        for step in (self._close_stdin, self._proc.terminate):
            try:
                step()
            except Exception:  # noqa: BLE001 — each step is best-effort and independent
                pass
        try:
            self._proc.wait(timeout=10)
        except Exception:  # noqa: BLE001
            try:
                self._proc.kill()
            except Exception:  # noqa: BLE001
                pass
            try:
                self._proc.wait(timeout=5)      # reap, or the pid lingers as a zombie
            except Exception:  # noqa: BLE001
                pass
        # Join both readers so nothing is left blocked on a closed fd. Bounded: each loop ends as
        # soon as its stream hits EOF, which terminating the process guarantees.
        self._reader.join(timeout=5)
        self._stderr.join(timeout=5)

    def _close_stdin(self) -> None:
        if self._proc.stdin and not self._proc.stdin.closed:
            self._proc.stdin.close()

    @property
    def pid(self) -> int:
        return self._proc.pid

    def __enter__(self) -> ReplSession:
        return self

    def __exit__(self, *exc) -> None:
        self.close()
