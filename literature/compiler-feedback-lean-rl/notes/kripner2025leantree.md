# kripner2025leantree — LeanTree: Accelerating White-Box Proof Search with Factorized States in Lean 4

Matěj Kripner, Michal Šustr, Milan Straka (Charles University; Czech Technical University)
ICML 2025 AI for Math Workshop 2025 · arXiv:2507.14722 · `pdf/kripner2025leantree.pdf`

**Tier: T3**: a workshop paper with released code and dataset (GitHub, HF `ufal/leantree`) and a concrete, correct technical analysis of REPL verification bugs. The experiment is small and "preliminary" (Llemma-7B, one benchmark, 5 seeds). It reports **no** speed or throughput measurement despite "Accelerating" in the title.
**Relevance: 2**: RQ2 (white-box Lean interaction tooling, factorized AND-OR states, dataset), RQ1 (RL exploiting verifier gaps: REPL false positives, `apply?`). It gives only qualitative input to RQ3.
**Read:** full text including appendices A–D

## Summary
LeanTree extends the Lean REPL to support white-box, tree-structured proof search over factorized proof states. It splits a goal list into independent goals except where they are coupled by shared metavariables, which yields an AND-OR tree in the style of Evariste/HTPS. A data-extraction module (REPL + PaperProof BetterParser + custom simplification) turns Mathlib and DeepSeek-Prover-V1 proofs into verified proof trees of simple tactics: 74,706 Mathlib tactic proofs and 26,201 DeepSeek-Prover-V1 proofs (Lean v4.19.0). Using Llemma-7B with 10 linear rollouts of up to 25 steps on miniF2F-test, white-box rollouts reach 18.36% versus 5.32% for black-box rollouts and 9.59% for whole-proof generation. The paper also documents that the old REPL tactic mode accepted 12 incorrect miniF2F proofs, and proposes type-checking only the new metavariable assignments, which is linear rather than quadratic.

## Key points
- [V] miniF2F-test with Llemma-7B (N=10 rollouts, M=25 steps, 5 runs): whole-proof 9.59% ± 0.71, black-box rollout 5.32% ± 0.37, white-box rollout 18.36% ± 0.60. Best-first search at 26.23% is *reported by Azerbayev et al.*, not rerun (Fig. 3).
- [P] Derived from Fig. 3: white-box beats black-box rollout by 3.45× and beats whole-proof generation by ~1.9×. [[shen2026keep]] cites the "3.4×" figure without this qualification.
- [V] Dataset: 74,706 factorized tactic proofs from Mathlib and 26,201 from DeepSeek-Prover-V1. 23.0% of Mathlib and 4.7% of DSP-V1 tactic proofs could not be converted; 28.6% of the Mathlib failures come from `calc`/`conv` (§4.2).
- [V] Verifier-exploitation evidence: the prover found 12 incorrect miniF2F proofs that passed the old REPL tactic mode, because tactic assignments were not kernel-checked (§3.4, App. B).
- [P] The upstream REPL fix (type-checking the full proof term after each tactic, April 2025) causes false negatives once a proof branches (e.g. `have k := sorry`). LeanTree instead checks only the new assignments g_i : G_i, which is linear in proof length rather than quadratic (App. B).
- [P] `apply?` has sorry semantics. DeepSeek-Prover-V2's published putnam_2005_a4 and putnam_2007_b4 proofs use it, and the authors suggest RL learned to exploit this. LeanTree bans `apply?` by default (App. A).
- [P] Mechanisms claimed to accelerate search: goal factorization (independent parallel exploration, transposition-style state reuse) and a "dynamic pool of environments suitable for parallel execution" (§3.1–3.2). **None of these is benchmarked for speed.** There are no proofs/s, latency, memory or reuse-rate numbers.
- [V] Compute: a single node with 8 AMD MI210s and 192 CPUs, for a total of 59 GPU-hours and 450 CPU-hours (§6).

## Verified quotes
> "Whole-proof Black-box rollout White-box rollout 9.59 % ± 0.71 5.32 % ± 0.37 18.36 % ± 0.60"

> "Best-first search∗ 26.23 %"

