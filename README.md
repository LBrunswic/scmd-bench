# scmd-bench

**Premise-conditioned Lean 4 proving.** Given a mathlib theorem statement and a set of K premises that
is guaranteed to be sufficient but padded with adversarial distractors, write a proof that Lean
accepts — citing only those premises.

This repository has three parts, all built from the same corpus:

| | what | where |
|---|---|---|
| **training set** | 168,807 mathlib theorems with gold dependencies and proofs, tokenizer-neutral, plus the premise table, BM25 hard negatives and a reference BASE assembler | release asset `scmd-bench-v1-train.tar` |
| **evaluation set** | 500 dev and 2,000 test items from the corpus's hold-out, each with a frozen BASE at K = 64 and K = 16 | `data/v1/` |
| **evaluation environment** | a verifier implementing a written contract, shipped as a network-free container | `scmd_bench/`, `docker/` |

The task and its data come from **SCMD**, a set-conditioned masked-diffusion prover. scmd-bench
exists so that other approaches can train and be ranked on exactly the task SCMD trains on:
autoregressive LLMs, retrieval provers, and pointer or diffusion models.

- [`docs/RULES.md`](docs/RULES.md) — the rules a result must follow (v1.0)
- [`docs/COMPARISON.md`](docs/COMPARISON.md) — how this relates to LeanDojo, miniCTX, SorryDB,
  VeriSoftBench, TheoremBench, PutnamBench…
- [`docs/DATASET_CARD.md`](docs/DATASET_CARD.md) — provenance, filters and what they removed, known
  limitations
- [`docs/SUBMITTING.md`](docs/SUBMITTING.md) — how to get on the leaderboard

## An item

This is a real dev item, shown on the anonymised track at K = 16. The two starred slots are the
gold premises; the star is not part of the prompt.

```text
theorem target {α} [BooleanAlgebra α] [IsAtomic α] {x y : α} :
    x = y ↔ ∀ a, IsAtom a → (a ≤ x ↔ a ≤ y)

  ⟪p0⟫ : ∀ a : α, a ≤ a
  ⟪p1⟫ {a b} : f a ≤ f b ↔ a ≤ b
  ⟪p3⟫ : a = b ↔ a ≤ b ∧ ¬a < b
* ⟪p5⟫ : a ≤ b → b ≤ a → a = b
  ⟪p10⟫ : ⊥ ⋖ a ↔ IsAtom a
* ⟪p15⟫ {α} [BooleanAlgebra α] [IsAtomic α] {x y : α} : x ≤ y ↔ ∀ a, IsAtom a → a ≤ x → a ≤ y
  …                                                        (16 slots)
```

A proof that verifies:

```lean
by
  refine ⟨fun h => h ▸ by simp, fun h => ?_⟩
  exact ⟪p5⟫ (⟪p15⟫.2 fun a ha hx => (h a ha).1 hx)
    (⟪p15⟫.2 fun a ha hy => (h a ha).2 hy)
```

A system returns only the text after `:=`. The `named` track shows the real mathlib names
(`le_antisymm`, …) instead of placeholders.

## Quickstart

```bash
pip install -e .                                          # the harness is stdlib-only
scmd-bench view --items data/v1/dev.jsonl --track anon --k 64 | head -1

# grading needs Lean v4.31.0 + mathlib fabf563a + the REPL; the container has all three
docker build -t scmd-bench:1.0 -f docker/Dockerfile .
docker run --rm --network none -v $PWD:/work scmd-bench:1.0 \
  grade --items /work/data/v1/dev.jsonl --submission /work/baselines/gold/dev.named.jsonl \
        --track named --k 64 --out /work/graded.jsonl
```

## What "solved" means

These checks are summarised from RULES §3, and all of them are enforced.

1. The proof elaborates in the target's **file-prefix environment**: its own file up to the
   target, so the target and anything after it do not exist.
2. It uses no `sorry`. The heartbeat budget is deterministic.
3. It makes exactly one declaration.
4. Axioms are limited to `propext`, `Classical.choice` and `Quot.sound`.
5. There are no `unsafe`, `implemented_by`, `native_decide` or budget/kernel options.
6. **Every theorem the proof names is in BASE or ambient**: defined outside mathlib, or private.
   This is decided from Lean's info tree, not from the text.
7. On the anonymised track, BASE premises are cited by placeholder.

The **headline is scored on items no zero-parameter tactic solves** (`rfl`, `simp`, `aesop`,
`exact?`, … — 16 of them). On SCMD's own held-out targets that floor was 26.5% before anyone
measured it.

## Baselines and validation (v1.0)

| | dev (500) | test (2,000) |
|---|---|---|
| gold proof, both tracks | 1.000 | 1.000 |
| ambient floor (any of 16 zero-parameter proofs) | 0.114 | 0.099 |
| qwen2.5-7B, CPU, named, K=16, n=4 (partial: 100 headline items) | solved 0.04, pass@1 0.018 | — |

The full table is in [`LEADERBOARD.md`](LEADERBOARD.md) and the harness checks are in the
[dataset card](docs/DATASET_CARD.md#harness-validation). The container and host grader agree on
500 of 500 dev verdicts.

## Rebuilding the data

`builder/` regenerates everything from LeanDLLM's corpus_v2 (`corpus_id 9831f3a0…`). It needs
the LeanDLLM source on `PYTHONPATH` and its data directory, and each manifest records the
upstream commit. The released files do not depend on it.

## License

Apache-2.0, as mathlib. See `NOTICE`.
