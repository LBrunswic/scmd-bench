"""Test tiers. `offline` always runs. `release` needs the training release on disk
(`SCMD_BENCH_RELEASE`), `lean` needs the pinned Lean + mathlib + REPL. Select with
`SCMD_BENCH_TIERS=offline,release,lean`. A SELECTED tier whose dependency is missing is a session
error, never a silent skip: a skipped verifier test is exactly the evidence a release claims."""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

TIERS = {t.strip() for t in os.environ.get("SCMD_BENCH_TIERS", "offline").split(",") if t.strip()}


def pytest_configure(config):
    for t in ("release", "lean"):
        config.addinivalue_line("markers", f"{t}: needs the {t} tier")


def pytest_collection_modifyitems(config, items):
    keep, drop = [], []
    for it in items:
        tier = next((t for t in ("release", "lean") if it.get_closest_marker(t)), "offline")
        (keep if tier in TIERS else drop).append(it)
    items[:] = keep
    config.hook.pytest_deselected(items=drop)


def pytest_sessionstart(session):
    if "release" in TIERS:
        rel = Path(os.environ.get("SCMD_BENCH_RELEASE", ""))
        if not (rel / "premises.jsonl.gz").is_file():
            raise pytest.UsageError(f"tier `release` selected but SCMD_BENCH_RELEASE={rel} has no premises.jsonl.gz")
    if "lean" in TIERS:
        from scmd_bench.repl import LeanPaths
        p = LeanPaths.discover()
        if not p.repl_bin.is_file():
            raise pytest.UsageError(f"tier `lean` selected but no REPL binary at {p.repl_bin}")