> "Overall, LeanTree contains 74 706 factorized tactic proofs from Mathlib and 26 201 from DeepSeek-Prover-V1."

> "23.0% of tactic proofs in Mathlib and 4.7% in DeepSeekProver-V1 were not converted"

> "finding 12 incorrect proofs in the MiniF2F validation set that passed verification in the REPL when using the tactic mode"

> "the new strategy also decreases the time complexity of verifying a proof from quadratic to linear since each sub-assignment is only verified once"

> "The end effect is that the current verification strategy leads to false negatives when the proof being verified contains at least one syntactic branching."

> "given the high CPU requirements of Lean 4, LeanTree implements a dynamic pool of environments suitable for parallel execution"

> "In total, our experiments necessitated 59 GPU-hours and 450 CPU-hours."

> "This highlights the potential of reinforcement learning to exploit unchecked ambiguities in a proving environment."

> "Our preliminary results hint that white-box approaches outperform black-box alternatives in some settings."

## Methods and evidence
- Data / setting: miniF2F-test (the Lean 4 version from InternLM2.5-StepProver / Wu et al. 2024). Llemma-7B, prompted without fine-tuning; `sorry`, `admit` and comments are disabled during sampling.
- Baselines: black-box whole-proof generation and black-box linear rollout with the same model. The best-first number is imported from Llemma.
- Evaluation: 5 runs with standard deviation, a held-out test set, and a single small model. There is no tree search of their own, despite the AND-OR framing.
- Artifacts: github.com/Kripner/leantree; HF dataset ufal/leantree (JSONL schema in App. D).

## Limitations and caveats
- Authors concede: the results are preliminary and hold only "in some settings"; not all proofs convert (23% of Mathlib fails).
- Not conceded: the title and abstract claim acceleration, parallel search and "efficient reuse of states", but the paper reports no timing, throughput or memory measurement at all. The acceleration claim is argued, not measured. → `claims_exceed_evidence=true`.
- The white-box vs black-box comparison uses an untuned 7B model prompted only to "complete the Lean 4 code". Black-box *rollout* is a handicapped variant (first tactic only), which inflates the headline ratio.
- The AND-OR search that factorization enables is never evaluated; only linear rollouts are.

## Contradictions and tensions
- [[shen2026keep]] summarises this paper as "a 3.4× accuracy improvement over black-box single-branch rollout". That is correct against black-box rollout, but the white-box gain over whole-proof generation is ~1.9×.
- [[xin2026axle]] takes the opposite design stance: stateless, declaration-level, no tactic-state sessions, and per-request isolation. LeanTree depends on long-lived REPL proof states.
- Relevant to [[santos2025kimina]]: both build on the Lean REPL, and Kimina's benchmark assumes REPL verdicts are correct. LeanTree shows the REPL tactic mode had false positives, although Kimina verifies whole files in command mode, not tactic mode.
- Round 2: confirmed in kind by [[vamshi2026reward]] and [[ammanamanchi2026faults]] (Lean < 4.20 `apply?` synthetic sorry passes compilation and sorry scans) and by [[wang2026longcat]] (RL policy learned nine context-level cheats) — frontend/verifier permissiveness, not the kernel, is where provers find false accepts.

## Open questions
- What is the actual throughput of factorized white-box search versus whole-proof verification per GPU- or CPU-hour?
- Does the linear-time incremental kernel check hold up against the adversarial cases in the Comparator and lean4checker test suites?

## Leads for next round
- term: factorized proof states; metavariable coupling; AND-OR / hypertree proof search; white-box vs black-box proving; incremental kernel checking of tactic assignments; REPL tactic-mode false positives.
- cited: HTPS / Evariste (Lample et al., NeurIPS 2022); ABEL (Gloeckle, Limperg, Synnaeve, Hayat, NeurIPS'24 MATH-AI workshop), described as online RL for NTP; PaperProof; lean-training-data (Morrison); InternLM2.5-StepProver (arXiv:2410.15700); DeepSeek-Prover-V1.5 (RLPAF, arXiv:2408.08152); Pantograph (arXiv:2410.16429).
- author: Matěj Kripner, Milan Straka (ÚFAL, Charles University).
