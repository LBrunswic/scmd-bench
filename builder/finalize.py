"""Turn candidates into the released item sets: gold oracle, BASE resolution, ambient floor.

    python -m builder.finalize --cands /data/scmd-bench/v1 --n-dev 500 --n-test 2000 --out data/v1

No `scmd` import: this runs on the benchmark's own grader, which is the point -- the harness that
admits an item is the harness that will grade submissions against it.

AN ITEM IS KEPT IFF, IN CANDIDATE ORDER (fixed before any Lean ran):
  * its gold proof is SOLVED on every (track, K) the item offers -- named and anonymised, K=64 and
    (when |gold| <= 16) K=16. A gold proof the harness rejects means either the harness or the item
    is wrong, and neither may be scored;
  * every BASE name of every K exists in the grading environment.
Items are never repaired. Rejections are counted by reason and published in the dataset card,
because a filter that silently drops hard items biases the set.

THE AMBIENT FLOOR is measured on every kept item: 16 zero-parameter proofs, each tried separately
under the full contract. An item any of them solves is `ambient_solvable`; the headline is scored on
the rest (`premise_necessary`).
"""

from __future__ import annotations

import argparse
import collections
import json
import sys
import time
from pathlib import Path

from scmd_bench.pool import Job, run_jobs
from scmd_bench.schema import read_jsonl

AMBIENT_BATTERY: tuple[str, ...] = (
    "rfl", "by simp", "by aesop", "by decide", "by omega", "by norm_num", "by ring",
    "by positivity", "by linarith", "by simp_all", "by simpa", "by tauto", "by field_simp",
    "by trivial", "by assumption", "by exact?",
)


def log(msg: str) -> None:
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", file=sys.stderr, flush=True)


