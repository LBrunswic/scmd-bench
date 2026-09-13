"""Draw the EVALUATION candidates (dev + test) from corpus_v2's hold-out.

    PYTHONNOUSERSITE=1 PYTHONPATH=$LEANDLLM $SCMD_PY -m builder.items --out /data/scmd-bench/v1

Writes `candidates.{dev,test}.jsonl` in a fixed shuffled order. `builder.finalize` then keeps, in
that order, the first N whose gold proof verifies on every track and whose BASE resolves in the
grading environment. Candidates, not items, because only Lean can say which targets are gradeable,
and deciding the order BEFORE Lean speaks is what keeps the filter from choosing easy items.

THE RULES, EACH A DEFENCE
-------------------------
* Hold-out only: test-side in at least one of file / temporal / novel_premises. None of these rows
  is in the training release.
* A theorem with 1..64 gold dependencies. Zero-dependency targets are the ambient theory's, not the
  task's (their BASE is all distractors), and are excluded rather than diluting the headline.
* Not a near-duplicate of any training row: Jaccard >= 0.9 on the target rendering, LeanDLLM's own
  rule (`scmd.data.splits.near_duplicate_pairs`), against the three-way training set.
* The recorded signature must not carry its own proof (a `:=` at bracket depth 0).
* One row per declaration name (`decls.txt` has 9 duplicates; they are dropped, not guessed).
* dev and test are split BY FILE, so no file contributes to both.
* BASE is drawn IN-CLOSURE (`scmd_bench.assemble`, `allowed=`): only premises in the target
  module's import closure, or declared above the target in its own module. Its `retrieval_hard`
  tier is the target's BM25 top-64 AMONG those premises (k1=20, b=1, the corpus's parameters),
  taken from a top-1024 list -- the in-closure analogue of the corpus's top-64.
* Endpoint curriculum (progress 1.0: 0.10 random / 0.25 sibling / 0.65 retrieval_hard), seed 0,
  epoch 0, example_id = row. K = 64 and K = 16; a target with more than 16 gold dependencies has no
  K = 16 variant (sufficiency is never truncated).
"""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import random
from pathlib import Path

from builder.common import (MATHLIB_PREFIX, anonymise_full_names, closure, has_toplevel_assign,
                            is_equation_compiler, load_corpus, log, module_imports,
                            render_proof_ids, sha256_file, target_rest)
from scmd_bench.assemble import PremisePools, assemble_base
from scmd_bench.schema import ITEM_SCHEMA, item_id_of, placeholder

SEED = 0
EPOCH = 0
PROGRESS = 1.0
HARD_DEPTH = 1024


