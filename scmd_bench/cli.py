"""`scmd-bench` -- view prompts, grade submissions, score, compare.

    scmd-bench view    --items data/v1/dev.jsonl --track anon --k 64 > prompts.jsonl
    scmd-bench grade   --items data/v1/dev.jsonl --submission sub.jsonl --track anon --k 64 \\
                       --out graded.jsonl [--workers 8]
    scmd-bench score   --items data/v1/dev.jsonl --graded graded.jsonl --n 64 --k 64 --out score.json
    scmd-bench compare --items data/v1/dev.jsonl --a a.graded.jsonl --b b.graded.jsonl --n 64 --k 64

A submission is JSONL, one line per attempt: `{"item_id": ..., "sample_idx": 0, "proof": "..."}`.
`proof` is the text after `:=` and nothing else. Grading is resumable: an existing `--out` is read
and only attempts it lacks are graded.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from collections import defaultdict
from pathlib import Path

from scmd_bench.pool import Job, run_jobs
from scmd_bench.schema import TRACKS, Attempt, Fault, load_items, read_jsonl
from scmd_bench.score import mcnemar, score


def _log(msg: str) -> None:
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", file=sys.stderr, flush=True)


def cmd_view(a: argparse.Namespace) -> int:
    for it in load_items(a.items):
        if str(a.k) in it.prompt["base"]:
            print(json.dumps(it.view(a.track, a.k), ensure_ascii=False))
    return 0


def cmd_grade(a: argparse.Namespace) -> int:
    items = {it.item_id: it for it in load_items(a.items)}
    subs: dict[str, list[tuple[int, str]]] = defaultdict(list)
    seen = set()
    for row in read_jsonl(a.submission):
        key = (row["item_id"], int(row["sample_idx"]))
        if row["item_id"] not in items:
            raise SystemExit(f"unknown item_id {row['item_id']}")
        if key in seen:
            raise SystemExit(f"duplicate attempt {key}")
        seen.add(key)
        subs[row["item_id"]].append((int(row["sample_idx"]), str(row.get("proof") or "")))
    out = Path(a.out)
    done: dict[tuple[str, int], dict] = {}
    if out.is_file():
        for r in read_jsonl(out):
            if a.regrade_harness and r.get("fault") == Fault.HARNESS.value:
                continue
            done[(r["item_id"], r["sample_idx"])] = r
    jobs = []
    for iid, proofs in subs.items():
        it = items[iid]
        if str(a.k) not in it.prompt["base"]:
            continue
        todo = [(i, p) for i, p in proofs if (iid, i) not in done]
        if todo:
            jobs.append(Job(item=it.to_json(),
                            attempts=[("s", a.track, a.k, i, p) for i, p in sorted(todo)]))
    _log(f"{sum(len(j.attempts) for j in jobs)} attempts over {len(jobs)} items to grade "
         f"({len(done)} already graded)")
    rows = dict(done)
    t0 = time.perf_counter()
    for n, res in enumerate(run_jobs(jobs, workers=a.workers), 1):
        if res.get("error"):
            _log(f"worker error on {res['item_id']}: {res['error'][-300:]}")
        for _tag, att in res["attempts"]:
            rows[(att["item_id"], att["sample_idx"])] = att
        if n % 20 == 0 or n == len(jobs):
            _log(f"  {n}/{len(jobs)} items, {time.perf_counter() - t0:.0f}s")
            _write(out, rows)
    _write(out, rows)
    return 0


def _write(out: Path, rows: dict) -> None:
    tmp = out.with_suffix(out.suffix + ".tmp")
    out.parent.mkdir(parents=True, exist_ok=True)
    with tmp.open("w", encoding="utf-8") as fh:
        for key in sorted(rows):
            fh.write(json.dumps(rows[key], ensure_ascii=False, sort_keys=True) + "\n")
    tmp.replace(out)


def cmd_score(a: argparse.Namespace) -> int:
    items = load_items(a.items)
    atts = [Attempt.from_json(r) for r in read_jsonl(a.graded)]
    res = score(items, atts, n=a.n, k_base=a.k, allow_harness_faults=a.allow_harness_faults)
    res["items_file"] = str(a.items)
    res["split"] = items[0].split if items else None
    text = json.dumps(res, indent=2)
    if a.out:
        Path(a.out).write_text(text + "\n", encoding="utf-8")
    print(text)
    return 0


def cmd_compare(a: argparse.Namespace) -> int:
    ids = {it.item_id for it in load_items(a.items)
           if it.meta.get("premise_necessary", False) or a.all_items}

    def solved(path: str) -> dict[str, bool]:
        s: dict[str, bool] = defaultdict(bool)
        for r in read_jsonl(path):
            if r["item_id"] in ids and r["sample_idx"] < a.n:
                s[r["item_id"]] |= r["outcome"] == "solved"
        return {i: s[i] for i in ids}

    print(json.dumps(mcnemar(solved(a.a), solved(a.b)), indent=2))
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="scmd-bench", description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    def common(p: argparse.ArgumentParser) -> None:
        p.add_argument("--items", required=True)
        p.add_argument("--k", type=int, default=64, choices=(64, 16))

    p = sub.add_parser("view"); common(p)
    p.add_argument("--track", choices=TRACKS, required=True)
    p.set_defaults(fn=cmd_view)
    p = sub.add_parser("grade"); common(p)
    p.add_argument("--track", choices=TRACKS, required=True)
    p.add_argument("--submission", required=True)
    p.add_argument("--out", required=True)
    p.add_argument("--workers", type=int, default=8)
    p.add_argument("--regrade-harness", action="store_true",
                   help="re-grade attempts whose previous verdict was a harness fault")
    p.set_defaults(fn=cmd_grade)
    p = sub.add_parser("score"); common(p)
    p.add_argument("--graded", required=True)
    p.add_argument("--n", type=int, required=True, help="samples per item the system drew")
    p.add_argument("--out")
    p.add_argument("--allow-harness-faults", action="store_true")
    p.set_defaults(fn=cmd_score)
    p = sub.add_parser("compare"); common(p)
    p.add_argument("--a", required=True)
    p.add_argument("--b", required=True)
    p.add_argument("--n", type=int, default=64)
    p.add_argument("--all-items", action="store_true", help="not only premise_necessary")
    p.set_defaults(fn=cmd_compare)
    a = ap.parse_args(argv)
    return a.fn(a)


if __name__ == "__main__":
    raise SystemExit(main())
