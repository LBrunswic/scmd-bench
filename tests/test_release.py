"""`release` tier: the stdlib assembler reproduces upstream `scmd.data.assemble` draw for draw."""

from __future__ import annotations

import gzip
import json
import os
from pathlib import Path

import pytest

from scmd_bench.assemble import PremisePools, assemble_base

ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.release
def test_assemble_parity_with_upstream():
    rel = Path(os.environ["SCMD_BENCH_RELEASE"])
    module_of = json.loads((rel / "target_modules.json").read_text(encoding="utf-8"))
    drawable = []
    with gzip.open(rel / "premises.jsonl.gz", "rt", encoding="utf-8") as fh:
        for line in fh:
            p = json.loads(line)
            module_of.setdefault(p["name"], p["module"])
            if p["drawable"]:
                drawable.append(p["name"])
    pools = PremisePools.build(module_of, drawable=drawable)
    fx = json.loads((ROOT / "tests/fixtures/assemble_parity.json").read_text(encoding="utf-8"))
    mism = []
    for r in fx["rows"]:
        b = assemble_base(r["decl"], r["gold"], pools=pools, hard=r["hard"], progress=r["progress"],
                          seed=0, epoch=r["epoch"], example_id=r["row"], k=r["k"])
        if (b.k, b.names, b.tiers) != (r["expect"]["k"], r["expect"]["names"], r["expect"]["tiers"]):
            mism.append(r["decl"])
    assert len(fx["rows"]) >= 1900
    assert not mism, f"{len(mism)} of {len(fx['rows'])} draws differ from upstream: {mism[:5]}"
