"""Grade many attempts across worker processes, one Lean session per worker.

Items are the unit of work: every attempt for one item is graded in that worker's one prefix
environment for the item, so the (expensive) prefix is elaborated once per item per run. Workers
default to 8: LeanDLLM measured that 16 verification workers OOM a 94 GB host (a verification
session retains every environment it builds) while 8 ran twice as fast.
"""

from __future__ import annotations

import multiprocessing as mp
import os
import time
import traceback
from dataclasses import dataclass, field
from typing import Any, Callable, Iterable, Iterator

from scmd_bench.schema import Attempt, Fault, Item, Outcome

DEFAULT_WORKERS = 8


@dataclass
class Job:
    """All attempts to grade for one item. `attempts`: `(tag, track, k, sample_idx, proof)`."""

    item: dict[str, Any]
    attempts: list[tuple[str, str, int, int, str]]
    #: extra harness checks: `("resolve", k)` -- do all BASE names of this K exist in the env?
    checks: list[tuple[str, int]] = field(default_factory=list)


def _worker(inq: mp.Queue, outq: mp.Queue, grader_kw: dict[str, Any]) -> None:
    from scmd_bench.verify import Grader
    g = Grader(**grader_kw)
    while True:
        job = inq.get()
        if job is None:
            break
        item = Item.from_json(job.item)
        out: dict[str, Any] = {"item_id": item.item_id, "attempts": [], "checks": {},
                               "pid": os.getpid()}
        t0 = time.perf_counter()
        try:
            for tag, track, k, idx, proof in job.attempts:
                a = g.grade(item, proof, track=track, k=k, sample_idx=idx)
                out["attempts"].append((tag, a.to_json()))
            for name, k in job.checks:
                if name == "resolve":
                    out["checks"][f"resolve_{k}"] = g.unresolvable(item, k)
        except Exception:  # noqa: BLE001 -- a worker must report, never die silently
            out["error"] = traceback.format_exc()[-2000:]
            try:
                g._new_session()
            except Exception:  # noqa: BLE001
                pass
        out["wall_s"] = round(time.perf_counter() - t0, 2)
        out["restarts"] = g.restarts
        outq.put(out)
    g.close()


def run_jobs(jobs: Iterable[Job], *, workers: int = DEFAULT_WORKERS,
             grader_kw: dict[str, Any] | None = None) -> Iterator[dict[str, Any]]:
    """Yield one result dict per job, in COMPLETION order (callers key by `item_id`)."""
    jobs = list(jobs)
    ctx = mp.get_context("spawn")
    inq: mp.Queue = ctx.Queue()
    outq: mp.Queue = ctx.Queue()
    procs = [ctx.Process(target=_worker, args=(inq, outq, grader_kw or {}), daemon=True)
             for _ in range(max(1, min(workers, len(jobs))))]
    for p in procs:
        p.start()
    for j in jobs:
        inq.put(j)
    for _ in procs:
        inq.put(None)
    for _ in range(len(jobs)):
        yield outq.get()
    for p in procs:
        p.join(timeout=60)
