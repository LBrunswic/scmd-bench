"""The environment an item is graded in, and the declaration a submission is placed into.

VENDORED from LeanDLLM `scmd/lean/env_cache.py` (`declaration_context` and its helpers) and
`scmd/lean/verify.py` (`strip_attributes`, `Target.render`) at `3616c91`. Each rule below is a
measured failure of the gold-proof oracle upstream, and the docstrings keep the measurement.

THE SUBSTRATE IS THE TARGET'S OWN FILE PREFIX
---------------------------------------------
A target is a statement sliced out of its file. It leans on `variable` binders, `open`s, local
notation and `namespace`s that live above it, so under a bare `import Mathlib` most targets do not
elaborate (LeanBench measured 2/50). `source[:char_start]` is the environment the declaration was
written in, and it is also LEAK-FREE: the target and everything after it do not exist there, so a
proof cannot cite the theorem it is proving or a later restatement of it.
"""

from __future__ import annotations

from typing import Final

#: mathlib's own `leanOptions`, which the REPL does NOT apply -- it reads a file, not a lake target.
#: Transcribed from `lakefile.lean`'s `mathlibLeanOptions`, minus the warning-only linters.
#: `maxSynthPendingDepth 3` is load-bearing (Lean's default is 1; real declarations fail to
#: synthesize instances without it). `autoImplicit false` is the other half: under the default an
#: unknown identifier silently becomes a bound variable, so a proof citing a name that is NOT in
#: scope would elaborate.
MATHLIB_LEAN_OPTIONS: Final[str] = (
    "set_option autoImplicit false\n"
    "set_option maxSynthPendingDepth 3\n"
    "set_option pp.unicode.fun true\n"
)

#: mathlib v4.31.0 is on Lean's module system: import lines read `public import Mathlib.X` and
#: `public meta import Mathlib.Y`. Keying on a line's first token matched almost no imports upstream
#: (oracle 0.005/200), so modifiers are skipped first.
_COMMAND_MODIFIERS: Final[frozenset[str]] = frozenset({
    "public", "meta", "private", "protected", "noncomputable", "scoped", "local", "partial",
    "unsafe", "nonrec",
})

#: Commands that can wrap a declaration with `... in`. Anything else ending in `in` is not a wrapper.
_WRAPPER_KEYWORDS: Final[frozenset[str]] = frozenset({
    "set_option", "open", "variable", "variables", "include", "omit", "attribute", "universe",
    "suppress_compilation",
})


def _command_keyword(stripped: str) -> str:
    for tok in stripped.split():
        if tok not in _COMMAND_MODIFIERS:
            return tok
    return ""


def _cut_dangling_wrapper(prefix: str, prefix_source: str) -> str:
    """Drop a trailing `set_option ... in` / `open ... in` that wraps the target itself.

    The extraction records `char_start` at the WRAPPED declaration, so a raw slice ends on the
    wrapper's `in` and Lean reports `unexpected end of input`. The wrapper is re-emitted in front of
    the statement by `render_declaration`, which is where it belongs: `set_option maxHeartbeats
    400000 in` scopes to one declaration.
    """
    ps = prefix_source.strip()
    stripped = prefix.rstrip()
    if ps and stripped.endswith(ps):
        return stripped[:len(stripped) - len(ps)]
    while True:
        stripped = stripped.rstrip()
        if not (stripped.endswith(" in") or stripped.endswith("\nin")):
            return stripped + "\n" if stripped else stripped
        lines = stripped.splitlines()
        for i in range(len(lines) - 1, -1, -1):
            if _command_keyword(lines[i].strip()) in _WRAPPER_KEYWORDS:
                stripped = "\n".join(lines[:i])
                break
        else:
            return stripped + "\n"


