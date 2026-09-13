"""Offline tests: no Lean, no release data."""

from __future__ import annotations

import itertools
import json
from pathlib import Path

import pytest

from scmd_bench import passk
from scmd_bench.assemble import (CURRICULUM_END, CURRICULUM_START, PremisePools, assemble_base,
                                 choose_k, curriculum_weights, tier_counts)
from scmd_bench.context import declaration_context, render_declaration, strip_attributes
from scmd_bench.schema import Attempt, Fault, Item, Outcome, item_id_of, placeholder
from scmd_bench.score import mcnemar, score
from scmd_bench.submission import (mask_comments_and_strings, spells, static_violations,
                                   substitute_placeholders)

ROOT = Path(__file__).resolve().parents[1]


# ── pass@k ───────────────────────────────────────────────────────────────────────────────────────
def test_passk_matches_enumeration_and_exact_arithmetic():
    n_checked = 0
    for n in range(2, 13):
        for c in range(0, n + 1):
            for k in range(1, n):
                assert abs(passk.pass_at_k(n, c, k) - passk.pass_at_k_bruteforce(n, c, k)) < 1e-12
                assert abs(passk.pass_at_k(n, c, k) - passk.pass_at_k_exact(n, c, k)) < 1e-12
                n_checked += 1
    assert n_checked > 500


def test_passk_refuses_n_equal_k():
    with pytest.raises(passk.PassAtKError):
        passk.pass_at_k(8, 1, 8)


# ── static checks ────────────────────────────────────────────────────────────────────────────────
def test_masking_preserves_offsets_and_hides_comments_and_strings():
    text = 'by\n  simp -- sorry here\n  /- nested /- sorry -/ -/ exact "sorry"'
    m = mask_comments_and_strings(text)
    assert len(m) == len(text)
    assert "sorry" not in m and "simp" in m and "exact" in m


@pytest.mark.parametrize("proof,bad", [
    ("sorry", True), ("by\n  exact sorry", True), ("by admit", True), ("by native_decide", True),
    ("by\n  run_tac pure ()", True), ("unsafe_thing", False), ("by exact h.sorry_free", False),
    ("by simp [foo_sorry]", False), ("by\n  set_option maxHeartbeats 0 in simp", True),
    ("by\n  set_option debug.skipKernelTC true in rfl", True),
    ("by\n  set_option push_neg.use_distrib true in push_neg", False),
    ("by simp -- sorry", False), ('by exact "unsafe"', False), ("by\n  #eval 1", True),
    ("by exact (implemented_by)", True),
])
def test_static_violations(proof, bad):
    assert bool(static_violations(proof)) is bad


def test_placeholders_substitute_absolute_names_and_record_spans():
    names = ["Finset.sum_comm", "add_comm"]
    sub = substitute_placeholders("by rw [⟪p1⟫, ⟪p0⟫] -- ⟪p1⟫", names)
    assert sub.text == "by rw [_root_.add_comm, _root_.Finset.sum_comm] -- ⟪p1⟫"
    assert [sub.text[a:b] for a, b in sub.spans] == ["_root_.add_comm", "_root_.Finset.sum_comm"]
    assert not sub.errors
    assert substitute_placeholders("⟪p2⟫", names).errors


def test_spells():
    assert spells("Finset.sum_comm", "Finset.sum_comm")
    assert spells("sum_comm", "Finset.sum_comm")
    assert spells("@_root_.Finset.sum_comm", "Finset.sum_comm")
    assert not spells("h.trans", "Eq.trans")
    assert not spells("comm", "Finset.sum_comm")


# ── rendering ────────────────────────────────────────────────────────────────────────────────────
def test_render_keeps_namespace_universes_and_wrapper():
    src, name, off = render_declaration("@[simp, to_additive]\nlemma Foo.bar.{u} (x : Nat) : x = x",
                                        "set_option maxHeartbeats 400000 in", "rfl")
    assert src == ("set_option maxHeartbeats 400000 in\n"
                   "theorem Foo.sb_target.{u} (x : Nat) : x = x := rfl")
    assert name == "Foo.sb_target" and src[off:] == "rfl"


def test_strip_attributes_handles_brackets_inside_docstrings():
    s = '@[to_additive /-- a `]` in prose -/]\ntheorem t : True'
    assert strip_attributes(s) == "theorem t : True"


def test_declaration_context_cuts_wrapper_and_inserts_options_after_imports():
    source = "module\n\npublic import Mathlib.A\nimport Mathlib.B\n\nnamespace X\nset_option foo 1 in\ntheorem t : True := trivial\n"
    cut = source.index("theorem")
    ctx = declaration_context(source, cut, "set_option foo 1 in")
    assert "set_option foo 1 in" not in ctx
    assert ctx.index("set_option autoImplicit false") > ctx.index("import Mathlib.B")
    assert ctx.rstrip().endswith("namespace X")


# ── assembly ─────────────────────────────────────────────────────────────────────────────────────
def _toy_pools():
    module_of = {}
    for m in range(6):
        for j in range(20):
            module_of[f"N{m}.p{j}"] = f"M{m}"
    return PremisePools.build(module_of)


def test_curriculum_endpoints_are_exact():
    assert curriculum_weights(0.0) == CURRICULUM_START
    assert curriculum_weights(1.0) == CURRICULUM_END
    for i in range(101):
        assert abs(sum(curriculum_weights(i / 100)) - 1) < 1e-9


