"""Record upstream `scmd.data.assemble`'s BASE draws, for `tests/test_assemble_parity.py`.

    PYTHONNOUSERSITE=1 PYTHONPATH=$LEANDLLM $SCMD_PY -m builder.parity --out tests/fixtures/assemble_parity.json

The fixture carries each row's inputs (target, gold deps, the target's hard list) and upstream's
output (slot names, tiers, K) for 2,000 rows drawn uniformly from the whole corpus, at mixed
curriculum points, epochs and forced/drawn K. The stdlib transcription must reproduce every one.
The universe and module map it needs ship in the training release (`premises.jsonl.gz`,
`target_modules.json`); the test reads them from `$SCMD_BENCH_RELEASE`.
"""

from __future__ import annotations

import argparse
import json
import random
from pathlib import Path

from builder.common import load_corpus, log


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="builder.parity")
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--n", type=int, default=2000)
    args = ap.parse_args(argv)

    from scmd.data.assemble import assemble
    from scmd.data.cli import _name_pool  # noqa: PLC2701
    from scmd.data.distractors import PremisePools

    c = load_corpus()
    pools = PremisePools.build(c.module_of, drawable=set(c.rests))
    names, _ = _name_pool(c.cfg, c.tok, seed=0)
    # Slot tokens are irrelevant to WHICH names are drawn; any non-None sequence satisfies assemble.
    slot_tokens = {n: (1,) for n in c.rests}
    rng = random.Random(20260913)
    rows = []
    idx = [i for i in range(len(c.reader)) if c.deps.get(c.reader.decls[i]) is not None]
    for i in rng.sample(idx, args.n):
        d = c.reader.decls[i]
        ex = c.reader.example(i)
        deps = list(c.deps[d])
        if len(deps) > 64 or len(deps) != len(ex["premises"]):
            continue
        prog = rng.choice([0.0, 0.25, 0.5, 1.0])
        epoch = rng.choice([0, 1, 37])
        k = rng.choice([None, None, 16, 64])
        k = None if (k is not None and len(deps) > k) else k
        a = assemble({**ex, "deps": deps}, pools=pools, slot_tokens=slot_tokens, vocab_size=c.vocab,
                     names=names, hard=c.hard.get(d, ()), progress=prog, seed=0, epoch=epoch,
                     example_id=i, k=k)
        rows.append({"row": i, "decl": d, "gold": deps, "hard": list(c.hard.get(d, ())),
                     "progress": prog, "epoch": epoch, "k": k,
                     "expect": {"k": a.k, "names": list(a.names), "tiers": list(a.tiers)}})
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps({"upstream_commit": c.meta["upstream_commit"],
                                    "corpus_id": c.meta["corpus_id"], "rows": rows}),
                        encoding="utf-8")
    log(f"wrote {len(rows)} parity rows -> {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