def declaration_context(source: str, char_start: int, prefix_source: str = "") -> str:
    """`source[:char_start]`, less a dangling wrapper, plus mathlib's options after the last import.

    The WHOLE prefix, not just its scope commands: `variable {B : Type u} [Bicategory B]` names
    things declared earlier in the same file, so a context without those declarations cannot
    elaborate its own `variable` lines (upstream oracle 0.005/200 when this was tried).

    `char_start` is a CHARACTER offset into the decoded text, not a byte offset.
    """
    prefix = _cut_dangling_wrapper(source[:char_start], prefix_source)
    lines = prefix.splitlines(keepends=True)
    last_import = 0
    for i, line in enumerate(lines):
        if _command_keyword(line.strip()) == "import":
            last_import = i + 1
    lines[last_import:last_import] = [MATHLIB_LEAN_OPTIONS]
    return "".join(lines)


def strip_attributes(stmt: str) -> str:
    """Drop leading `@[...]` attribute blocks and doc comments from a declaration's signature.

    `@[to_additive]` derives a name from the declaration's, which the rename breaks (41 of 200
    upstream oracle statements), and `@[simp]` would leak the target into the simp set of every
    later check in the session. Bracket-matched, because an attribute can contain a doc comment
    whose prose has a `]` in it.
    """
    s = stmt
    while True:
        i = 0
        while i < len(s) and s[i].isspace():
            i += 1
        if s.startswith("/--", i):
            j = s.find("-/", i + 3)
            if j < 0:
                return s
            s = s[j + 2:]
            continue
        if not s.startswith("@[", i):
            return s.lstrip()
        depth, k, n = 0, i + 1, len(s)
        while k < n:
            c = s[k]
            if c == '"':
                k += 1
                while k < n and s[k] != '"':
                    k += 2 if s[k] == "\\" else 1
            elif s.startswith("/-", k):
                end = s.find("-/", k + 2)
                k = (end + 1) if end >= 0 else n
            elif c == "[":
                depth += 1
            elif c == "]":
                depth -= 1
                if depth == 0:
                    s = s[k + 1:]
                    break
            k += 1
        else:
            return s.lstrip()


#: The last name component every graded declaration is given.
TARGET_STEM: Final[str] = "sb_target"


def render_declaration(stmt_source: str, prefix_source: str, proof: str) -> tuple[str, str, int]:
    """`(source, declared_name, proof_offset)` for one graded attempt.

    The declaration's LAST name component becomes `sb_target`; any namespace written into the name
    is KEPT, because Lean opens the namespace a dotted declaration name introduces for that
    declaration's body -- renaming `Height.iSup_fun_eq_max` to a bare name moved its proof out of
    `Height` and broke 5 of 200 upstream gold proofs with `Unknown identifier`.

    The proof goes on the SAME LINE as `:=`. Lean is indentation-sensitive, and LeanBench measured a
    term-mode `let` that stops parsing when moved to the next line at column 0.

    `proof_offset` is the character offset at which `proof` begins in `source`: everything before it
    is harness text, and only what follows is charged to the submission.
    """
    prefix = (prefix_source.strip() + "\n") if prefix_source.strip() else ""
    stmt = strip_attributes(stmt_source).strip()
    name = TARGET_STEM
    for kw in ("theorem", "lemma"):
        token = kw + " "
        i = stmt.find(token)
        if i >= 0:
            j = i + len(token)
            k = j
            while k < len(stmt) and not stmt[k].isspace() and stmt[k] not in "(:{[":
                k += 1
            written = stmt[j:k]
            # `theorem foo.{u, v} ...`: universe parameters follow the name as `.{...}` and stay.
            univ = ""
            if written.endswith(".") and stmt[k:k + 1] == "{":
                close = stmt.find("}", k)
                if close < 0:
                    raise ValueError(f"unterminated universe list: {stmt[:120]!r}")
                written, univ = written[:-1], stmt[k - 1:close + 1]
                k = close + 1
            head, _, last = written.rpartition(".")
            name = f"{head}.{TARGET_STEM}" if last and head else TARGET_STEM
            stmt = stmt[:i] + "theorem " + name + univ + stmt[k:]
            break
    else:
        raise ValueError(f"not a theorem/lemma statement: {stmt[:120]!r}")
    head = f"{prefix}{stmt} := "
    return head + proof, name, len(head)