def _file_side(file: str, dev_frac: float) -> str:
    h = int(hashlib.sha256(f"scmd-bench/v1/devtest/{file}".encode()).hexdigest()[:8], 16)
    return "dev" if h / 0xFFFFFFFF < dev_frac else "test"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="builder.items")
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--n-dev", type=int, default=900, help="candidates, not final items")
    ap.add_argument("--n-test", type=int, default=3400)
    ap.add_argument("--dev-frac", type=float, default=0.2)
    args = ap.parse_args(argv)
    args.out.mkdir(parents=True, exist_ok=True)
    c = load_corpus()
    decls = c.reader.decls
    V = c.vocab

    counts: dict[str, int] = {}

    def drop(why: str) -> None:
        counts[why] = counts.get(why, 0) + 1

    from collections import Counter
    dup = {d for d, n in Counter(decls).items() if n > 1}
    cands: list[int] = []
    for i, d in enumerate(decls):
        if c.trainable(i):
            continue
        counts["holdout_rows"] = counts.get("holdout_rows", 0) + 1
        rec = c.recs.get(d)
        deps = c.deps.get(d, ())
        if d in dup:
            drop("duplicate_name"); continue
        if rec is None or not rec.is_thm:
            drop("no_theorem_record"); continue
        if not ("theorem " in rec.stmt_source or "lemma " in rec.stmt_source):
            drop("not_theorem_syntax"); continue
        if has_toplevel_assign(rec.stmt_source):
            drop("statement_carries_proof"); continue
        if is_equation_compiler(rec.stmt_source):
            drop("equation_compiler_statement"); continue
        if not deps:
            drop("zero_deps"); continue
        if len(deps) > 64:
            drop("over_k64"); continue
        if any(c.rest_of(p) is None for p in deps):
            drop("gold_premise_unrenderable"); continue
        cands.append(i)
    log(f"{len(cands)} eligible hold-out rows; {counts}")

    log("near-duplicate screen against the three-way training set ...")
    from scmd.data.splits import Split, near_duplicate_pairs
    statements = {}
    train_names = set()
    cand_set = set(cands)
    for i, d in enumerate(decls):
        rec = c.recs.get(d)
        if rec is None:
            continue
        if c.trainable(i):
            train_names.add(d)
        statements[d] = rec.full_name + target_rest(rec) if (c.trainable(i) or i in cand_set) else None
    statements = {k: v for k, v in statements.items() if v}
    nd = near_duplicate_pairs(Split(name="file", train=frozenset(train_names),
                                    test=frozenset(decls[i] for i in cands)),
                              statements, threshold=0.9, max_offenders=100000)
    near = {o["test"] for o in nd.offenders}
    cands = [i for i in cands if decls[i] not in near]
    counts["near_duplicate"] = len(near)
    log(f"{len(near)} near-duplicates removed; {len(cands)} remain")

    rng = random.Random(f"scmd-bench/v1/candidates/{SEED}")
    rng.shuffle(cands)
    sides = {"dev": [], "test": []}
    for i in cands:
        side = _file_side(c.recs[decls[i]].file, args.dev_frac)
        want = args.n_dev if side == "dev" else args.n_test
        if len(sides[side]) < want:
            sides[side].append(i)
        if len(sides["dev"]) >= args.n_dev and len(sides["test"]) >= args.n_test:
            break
    chosen = sides["dev"] + sides["test"]
    log(f"candidates: dev {len(sides['dev'])}, test {len(sides['test'])}")

    graph = module_imports(Path(MATHLIB_PREFIX))
    memo: dict[str, frozenset[str]] = {}
    pools = PremisePools.build(c.module_of, drawable=set(c.rests))
    by_module: dict[str, list[str]] = {}
    for p in c.rests:
        by_module.setdefault(c.module_of[p], []).append(p)

    log("BM25 index for in-closure hard negatives ...")
    from scmd.data.bm25 import Bm25Params, build_index, statement_terms
    premise_text = {n: n + r for n, r in c.rests.items()}
    ix = build_index(premise_text, params=Bm25Params(k1=20.0, b=1.0))

    hard_out = gzip.open(args.out / "eval_hard_negatives.jsonl.gz", "wt", encoding="utf-8")
    for side, rows in sides.items():
        path = args.out / f"candidates.{side}.jsonl"
        n = 0
        with path.open("w", encoding="utf-8") as fh:
            for i in rows:
                d = decls[i]
                rec = c.recs[d]
                deps = list(c.deps[d])
                clo = closure(rec.module, graph, memo)
                allowed = {p for m in clo for p in by_module.get(m, ())}
                allowed |= {p for p in by_module.get(rec.module, ())
                            if (r := c.recs.get(p)) is not None and r.char_start < rec.char_start}
                allowed -= {d}
                missing_gold = [p for p in deps if p not in allowed and p in c.rests]
                q = statement_terms(rec.full_name + target_rest(rec))
                deep = [nm for nm, _s in ix.top(q, HARD_DEPTH, exclude=[d, *deps])]
                hard = [nm for nm in deep if nm in allowed][:64]
                hard_out.write(json.dumps({"decl": d, "row": i, "hard": hard}) + "\n")
                ex = c.reader.example(i)
                ids = [int(t) for t in ex["proof"]]
                bases, anon, src_anon, meta_k = {}, {}, {}, {}
                for K in (64, 16):
                    if len(deps) > K:
                        continue
                    b = assemble_base(d, deps, pools=pools, hard=hard, progress=PROGRESS,
                                      seed=SEED, epoch=EPOCH, example_id=i, k=K, allowed=allowed | set(deps))
                    bases[str(K)] = [{"name": nm, "rest": c.rest_of(nm)} for nm in b.names]
                    slot = {nm: s for s, nm in enumerate(b.names)}
                    src_anon[str(K)] = anonymise_full_names(rec.proof_source,
                                                            {nm: placeholder(s) for nm, s in slot.items()})
                    anon[str(K)] = anonymise_full_names(
                        render_proof_ids(c, ids, [placeholder(slot[p]) for p in deps]),
                        {nm: placeholder(s) for nm, s in slot.items()})
                    meta_k[str(K)] = {"k": b.k, "tiers": {t: b.tiers.count(t) for t in sorted(set(b.tiers))}}
                prompt = {"target": target_rest(rec), "base": bases}
                grading = {"file": rec.file, "char_start": rec.char_start, "module": rec.module,
                           "stmt_source": rec.stmt_source, "prefix_source": rec.prefix_source}
                item = {
                    "schema": ITEM_SCHEMA, "item_id": item_id_of(prompt, grading), "split": side,
                    "prompt": prompt, "grading": grading,
                    "answer": {"decl": d, "gold_deps": deps,
                               "gold_proof": render_proof_ids(c, ids, deps),
                               "gold_proof_anon": anon, "proof_source": rec.proof_source,
                               "proof_source_anon": src_anon},
                    "meta": {"row": i, "splits": c.splits_of(i),
                             "heldout_in": sorted(s for s, v in c.splits_of(i).items() if v == "test"),
                             "n_gold": len(deps), "bases": meta_k,
                             "gold_outside_closure": missing_gold,
                             "n_allowed": len(allowed), "n_hard_in_closure": len(hard)},
                }
                fh.write(json.dumps(item, ensure_ascii=False) + "\n")
                n += 1
                if n % 500 == 0:
                    log(f"  {side}: {n}")
        log(f"wrote {n} {side} candidates -> {path}")
    hard_out.close()
    man = {"benchmark": "scmd-bench", "release": "v1.0", "part": "candidates",
           "source": c.meta, "filter_counts": counts,
           "rules": {"seed": SEED, "epoch": EPOCH, "progress": PROGRESS, "hard_depth": HARD_DEPTH,
                     "dev_frac_by_file": args.dev_frac, "near_dup_threshold": 0.9},
           "sha256": {f: sha256_file(args.out / f) for f in
                      ("candidates.dev.jsonl", "candidates.test.jsonl", "eval_hard_negatives.jsonl.gz")}}
    (args.out / "MANIFEST.candidates.json").write_text(json.dumps(man, indent=2), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
