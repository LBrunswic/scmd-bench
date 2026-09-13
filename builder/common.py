"""Load corpus_v2 and its upstream text artifacts through LeanDLLM's own readers.

BUILDER-ONLY. Everything under `builder/` imports `scmd` (LeanDLLM) on purpose: the benchmark's
data must be the corpus SCMD trained on, and a second reader of the shard is a second thing that
can disagree with it. Nothing in `scmd_bench/` imports this, and the released files carry no
dependency on it. Run with LeanDLLM on `PYTHONPATH`:

    PYTHONNOUSERSITE=1 PYTHONPATH=$LEANDLLM $SCMD_PY -m builder.export ...

The pinned upstream commit is recorded in every manifest this package writes.
"""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

SHARD = "corpus_v2"
EXPECT_CORPUS_ID = "9831f3a0501bc66a7d2887f8bb2fd9f2de46ed1c8395bd29d9aa3d64be3bae4a"
EXPECT_BANK_SHA = "46bef4750502a0693b6272c273917ef29a86b567a3f9157e29e89bc8ce695eba"
HARD_KEY = {"k": 64, "n_docs": 100853, "k1": 20.0, "b": 1.0, "basis": "target_text_v2"}
MATHLIB_PREFIX = "/data/scmd/lean/library-v4.31.0/.lake/packages/mathlib/"


def log(msg: str) -> None:
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", file=sys.stderr, flush=True)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def upstream_commit() -> str:
    import scmd
    root = Path(scmd.__file__).resolve().parents[1]
    try:
        out = subprocess.run(["git", "-C", str(root), "rev-parse", "HEAD"], capture_output=True,
                             text=True, check=True).stdout.strip()
        dirty = subprocess.run(["git", "-C", str(root), "status", "--porcelain", "scmd"],
                               capture_output=True, text=True).stdout.strip()
        return out + ("-dirty" if dirty else "")
    except Exception:  # noqa: BLE001
        return "unknown"


@dataclass
class DeclRec:
    full_name: str
    module: str
    file: str               # relative to the mathlib root, e.g. Mathlib/Algebra/Group/Defs.lean
    char_start: int
    source_name: str
    stmt_source: str
    prefix_source: str
    proof_source: str
    pp_type: str
    is_thm: bool
    is_private: bool


@dataclass
class Corpus:
    cfg: Any
    reader: Any
    tok: Any
    assignment: dict[str, dict[str, str]]
    deps: dict[str, tuple[str, ...]]
    recs: dict[str, DeclRec]
    rests: dict[str, str]                 # drawable premise -> SOURCE rest (after the name)
    bank_rests: dict[str, str]            # premise with no record -> HYP rest from S7b's bank
    module_of: dict[str, str]
    hard: dict[str, list[str]]
    meta: dict[str, Any] = field(default_factory=dict)

    @property
    def vocab(self) -> int:
        return self.reader.manifest.geometry.vocab_size

    def rest_of(self, premise: str) -> str | None:
        if premise in self.rests:
            return self.rests[premise]
        return self.bank_rests.get(premise)

    def splits_of(self, row: int) -> dict[str, str]:
        return dict(self.assignment.get(self.reader.decls[row], {}))

    def trainable(self, row: int) -> bool:
        a = self.assignment.get(self.reader.decls[row])
        return bool(a) and all(v == "train" for v in a.values())


