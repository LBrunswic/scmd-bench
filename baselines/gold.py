"""Gold submissions (harness validation) and the gold-removed control.

    python -m baselines.gold --items data/v1/dev.jsonl --out baselines/gold

Writes `<split>.named.jsonl` and `<split>.anon.jsonl` (gold proof, one sample) and
`<split>.control_gold_removed.items.jsonl`: the same items with every gold premise deleted from
BASE. Grading the named gold proof against those items must NOT solve: that is the admissibility
check shown to bite on real proofs, not only on planted ones.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from scmd_bench.schema import item_id_of, load_items, write_jsonl


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--items", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--k", default="64")
    a = ap.parse_args(argv)
    split = a.items.stem
    items = load_items(a.items)
    write_jsonl(a.out / f"{split}.named.jsonl",
                [{"item_id": it.item_id, "sample_idx": 0, "proof": it.answer["gold_proof"]}
                 for it in items if a.k in it.prompt["base"]])
    write_jsonl(a.out / f"{split}.anon.jsonl",
                [{"item_id": it.item_id, "sample_idx": 0, "proof": it.answer["gold_proof_anon"][a.k]}
                 for it in items if a.k in it.prompt["base"]])
    ctrl, sub = [], []
    for it in items:
        gold = set(it.answer["gold_deps"])
        d = it.to_json()
        d["prompt"] = json.loads(json.dumps(it.prompt))
        d["prompt"]["base"] = {k: [s for s in v if s["name"] not in gold] for k, v in it.prompt["base"].items()}
        d["item_id"] = item_id_of(d["prompt"], it.grading)
        ctrl.append(d)
        sub.append({"item_id": d["item_id"], "sample_idx": 0, "proof": it.answer["gold_proof"]})
    write_jsonl(a.out / f"{split}.control_gold_removed.items.jsonl", ctrl)
    write_jsonl(a.out / f"{split}.control_gold_removed.named.jsonl", sub)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
