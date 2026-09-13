"""From graded attempts to the numbers a leaderboard row carries.

RULES.md section 6 is implemented here, and nowhere else:
  * pass@k with Codex's unbiased estimator, per item, averaged over items; `n > k` required;
  * the HEADLINE subset is `premise_necessary` (no zero-parameter tactic solves the item), and the
    full set is always reported beside it;
  * 95% bootstrap intervals over ITEMS (the sampling unit a re-draw of the benchmark would move);
  * a missing sample is a failed sample, never a skipped one -- dropping hard items from the
    denominator is the easiest way to inflate a pass rate;
  * VOID items (the grader could not build their environment) and harness faults are excluded and
    COUNTED; `score` refuses to produce a final row while harness faults are owed a re-run.
"""

from __future__ import annotations

import math
import random
from collections import defaultdict
from dataclasses import dataclass
from typing import Any, Iterable, Sequence

from scmd_bench.passk import pass_at_k
from scmd_bench.schema import Attempt, Fault, Item, Outcome

HEADLINE_KS: tuple[int, ...] = (1, 8, 32)
BOOTSTRAP_B = 2000


@dataclass
class ItemTally:
    n: int
    c: int
    void: bool = False
    harness_faults: int = 0


def tally(items: Sequence[Item], attempts: Iterable[Attempt], *, n: int) -> dict[str, ItemTally]:
    by_item: dict[str, dict[int, Attempt]] = defaultdict(dict)
    for a in attempts:
        if a.sample_idx < 0 or a.sample_idx >= n:
            raise ValueError(f"{a.item_id}: sample_idx {a.sample_idx} outside [0, {n})")
        if a.sample_idx in by_item[a.item_id]:
            raise ValueError(f"{a.item_id}: sample {a.sample_idx} graded twice")
        by_item[a.item_id][a.sample_idx] = a
    out: dict[str, ItemTally] = {}
    for it in items:
        rows = by_item.get(it.item_id, {})
        void = any(a.outcome is Outcome.VOID for a in rows.values())
        hf = sum(1 for a in rows.values() if a.fault is Fault.HARNESS)
        c = sum(1 for a in rows.values() if a.outcome.is_success)
        out[it.item_id] = ItemTally(n=n, c=c, void=void, harness_faults=hf)
    return out


def _subset_rows(items: Sequence[Item], tallies: dict[str, ItemTally],
                 pred) -> list[tuple[int, int]]:
    return [(tallies[it.item_id].n, tallies[it.item_id].c) for it in items
            if pred(it) and not tallies[it.item_id].void]


def _mean_ci(rows: list[tuple[int, int]], k: int, seed: int) -> dict[str, Any]:
    vals = [pass_at_k(n, c, k) for n, c in rows]
    if not vals:
        return {"n_items": 0}
    mean = sum(vals) / len(vals)
    rng = random.Random(seed)
    boots = []
    for _ in range(BOOTSTRAP_B):
        s = [vals[rng.randrange(len(vals))] for _ in vals]
        boots.append(sum(s) / len(s))
    boots.sort()
    return {"n_items": len(vals), "mean": round(mean, 6),
            "ci95": [round(boots[int(0.025 * BOOTSTRAP_B)], 6),
                     round(boots[int(0.975 * BOOTSTRAP_B) - 1], 6)]}


SUBSETS = {
    "premise_necessary": lambda it: it.meta.get("premise_necessary", False),
    "all": lambda it: True,
    "heldout:file": lambda it: "file" in it.meta.get("heldout_in", ()),
    "heldout:temporal": lambda it: "temporal" in it.meta.get("heldout_in", ()),
    "heldout:novel_premises": lambda it: "novel_premises" in it.meta.get("heldout_in", ()),
    "gold:1": lambda it: it.meta.get("n_gold") == 1,
    "gold:2-3": lambda it: 2 <= it.meta.get("n_gold", 0) <= 3,
    "gold:4-8": lambda it: 4 <= it.meta.get("n_gold", 0) <= 8,
    "gold:9+": lambda it: it.meta.get("n_gold", 0) >= 9,
}


def score(items: Sequence[Item], attempts: Iterable[Attempt], *, n: int, k_base: int,
          ks: Sequence[int] = HEADLINE_KS, seed: int = 0,
          allow_harness_faults: bool = False) -> dict[str, Any]:
    items = [it for it in items if str(k_base) in it.prompt["base"]]
    tallies = tally(items, list(attempts), n=n)
    hf = sum(t.harness_faults for t in tallies.values())
    if hf and not allow_harness_faults:
        raise ValueError(f"{hf} attempts carry fault=harness and are owed a re-run "
                         "(`scmd-bench grade --regrade-harness`); refusing to score")
    ks_ok = [k for k in ks if n > k]
    out: dict[str, Any] = {
        "n_samples": n, "k_base": k_base, "n_items": len(items),
        "n_void": sum(t.void for t in tallies.values()), "harness_faults": hf,
        "ks_reported": ks_ok, "ks_refused_n_le_k": [k for k in ks if n <= k],
        "subsets": {},
    }
    for name, pred in SUBSETS.items():
        rows = _subset_rows(items, tallies, pred)
        out["subsets"][name] = {f"pass@{k}": _mean_ci(rows, k, seed) for k in ks_ok}
        out["subsets"][name]["solved_any"] = (sum(1 for _n, c in rows if c) / len(rows)
                                             if rows else None)
    out["headline"] = {k: v for k, v in out["subsets"]["premise_necessary"].items()}
    return out


def mcnemar(a: dict[str, bool], b: dict[str, bool]) -> dict[str, Any]:
    """Exact two-sided McNemar on per-item solved indicators, over items both runs graded."""
    common = sorted(set(a) & set(b))
    b01 = sum(1 for i in common if not a[i] and b[i])
    b10 = sum(1 for i in common if a[i] and not b[i])
    m = b01 + b10
    if m == 0:
        p = 1.0
    else:
        tail = sum(math.comb(m, j) for j in range(0, min(b01, b10) + 1)) / 2 ** m
        p = min(1.0, 2 * tail)
    return {"n_items": len(common), "only_a": b10, "only_b": b01, "p_value": p}