def load_corpus(*, host: str = "node1", with_hard: bool = True) -> Corpus:
    import argparse

    from scmd.data.cli import _corpus_inputs, hypo_bank_path, premise_universe  # noqa: PLC2701
    from scmd.data.premise import HYP, SOURCE, premise_rest
    from scmd.data.shard import ShardReader
    from scmd.data.splits import load_assignment
    from scmd.tok.corpus import load_deps
    from scmd.tok.hf import LeanTokenizer

    cfg, records, deps_path = _corpus_inputs(
        argparse.Namespace(host=host, records="", deps="", shard=SHARD))
    shard_dir = Path(cfg.shard_root) / SHARD
    reader = ShardReader(shard_dir)
    man = reader.manifest
    if man.corpus_id != EXPECT_CORPUS_ID:
        raise SystemExit(f"corpus_id {man.corpus_id} != pinned {EXPECT_CORPUS_ID}")
    bank = hypo_bank_path(cfg)
    if sha256_file(bank) != EXPECT_BANK_SHA:
        raise SystemExit(f"{bank} does not match the shard manifest's hyp_bank_sha")
    log(f"shard {SHARD}: {len(reader)} rows, corpus_id {man.corpus_id[:16]}")
    tok = LeanTokenizer.from_artifact("ms16k")
    assignment = load_assignment(shard_dir)
    deps = load_deps(deps_path)
    log("premise universe (walks records.jsonl) ...")
    types, _cited = premise_universe(records, deps_path)
    rests = {n: premise_rest(n, pp, style=SOURCE, stmt_source=src) for n, (pp, src) in types.items()}

    log("declaration records ...")
    wanted = set(reader.decls) | set(rests)
    recs: dict[str, DeclRec] = {}
    with records.open(encoding="utf-8") as fh:
        for line in fh:
            rec = json.loads(line)
            if not rec.get("ok"):
                continue
            for d in rec.get("decls") or ():
                n = d.get("full_name")
                if n not in wanted or n in recs or d.get("char_start") is None:
                    continue
                f = str(d.get("file") or "")
                if f.startswith(MATHLIB_PREFIX):
                    f = f[len(MATHLIB_PREFIX):]
                recs[n] = DeclRec(
                    full_name=n, module=d.get("module") or rec.get("module") or "", file=f,
                    char_start=int(d["char_start"]), source_name=d.get("source_name") or "",
                    stmt_source=d.get("stmt_source") or "", prefix_source=d.get("prefix_source") or "",
                    proof_source=d.get("proof_source") or "", pp_type=d.get("pp_type") or "",
                    is_thm=bool(d.get("is_thm")), is_private=bool(d.get("is_private")))
    log(f"{len(recs)} records kept")

    gold_names = {d for row in reader.decls for d in deps.get(row, ())}
    need_bank = gold_names - set(rests)
    bank_rests: dict[str, str] = {}
    with bank.open(encoding="utf-8") as fh:
        for line in fh:
            for r in json.loads(line).get("rows") or ():
                n = r.get("name")
                if n in need_bank and n not in bank_rests and r.get("hyp_type"):
                    try:
                        bank_rests[n] = premise_rest(n, r["hyp_type"], style=HYP)
                    except ValueError:
                        pass
    log(f"{len(rests)} drawable premises, {len(bank_rests)} gold-only premises from the bank")

    module_of: dict[str, str] = {}
    for n in wanted:
        r = recs.get(n)
        module_of[n] = r.module if r else (n.rpartition(".")[0] or "?")

    hard: dict[str, list[str]] = {}
    if with_hard:
        path = Path(cfg.data_root) / "data" / "assemble_v1" / "hard_negatives.json"
        log(f"hard negatives {path} ...")
        doc = json.loads(path.read_text(encoding="utf-8"))
        if doc.get("key") != HARD_KEY:
            raise SystemExit(f"hard-negative cache key {doc.get('key')} != {HARD_KEY}")
        hard = doc["lists"]
    meta = {"shard": SHARD, "corpus_id": man.corpus_id, "tokenizer_id": man.tokenizer_id,
            "records_sha256": None, "deps_sha256": None, "hyp_bank_sha256": EXPECT_BANK_SHA,
            "hard_negatives_key": HARD_KEY, "upstream_commit": upstream_commit(),
            "records": str(records), "deps": str(deps_path)}
    return Corpus(cfg=cfg, reader=reader, tok=tok, assignment=assignment, deps=deps, recs=recs,
                  rests=rests, bank_rests=bank_rests, module_of=module_of, hard=hard, meta=meta)


def target_rest(rec: DeclRec) -> str:
    """The target's signature as SCMD sees it (`render_premise(SOURCE)`), minus the name."""
    from scmd.data.build import target_text
    whole = target_text({"full_name": rec.full_name, "pp_type": rec.pp_type,
                         "stmt_source": rec.stmt_source})
    if not whole.startswith(rec.full_name):
        raise ValueError(f"{rec.full_name}: target rendering does not start with its name")
    return whole[len(rec.full_name):]


def render_proof_ids(corpus: Corpus, ids: list[int], names: list[str]) -> str:
    from scmd.tok.render import render_proof
    return render_proof(ids, names, corpus.vocab, tokenizer=corpus.tok, k_max=max(64, len(names)))


# ── the import graph ────────────────────────────────────────────────────────────────────────────
_IMPORT = re.compile(r"^\s*(public\s+)?(meta\s+)?import\s+(all\s+)?([\w.'«»]+)")


def module_imports(mathlib_root: Path) -> dict[str, list[list]]:
    """`Mathlib.X.Y -> [[imported module, is_public, is_meta], ...]`, read from the source headers.

    The flags are load-bearing. mathlib v4.31.0 is on Lean's module system, where a PRIVATE
    `import M` makes M visible to the importing file only: files that import THAT file do not see M.
    A closure that follows every edge over-approximates what a target can name -- measured on the
    first 30 dev candidates, it put 4 premises into BASE that do not resolve in the grading
    environment (`Finset.prod_sub_ordered` from `Mathlib.Data.DFinsupp.BigOperators`, among them);
    following `public import` edges past the first hop excludes all four.

    Only `Mathlib.*` edges are kept: the premise universe is `Mathlib.*`, so the rest of the closure
    never contains a premise.
    """
    out: dict[str, list[list]] = {}
    for p in sorted((mathlib_root / "Mathlib").rglob("*.lean")):
        mod = ".".join(p.relative_to(mathlib_root).with_suffix("").parts)
        imps: list[list] = []
        in_block = False
        for line in p.read_text(encoding="utf-8").splitlines():
            s = line.strip()
            if in_block:
                if "-/" in s:
                    in_block = False
                continue
            if s.startswith("/-"):
                in_block = "-/" not in s
                continue
            if not s or s.startswith("--") or s == "module" or s.startswith("prelude"):
                continue
            m = _IMPORT.match(line)
            if not m:
                break
            if m.group(4).startswith("Mathlib."):
                imps.append([m.group(4), bool(m.group(1)), bool(m.group(2))])
        out[mod] = imps
    return out