def jobs_for(item: dict) -> Job:
    atts = []
    ans = item["answer"]
    for k in item["prompt"]["base"]:
        atts.append((f"gold/named/{k}", "named", int(k), 0, ans["gold_proof"]))
        atts.append((f"gold/anon/{k}", "anon", int(k), 0, ans["gold_proof_anon"][k]))
        if ans.get("proof_source"):
            atts.append((f"src/named/{k}", "named", int(k), 1, ans["proof_source"]))
            atts.append((f"src/anon/{k}", "anon", int(k), 1, ans["proof_source_anon"][k]))
    for j, tac in enumerate(AMBIENT_BATTERY):
        atts.append((f"ambient/{tac}", "named", 64, j, tac))
    return Job(item=item, attempts=atts, checks=[("resolve", int(k)) for k in item["prompt"]["base"]])


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="builder.finalize")
    ap.add_argument("--cands", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--n-dev", type=int, default=500)
    ap.add_argument("--n-test", type=int, default=2000)
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--splits", default="dev,test")
    ap.add_argument("--limit", type=int, default=0, help="grade only the first N candidates per split")
    args = ap.parse_args(argv)
    args.out.mkdir(parents=True, exist_ok=True)

    for split in args.splits.split(","):
        want = args.n_dev if split == "dev" else args.n_test
        cands = list(read_jsonl(args.cands / f"candidates.{split}.jsonl"))
        if args.limit:
            cands = cands[:args.limit]
        log(f"{split}: grading {len(cands)} candidates with {args.workers} workers")
        raw_path = args.out / f"_finalize.{split}.jsonl"
        done: dict[str, dict] = {}
        if raw_path.is_file():                     # resumable: a multi-hour pass must survive a crash
            for r in read_jsonl(raw_path):
                done[r["item_id"]] = r
            log(f"  resuming: {len(done)} already graded")
        todo = [c for c in cands if c["item_id"] not in done]
        t0 = time.perf_counter()
        with raw_path.open("a", encoding="utf-8") as fh:
            for n, res in enumerate(run_jobs((jobs_for(c) for c in todo), workers=args.workers), 1):
                done[res["item_id"]] = res
                fh.write(json.dumps(res, ensure_ascii=False) + "\n")
                fh.flush()
                if n % 25 == 0 or n == len(todo):
                    el = time.perf_counter() - t0
                    log(f"  {n}/{len(todo)} in {el/60:.1f} min ({el/n:.1f} s/item)")

        reasons: collections.Counter[str] = collections.Counter()
        kept: list[dict] = []
        gold_detail: list[dict] = []
        for c in cands:
            res = done.get(c["item_id"])
            if res is None:
                reasons["not_graded"] += 1
                continue
            if res.get("error"):
                reasons["worker_error"] += 1
                continue
            atts = {tag: a for tag, a in res["attempts"]}
            ok = lambda tag: atts.get(tag, {}).get("outcome") == "solved"  # noqa: E731
            # A WITNESS, NOT A LABEL. Sufficiency needs SOME verified proof inside BASE on each
            # track; the corpus's own rendering is tried first and mathlib's original proof text
            # second. The second recovers items whose rendering hit a known corpus defect (a case
            # label expanded to a full name, a misresolved dependency) without changing BASE.
            chosen, bad = {}, []
            for k in c["prompt"]["base"]:
                for track in ("named", "anon"):
                    if ok(f"gold/{track}/{k}"):
                        chosen[(track, k)] = "gold"
                    elif ok(f"src/{track}/{k}"):
                        chosen[(track, k)] = "src"
                    else:
                        bad.append(f"gold/{track}/{k}")
            if bad:
                first = atts[bad[0]]
                why = ("void" if first["outcome"] == "void" else
                       f"gold_{bad[0].split('/')[1]}_{first['outcome']}")
                reasons[why] += 1
                gold_detail.append({"item_id": c["item_id"], "decl": c["answer"]["decl"],
                                    "failed": bad, "outcome": first["outcome"],
                                    "detail": first["detail"][:500],
                                    "source_detail": atts.get(bad[0].replace("gold/", "src/"), {}).get("detail", "")[:300]})
                continue
            unres = {k: v for k, v in res["checks"].items() if v}
            if unres:
                reasons["base_unresolvable"] += 1
                gold_detail.append({"item_id": c["item_id"], "decl": c["answer"]["decl"],
                                    "unresolvable": unres})
                continue
            if len(kept) >= want:
                reasons["surplus"] += 1
                continue
            amb = sorted(tag.split("/", 1)[1] for tag, a in atts.items()
                         if tag.startswith("ambient/") and a["outcome"] == "solved")
            c = dict(c)
            ans = dict(c["answer"])
            ans["gold_proof_anon"] = dict(ans["gold_proof_anon"])
            for (track, k), which in chosen.items():
                if which == "src":
                    if track == "named":
                        ans["gold_proof"] = ans["proof_source"]
                    else:
                        ans["gold_proof_anon"][k] = ans["proof_source_anon"][k]
            witness = {f"{t}/{k}": w for (t, k), w in chosen.items()}
            reasons["witness_from_proof_source"] += any(w == "src" for w in witness.values())
            c["answer"] = ans
            c["meta"] = dict(c["meta"], ambient_solved_by=amb, ambient_solvable=bool(amb),
                             premise_necessary=not amb, gold_witness=witness)
            kept.append(c)
        out = args.out / f"{split}.jsonl"
        with out.open("w", encoding="utf-8") as fh:
            for c in kept:
                fh.write(json.dumps(c, ensure_ascii=False, sort_keys=True) + "\n")
        summary = {"split": split, "n_candidates": len(cands), "n_kept": len(kept), "want": want,
                   "reasons": dict(reasons),
                   "ambient_solvable": sum(c["meta"]["ambient_solvable"] for c in kept),
                   "gold_failures": gold_detail}
        (args.out / f"_finalize.{split}.summary.json").write_text(
            json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
        log(f"{split}: kept {len(kept)}/{want}; {dict(reasons)}; "
            f"ambient_solvable {summary['ambient_solvable']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
