# How scmd-bench relates to existing Lean benchmarks

Surveyed 2026-09-13. Rows marked † were written from memory and have not been re-checked against
the source. Every other row was checked against the linked page on that date.

## The task each benchmark poses

| benchmark | system is given | system returns | contamination / split control | verification | budget convention | size |
|---|---|---|---|---|---|---|
| **scmd-bench v1** | target + **K premises, gold plus graded distractors** (BM25-hard / sibling / random) | full proof | three held-out splits (file / temporal / novel_premises), near-duplicate screen, exposure declared | file-prefix environment; kernel; axiom whitelist; theorems named ∈ BASE; one declaration | n = 64, pass@1/8/32, bootstrap CI, headline on `premise_necessary` | 500 dev / 2,000 test; 168,807 train |
| [LeanDojo Benchmark 4](https://leandojo.org/leandojo.html) | proof state; all accessible premises | tactics | `random` vs `novel_premises` splits | real environment | pass@1 under a search budget | 122,517 theorems |
| [miniCTX / -v2](https://cmu-l3.github.io/minictx/) | target + the file text above it + imports | full proof | **temporal**: projects added after model cutoffs (v2 cutoff 2024-11-28) | compiles; 120 s | success rate; later work plots against calls ≤ 32 | several hundred† |
| [SorryDB](https://arxiv.org/abs/2603.02668) | a real `sorry` in its repository at a fixed commit | replacement text | **live** snapshots (SorryDB-2601) | file compiles, exactly one fewer `sorry`, other goals unchanged, no new imports or lemmas | pass@32; 16 self-correction rounds | 1,000 eval of 5,663 |
| [VeriSoftBench](https://arxiv.org/abs/2602.18307) | target + **curated gold dependencies** or the full repository | full proof | proof bodies removed from context | no `sorry`/`admit`; trivially automatable tasks excluded | pass@8 + 3 repair rounds; 300 s | 500 |
| [TheoremBench (premised)](https://arxiv.org/abs/2606.09450) | target with **gold earlier results as hypotheses** | full proof | none (all evaluation) | compiles | pass@k, k ≤ 64 | 1,142 |
| [CSLibPremiseBench](https://arxiv.org/abs/2605.14549) | target + candidate pool | **ranked premises** (no proof) | test and dev from different modules | label audit (48.2% of source labels found in the elaborated term) | ranking metrics | 801 |
| [LeanHammer / premise selection](https://arxiv.org/abs/2506.07477) | goal + selected premises | hammer proof | Mathlib split | real environment | cumulative; 43.0% with gold premises, reported as an upper bound | Mathlib test |
| [PutnamBench](https://trishullab.github.io/PutnamBench/leaderboard.html) | formal statement | full proof | proofs not published | compiles; some entries SafeVerify | not standardised (maintainers ask for suggestions) | 672 Lean |
| miniF2F / ProofNet | formal statement | full proof | fixed test sets; defects audited in [2606.29493](https://arxiv.org/abs/2606.29493) | compiles | pass@32 / @3200 | 244 / 186† |
| [FormalMATH](https://arxiv.org/abs/2505.02735) | formal statement | full proof | — | compiles | pass@32 | 5,560 |

## What scmd-bench borrows, and from whom

| rule | source |
|---|---|
| the `novel_premises` split; near-duplicate blocks kept on one side | LeanDojo |
| leak-free context: the file up to the target, nothing after it | miniCTX, VeriSoftBench |
| exactly one declaration; no new imports, options or lemmas | SorryDB |
| axiom whitelist; `native_decide` refused; `implemented_by`/`unsafe` refused by text because `#print axioms` cannot see them | SafeVerify, Lean's *Validating a Lean Proof* |
| pass@32 as a standard point; every verifier call counts toward the budget | SorryDB, DeepSeek-Prover |
| a gold-premise control reported as an upper bound | LeanHammer |
| both gold-label definitions published (source-level dependencies, and the proof text they were resolved from) | CSLibPremiseBench, `zhu2025premise` |
| budget classes kept in separate columns | PutnamBench's stated gap |
| bootstrap intervals over items; seeds and temperature declared | `hochlehnert2025soberlook` |
| a shuffled-order re-draw for order-sensitive systems | `chen2024premiseorder` |

## What is new

1. **A fixed, sufficient, adversarial premise set.** BASE always contains the gold dependencies,
   padded to K with distractors, and the hardest tier is the BM25 top-scoring non-dependencies.
   The two nearest benchmarks each drop one side of this. TheoremBench and VeriSoftBench give gold
   premises with no distractors. LeanDojo, miniCTX and SorryDB give everything and select nothing.
   scmd-bench keeps selection and composition in one task and still grades a proof, not a
   ranking.
2. **The premise set is part of the verification contract.** A proof that names a theorem
   outside BASE is illegal, and the grader decides this from the elaborator's info tree, not from
   source text. It does so in the target's own file-prefix environment.
3. **The ambient floor is measured on every item and shapes the headline.** Items that a
   zero-parameter tactic solves are scored separately. On SCMD's own targets that floor was 26.5%,
   above both model arms, before anyone had measured it.
4. **The training set comes with the benchmark.** It is tokenizer-neutral, and its reference
   assembler reproduces the distribution a trained system (SCMD) actually saw, draw for draw. The
   eval set is drawn from that corpus's hold-out, so a system trained on the release is scored
   out of sample by construction.
5. **A named and an anonymised track on the same items.** The gap between them measures how much
   a system relies on knowing mathlib's lemma names.

## What scmd-bench does not do (v1)

- **No post-cutoff test set.** Every target is in public mathlib at `fabf563a` (2026-06-15), so a
  web-pretrained model may have seen it. Results are marked exposed or clean, and the planned
  v1.1 temporal set covers declarations added after the pin.
- **mathlib only.** The multi-library corpus_v3 is planned for v1.1. Each source needs its own
  pinned workspace and a license check.
- **Reach is reported, not bounded.** A tactic can still reach lemmas outside BASE without naming
  them. The `premise_necessary` headline and the per-attempt `reach_outside_base` report address
  this; neither eliminates it.
- **The gold label is the corpus's.** Items whose gold proof does not verify under the contract
  are dropped, not repaired, and the dataset card counts the drops by reason.