def _exported(module: str, graph: dict[str, list[list]], memo: dict[str, frozenset[str]]) -> frozenset[str]:
    """Modules visible to anything that imports `module`: its public imports, transitively."""
    if module in memo:
        return memo[module]
    if sys.getrecursionlimit() < 20000:
        sys.setrecursionlimit(20000)
    acc: set[str] = set()
    for dep, public, _meta in graph.get(module, ()):
        if public:
            acc.add(dep)
            acc |= _exported(dep, graph, memo)
    memo[module] = frozenset(acc)
    return memo[module]


def closure(module: str, graph: dict[str, list[list]], memo: dict[str, frozenset[str]]) -> frozenset[str]:
    """The Mathlib modules whose declarations `module`'s source can name, excluding itself:
    every direct import, plus what each of them EXPORTS (public imports, transitively)."""
    acc: set[str] = set()
    for dep, _public, _meta in graph.get(module, ()):
        acc.add(dep)
        acc |= _exported(dep, graph, memo)
    return frozenset(acc)

_OPENERS = "([{⟨⦃⟪«"
_CLOSERS = ")]}⟩⦄⟫»"


def has_toplevel_assign(statement: str) -> bool:
    """Is there a `:=` at bracket depth 0 (comments and strings masked)? Then the "statement"
    carries its own proof: S2's statement/proof split can land inside a `calc` or term body, leaving
    most of the proof in `stmt_source` (LeanBench measured 5.69% of a mathlib pool). Such a target
    hands a system its own answer, and is excluded. `(h : P := by simp)` is at depth 1 and passes.
    """
    from scmd_bench.submission import mask_comments_and_strings
    text = mask_comments_and_strings(statement)
    depth = 0
    for i, ch in enumerate(text):
        if ch in _OPENERS:
            depth += 1
        elif ch in _CLOSERS:
            depth -= 1
        elif ch == ":" and text[i + 1:i + 2] == "=" and depth <= 0:
            return True
    return False


def is_equation_compiler(statement: str) -> bool:
    """Does the signature end in pattern-matching alternatives (`| a, b => ...`)? Then the target has
    no `:= proof` form to grade, and is excluded. (`Mathlib.Meta.NormNum.IsRat.neg_to_eq`.)"""
    from scmd_bench.submission import mask_comments_and_strings
    return bool(re.search(r"(^|\n)\s*\|", mask_comments_and_strings(statement))) or \
        statement.rstrip().endswith("=>")


def anonymise_full_names(proof: str, names_to_slot: dict[str, str]) -> str:
    """Replace every remaining whole-token FULL name of a BASE premise by its placeholder.

    The shard's pointer labels skip some references (LeanDLLM GAP-M4-001: an occurrence the label
    builder classified `non_term`), so a pointer-rendered proof can still spell a premise's real
    name -- and the anonymised track forbids exactly that. Only names shaped like lemma names are
    replaced -- dotted, or containing `_` -- because a short undotted name (`R`, `get`) collides with
    binders and case labels, which is what sank LeanBench's short-name rewriting (gold 0.74). A
    token preceded by `.` (field notation) or followed by ` =>` (a case label) is left alone. Longest
    first, so `Foo.bar_baz` is not cut at `Foo.bar`. The gold oracle then re-verifies the result.
    """
    from scmd_bench.submission import mask_comments_and_strings
    # A proof written under `open NumberField` spells `nrRealPlaces_eq_zero_iff` for
    # `NumberField.nrRealPlaces_eq_zero_iff`. Trailing-component forms are replaced too, when they
    # are lemma-shaped and name exactly ONE BASE premise.
    forms: dict[str, list[str]] = {}
    for name in names_to_slot:
        parts = name.split(".")
        for i in range(1, len(parts)):
            forms.setdefault(".".join(parts[i:]), []).append(name)
    names_to_slot = dict(names_to_slot)
    for form, owners in forms.items():
        if len(owners) == 1 and form not in names_to_slot and "_" in form:
            names_to_slot[form] = names_to_slot[owners[0]]
    for name in sorted(names_to_slot, key=len, reverse=True):
        if "." not in name and "_" not in name:
            continue
        rx = re.compile(r"(?<![\w.'@])" + re.escape(name) + r"(?![\w'])(?!\s*=>)")
        masked = mask_comments_and_strings(proof)
        spans = [m.span() for m in rx.finditer(masked)]
        for a, b in reversed(spans):
            proof = proof[:a] + names_to_slot[name] + proof[b:]
    return proof
