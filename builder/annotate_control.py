"""Annotate items with the gold-removed control: does removing the gold premises from BASE make
the gold proof inadmissible?

    python -m builder.annotate_control --items data/v1/dev.jsonl --graded results/gold/dev.control_gold_removed.graded.jsonl

`meta.base_binding = True` when it does. When it does not, every gold dependency the proof names is
VOCABULARY (a definition, structure or projection), which the contract does not charge, so BASE
membership is not what the item tests. Measured on dev: 31 of 500. `score` reports the
`base_binding` subset beside the headline.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from scmd_bench.schema import item_id_of, read_jsonl


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--items", type=Path, required=True)
    ap.add_argument("--graded", type=Path, required=True)
    a = ap.parse_args(argv)
    verdict = {r["item_id"]: r["outcome"] for r in read_jsonl(a.graded)}
    rows = list(read_jsonl(a.items))
    n_bind = 0
    for d in rows:
        gold = set(d["answer"]["gold_deps"])
        ctrl_prompt = dict(d["prompt"], base={k: [s for s in v if s["name"] not in gold]
                                               for k, v in d["prompt"]["base"].items()})
        cid = item_id_of(ctrl_prompt, d["grading"])
        if cid not in verdict:
            raise SystemExit(f"{d['item_id']}: control not graded")
        d["meta"]["base_binding"] = verdict[cid] != "solved"
        n_bind += d["meta"]["base_binding"]
    with a.items.open("w", encoding="utf-8") as fh:
        for d in rows:
            fh.write(json.dumps(d, ensure_ascii=False, sort_keys=True) + "\n")
    print(f"{n_bind}/{len(rows)} items base_binding")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
