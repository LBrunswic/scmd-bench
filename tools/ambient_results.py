"""Export the ambient battery's verdicts (graded during `builder.finalize`) as a results row.

The 16 zero-parameter proofs are one "system" whose 16 samples are 16 DIFFERENT tactics, so its
pass@k is not an i.i.d. estimate; `solved` (any of the 16) is the figure to read.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scmd_bench.schema import Attempt, load_items, read_jsonl, write_jsonl  # noqa: E402
from scmd_bench.score import score  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]


def main(split: str) -> int:
    items = load_items(ROOT / f"data/v1/{split}.jsonl")
    keep = {it.item_id for it in items}
    rows = []
    for r in read_jsonl(ROOT / f"data/v1/_finalize.{split}.jsonl"):
        if r["item_id"] not in keep:
            continue
        for tag, a in r["attempts"]:
            if tag.startswith("ambient/"):
                rows.append(a)
    out = ROOT / "results/ambient"
    write_jsonl(out / f"{split}.named.graded.jsonl", rows)
    res = score(items, [Attempt.from_json(a) for a in rows], n=16, k_base=64, ks=(1, 8),
                allow_harness_faults=True)
    res["split"] = split
    (out / f"{split}.named.score.json").write_text(json.dumps(res, indent=2), encoding="utf-8")
    (out / f"{split}.named.system.json").write_text(json.dumps({
        "name": "ambient battery (16 zero-parameter proofs)", "track": "named", "k": 64,
        "n_samples": 16, "budget": "16 fixed tactics, not i.i.d.", "exposure": "n/a",
        "parameters": 0}, indent=2), encoding="utf-8")
    print(json.dumps({k: v for k, v in res["subsets"]["all"].items()}, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1]))
