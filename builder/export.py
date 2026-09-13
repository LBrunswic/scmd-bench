"""Export the tokenizer-neutral TRAINING release: rows, premises, hard negatives, import graph.

    PYTHONNOUSERSITE=1 PYTHONPATH=$LEANDLLM $SCMD_PY -m builder.export --out /data/scmd-bench/v1

WHAT IS EXPORTED, AND WHAT IS NOT
---------------------------------
Only rows TRAIN-SIDE IN ALL THREE SPLITS (file, temporal, novel_premises) -- 168,807 of 192,836.
The hold-out rows are not in `train.jsonl.gz` at all, so a pipeline that trains on "everything in
the file" cannot train on the evaluation targets. Their premises, hard negatives and module edges
ARE exported, because an eval BASE is drawn from them and a competitor must be able to reproduce
that draw.

Per row, two proofs:
  * `proof` -- the corpus's own proof text (the shard's tokens decoded, dependencies spelled by
    full name). This is what SCMD trains on and what the gold oracle verifies.
  * `proof_pointers` -- the same proof with each dependency reference written `⟪dJ⟫`, J indexing
    `gold_deps`. A pointer or anonymised-track system can train on this and substitute slot
    placeholders at assembly (`scmd_bench.assemble` returns the slot of every gold dependency).
and two label sets, because they are not the same set: `gold_deps` (the corpus's source-level
dependencies, which define BASE's sufficiency) and `proof_source` (mathlib's own text, from which
other label definitions can be re-derived).
"""

from __future__ import annotations

import argparse
import gzip
import json
from pathlib import Path

from builder.common import (MATHLIB_PREFIX, load_corpus, log, module_imports, render_proof_ids,
                            sha256_file, target_rest)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="builder.export")
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--limit", type=int, default=0, help="first N train rows only (smoke)")
    args = ap.parse_args(argv)
    args.out.mkdir(parents=True, exist_ok=True)
    c = load_corpus()
    V = c.vocab
    decls = c.reader.decls

    n_rows = n_skipped = n_no_record = 0
    skipped: dict[str, int] = {}
    path = args.out / "train.jsonl.gz"
    log(f"writing {path} ...")
    with gzip.open(path, "wt", encoding="utf-8", compresslevel=6) as fh:
        for i, decl in enumerate(decls):
            if not c.trainable(i):
                continue
            rec = c.recs.get(decl)
            ex = c.reader.example(i)
            deps = list(c.deps.get(decl, ()))
            ids = [int(t) for t in ex["proof"]]
            if any(t >= V + len(deps) for t in ids):
                skipped["pointer_out_of_range"] = skipped.get("pointer_out_of_range", 0) + 1
                n_skipped += 1
                continue
            if rec is None:
                # No S2 record carries this row's file offset (its file's extraction failed, or the
                # declaration was joined from elsewhere). The row is still a training example --
                # the shard's own target is decoded -- but it has no grading environment, so the
                # location fields are null and it can never be an evaluation item.
                n_no_record += 1
            row = {
                "row": i, "decl": decl, "module": c.module_of.get(decl),
                "file": rec.file if rec else None,
                "char_start": rec.char_start if rec else None,
                "source_name": rec.source_name if rec else None,
                "statement": (rec.full_name + target_rest(rec)) if rec else c.tok.decode(list(ex["target"])),
                "stmt_source": rec.stmt_source if rec else None,
                "prefix_source": rec.prefix_source if rec else None,
                "gold_deps": deps,
                "gold_dep_rests": [c.rest_of(d) for d in deps],
                "proof": render_proof_ids(c, ids, deps),
                "proof_pointers": render_proof_ids(c, ids, [f"⟪d{j}⟫" for j in range(len(deps))]),
                "proof_source": rec.proof_source if rec else None,
                "splits": c.splits_of(i),
            }
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")
            n_rows += 1
            if n_rows % 20000 == 0:
                log(f"  {n_rows} rows")
            if args.limit and n_rows >= args.limit:
                break
    log(f"{n_rows} train rows, skipped {skipped}")

    held = sorted({d for i, d in enumerate(decls) if not c.trainable(i)})
    (args.out / "heldout_decls.txt").write_text("\n".join(held) + "\n", encoding="utf-8")
    log(f"{len(held)} held-out declaration names")

    log("premises ...")
    prem_path = args.out / "premises.jsonl.gz"
    n_prem = 0
    with gzip.open(prem_path, "wt", encoding="utf-8", compresslevel=6) as fh:
        for name in sorted(set(c.rests) | set(c.bank_rests)):
            rec = c.recs.get(name)
            fh.write(json.dumps({
                "name": name, "rest": c.rest_of(name), "module": c.module_of.get(name),
                "char_start": rec.char_start if rec else None,
                "drawable": name in c.rests,
                "render": "source" if name in c.rests else "bank",
            }, ensure_ascii=False) + "\n")
            n_prem += 1

    log("hard negatives ...")
    hard_path = args.out / "hard_negatives.jsonl.gz"
    with gzip.open(hard_path, "wt", encoding="utf-8", compresslevel=6) as fh:
        for decl in sorted(c.hard):
            fh.write(json.dumps({"decl": decl, "hard": c.hard[decl]}, ensure_ascii=False) + "\n")

    log("module import graph ...")
    graph = module_imports(Path(MATHLIB_PREFIX))
    (args.out / "modules.json").write_text(json.dumps(graph, sort_keys=True), encoding="utf-8")

    # Module of every TARGET too (the sibling tier looks the target up), for rows and hold-out alike.
    tmods = {d: c.module_of.get(d, "") for d in decls}
    (args.out / "target_modules.json").write_text(json.dumps(tmods, sort_keys=True),
                                                  encoding="utf-8")
    files = ["train.jsonl.gz", "heldout_decls.txt", "premises.jsonl.gz", "hard_negatives.jsonl.gz", "modules.json",
             "target_modules.json"]
    manifest = {
        "benchmark": "scmd-bench", "release": "v1.0", "part": "train",
        "source": c.meta, "n_train_rows": n_rows, "n_skipped": skipped, "n_rows_without_location": n_no_record,
        "n_premises": n_prem, "n_drawable": len(c.rests), "n_hard_lists": len(c.hard),
        "n_modules": len(graph), "row_rule": "train side of file AND temporal AND novel_premises",
        "sha256": {f: sha256_file(args.out / f) for f in files},
    }
    (args.out / "MANIFEST.train.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    log(f"done: {json.dumps({k: v for k, v in manifest.items() if k != 'sha256'})}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