def test_tier_counts_sum_and_k_choices():
    import random
    for n in range(0, 70):
        assert sum(tier_counts(n, CURRICULUM_END, random.Random(n)).values()) == n
    assert {choose_k(0, 0, i) for i in range(200)} == {8, 16, 32, 64}


def test_assembly_is_pure_sufficient_and_never_leaks_gold():
    pools = _toy_pools()
    gold = ["N0.p1", "N1.p2", "N0.p3"]
    hard = [f"N2.p{j}" for j in range(20)] + gold
    for ex in range(30):
        a = assemble_base("N0.p0", gold, pools=pools, hard=hard, progress=1.0, example_id=ex, k=16)
        b = assemble_base("N0.p0", gold, pools=pools, hard=hard, progress=1.0, example_id=ex, k=16)
        assert a == b
        assert a.k == 16 and len(set(a.names)) == 16
        assert sorted(n for n, t in zip(a.names, a.tiers) if t == "gold") == sorted(gold)
        assert "N0.p0" not in a.names


def test_allowed_restricts_every_distractor():
    pools = _toy_pools()
    allowed = {f"N3.p{j}" for j in range(20)} | {f"N4.p{j}" for j in range(20)}
    gold = ["N0.p1"]
    a = assemble_base("N0.p0", gold, pools=pools, hard=["N5.p1", "N3.p2"], progress=1.0, k=32,
                      allowed=allowed | set(gold))
    assert all(n in allowed for n, t in zip(a.names, a.tiers) if t != "gold")


def test_sufficiency_raises_k():
    pools = _toy_pools()
    gold = [f"N1.p{j}" for j in range(10)]
    a = assemble_base("N0.p0", gold, pools=pools, example_id=3, k=8)
    assert a.k == 16 and a.k_drawn == 8


# ── items, views, scoring ────────────────────────────────────────────────────────────────────────
def _item(i=0, necessary=True):
    prompt = {"target": " (n : ℕ) : n + 0 = n",
              "base": {"64": [{"name": "Nat.add_zero", "rest": " (n : ℕ) : n + 0 = n"}]}}
    grading = {"file": "Mathlib/X.lean", "char_start": i, "stmt_source": "theorem x (n : ℕ) : n + 0 = n",
               "prefix_source": "", "module": "Mathlib.X"}
    return Item(item_id=item_id_of(prompt, grading), split="dev", prompt=prompt, grading=grading,
                answer={"gold_proof": "Nat.add_zero n"},
                meta={"premise_necessary": necessary, "heldout_in": ["file"], "n_gold": 1})


def test_view_hides_answer_grading_and_real_names_on_anon():
    it = _item()
    for track in ("named", "anon"):
        v = json.dumps(it.view(track, 64), ensure_ascii=False)
        assert "Nat.add_zero n" not in v and "Mathlib/X.lean" not in v
    anon = it.view("anon", 64)
    assert anon["base"][0]["name"] == placeholder(0)
    assert "Nat.add_zero" not in json.dumps(anon, ensure_ascii=False)


def test_item_id_is_content_addressed():
    assert _item(0).item_id != _item(1).item_id
    assert _item(0).item_id == _item(0).item_id


def test_missing_samples_count_as_failures_and_harness_faults_block_scoring():
    items = [_item(0), _item(1)]
    atts = [Attempt(items[0].item_id, s, Outcome.SOLVED) for s in range(3)]
    res = score(items, atts, n=4, k_base=64, ks=(1,))
    # item0: 3/4 solved -> 0.75; item1: no rows -> 0.0
    assert res["subsets"]["all"]["pass@1"]["mean"] == pytest.approx(0.375)
    bad = atts + [Attempt(items[1].item_id, 0, Outcome.TIMEOUT, Fault.HARNESS)]
    with pytest.raises(ValueError):
        score(items, bad, n=4, k_base=64, ks=(1,))


def test_mcnemar_exact():
    a = {str(i): i < 10 for i in range(40)}
    b = {str(i): i < 20 for i in range(40)}
    r = mcnemar(a, b)
    assert r["only_b"] == 10 and r["only_a"] == 0
    assert r["p_value"] == pytest.approx(2 * 0.5 ** 10)


def test_released_items_never_show_their_answer():
    for path in sorted(p for p in (ROOT / "data").glob("v*/*.jsonl") if not p.name.startswith("_")):
        for line in path.read_text(encoding="utf-8").splitlines():
            it = Item.from_json(json.loads(line))
            for k in it.prompt["base"]:
                v = json.dumps(it.view("anon", int(k)), ensure_ascii=False)
                gold = it.answer["gold_proof"].strip()
                if len(gold) > 40:
                    assert gold not in v


def test_clean_rest_drops_leftover_heads_only():
    from scmd_bench.schema import clean_rest
    assert clean_rest(" lemma empty : Absorbs M s ∅") == " : Absorbs M s ∅"
    assert clean_rest(" def extend₂ (f : α → β → γ) : hatα") == " (f : α → β → γ) : hatα"
    assert clean_rest(" {a b} : f a ≤ f b ↔ a ≤ b") == " {a b} : f a ≤ f b ↔ a ≤ b"
