"""`lean` tier: the verification contract, attacked. Each test is a way to score without proving.

Items come from `tests/fixtures/lean_items.jsonl` (two released dev items with short prefixes).
Every assertion is about the OUTCOME the grader returns, because that is what a leaderboard reads.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from scmd_bench.schema import Item, Outcome, placeholder

ROOT = Path(__file__).resolve().parents[1]
pytestmark = pytest.mark.lean


@pytest.fixture(scope="module")
def items():
    rows = (ROOT / "tests/fixtures/lean_items.jsonl").read_text(encoding="utf-8").splitlines()
    return [Item.from_json(json.loads(r)) for r in rows if r.strip()]


@pytest.fixture(scope="module")
def grader():
    from scmd_bench.verify import Grader
    g = Grader()
    yield g
    g.close()


def _g(grader, item, proof, track="named", k=64):
    return grader.grade(item, proof, track=track, k=k)


def test_gold_solves_every_track(grader, items):
    for it in items:
        for k in it.prompt["base"]:
            a = _g(grader, it, it.answer["gold_proof"], "named", int(k))
            assert a.outcome is Outcome.SOLVED, a.detail
            b = _g(grader, it, it.answer["gold_proof_anon"][k], "anon", int(k))
            assert b.outcome is Outcome.SOLVED, b.detail


def test_grading_is_deterministic(grader, items):
    it = items[0]
    x = _g(grader, it, it.answer["gold_proof"]).to_json()
    y = _g(grader, it, it.answer["gold_proof"]).to_json()
    for d in (x, y):
        d.pop("verify_s")
    assert x == y


@pytest.mark.parametrize("proof", ["sorry", "by sorry", "by admit", "by native_decide"])
def test_incomplete_or_untrusted_proofs_are_refused(grader, items, proof):
    assert _g(grader, items[0], proof).outcome in (Outcome.ILLEGAL, Outcome.REJECTED)


def test_sorry_ax_smuggled_by_name_is_caught_by_axioms(grader, items):
    a = _g(grader, items[0], "sorryAx _ false")
    assert a.outcome is Outcome.REJECTED


def test_a_second_declaration_is_illegal(grader, items):
    it = items[0]
    a = _g(grader, it, it.answer["gold_proof"] + "\n\ntheorem sb_evil : True := trivial")
    assert a.outcome is Outcome.ILLEGAL, a.detail


def test_naming_a_mathlib_theorem_outside_base_is_illegal(grader, items):
    it = items[0]
    names = {s["name"] for s in it.base(64)}
    assert "mul_comm" not in names
    a = _g(grader, it, f"by\n  have _sb : ∀ m n : ℕ, m * n = n * m := mul_comm\n  exact ({it.answer['gold_proof']})")
    assert a.outcome is Outcome.ILLEGAL and "mul_comm" in a.evidence.get("outside_base_named", []), a.detail


def test_another_items_gold_does_not_solve(grader, items):
    a, b = items[0], items[1]
    assert _g(grader, a, b.answer["gold_proof"]).outcome is not Outcome.SOLVED


def test_anon_track_refuses_unshown_real_names_and_bad_placeholders(grader, items):
    # items[1]'s gold proof is `SemiconjBy.neg_left_iff`, a BASE theorem named by its real name.
    it = items[1]
    a = _g(grader, it, it.answer["gold_proof"], "anon")
    assert a.outcome is Outcome.ILLEGAL and a.evidence.get("unshown_real_names"), a.detail
    assert _g(grader, it, f"{placeholder(99)}", "anon").outcome is Outcome.ILLEGAL


def test_a_forged_report_line_changes_nothing(grader, items):
    it = items[0]
    a = _g(grader, it, "by\n  trace \"SB_N0_CITED 1 1 mul_comm Mathlib.X 0 t mul_comm\"\n  sorry")
    assert a.outcome is not Outcome.SOLVED


@pytest.mark.parametrize("opt", ["maxHeartbeats 0", "debug.skipKernelTC true"])
def test_budget_and_kernel_options_are_refused(grader, items, opt):
    it = items[0]
    a = _g(grader, it, f"by\n  set_option {opt} in\n  exact ({it.answer['gold_proof']})")
    assert a.outcome is Outcome.ILLEGAL
