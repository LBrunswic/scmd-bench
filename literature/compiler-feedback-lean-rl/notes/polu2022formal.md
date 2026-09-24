# polu2022formal — Formal Mathematics Statement Curriculum Learning

Stanislas Polu, Jesse Michael Han, Kunhao Zheng, Mantas Baksys, Igor Babuschkin, Ilya Sutskever (OpenAI, École Polytechnique, Cambridge)
ICLR 2023 (notable top-25%; confirmed via openreview.net/forum?id=-P7G-8dmSh4 and iclr.cc/virtual/2023/poster/11923 by web search on 2026-09-23. The archived text is arXiv v1, 3 Feb 2022, marked "Preprint. Under review.") · arXiv:2202.01344 · `pdf/polu2022formal.pdf`

**Tier: T1** — Peer-reviewed at ICLR 2023. Its method (verifier-filtered expert iteration on proof-search outputs) became the standard self-training baseline used and extended by later Lean provers in this KB: DeepSeek-Prover's SFT expert iteration ([[xin2024deepseeka]]) and Goedel-Prover-V2's "standard expert iteration" ([[lin2025goedela]]). lean-gym and the miniF2F curriculum statements are released; model weights are not. Its environment has a published critique: [[yang2023leandojo]] measures lean-gym misjudging 21.1% of correct proofs. That error biases the paper's pass rates *downward*, so it does not undercut the conclusions. The compute-matched claim rests on a fitted "adjusted compute" extrapolation, not on a run.
**Relevance: 2** — RQ1: the classic verifier-filtered self-training loop, with per-iteration gains, compute cost, and a compute-adjusted comparison with sampling only. RQ2: lean-gym, an early REPL environment and its scaling notes. Lean 3 with a 774M model, so the numbers are historical.
**Read:** full text (§1–8, Tables 1–2, Fig. 1–4, App. B lean-gym, D synthetic inequalities).

## Summary
GPT-f (774M decoder, WebMath pre-training) is fine-tuned on mathlib tactic data. It is then improved by expert iteration: best-first proof search (d=512 expansions, e=8 samples each) on a statement set; successful searches, as verified by Lean via lean-gym, become new proofstep data; visited-but-unproved goals become negatives for a "proofsize" value objective. The loop re-fine-tunes θ0 on the globally deduplicated accumulated data each iteration, for 8 iterations. Against a sample-only loop, including a fitted "adjusted compute" line that spends expert iteration's extra train and sample compute on more test-time searches, expert iteration scales with a higher exponent. On synthetic inequalities of controlled difficulty, it closes depth-6 problems that sampling never reaches, with no ground-truth proofs at that level. With 327 hand-formalized competition statements added as curriculum, it reaches 36.6% on miniF2F-test (pass@64) and 47.3% on miniF2F-valid.

## Key points
- [V] Expert iteration on mathlib-train raises mathlib-valid pass@1 from 56.3% (θ1) to 62.6% (θ9), following "a clear logarithmic scaling law". That is ≈6.3 pp over 8 iterations, with diminishing returns per iteration (§4.6, Fig. 1).
- [V] Proved mathlib-train statements rise from 17390 (67.8%) at iteration 1 to 19476 (76.0%) at iteration 9. By iteration 9, "more than 90%" of the training data is model-generated (§4.6).
- [V] Compute-matched comparison: the scaling exponent of expert iteration is "substantially higher" than that of scaling test-time proof search. [P] The comparison is against an *extrapolated* adjusted-compute line (fit of the sample-only curve, shifted), not a run at matched compute (Fig. 2).
- [V] Curriculum without proofs: on synth-ineq, expert iteration closes 6 problems at ND=6, while sample-only stays at 0 (§5.2, Fig. 3).
- [V] Full-curriculum results on miniF2F: 47.3% on valid and 36.6% on test at a=64 attempts (§6.2).
- [P] In Table 2 (column order reconstructed from the extracted text), miniF2F-test pass@1 goes from 25.9 (θ1) to 27.2 (θ9 mathlib) to 29.6 (θ9 full), and pass@64 from 33.6 to 35.2 to 36.6. mathlib-valid pass@1 goes from 56.3 to 62.6 (mathlib-only) and 61.7 (full). So on the out-of-distribution target, 8 iterations of expert iteration plus a hand-made curriculum buy ≈+3.7 pp pass@1 and +3.0 pp pass@64 (Table 2).
- [V] Compute cost: a full expert iteration to train θ9full took "about 2000 A100 days". One proof search (a=1, d=512, e=8) costs about 0.1 A100 hour (§7.1). [P] Each full-curriculum iteration runs ≈33.2k searches (Fig. 4 caption), so ≈3.3k A100-hours of search per iteration (derived). The Lean-side (CPU) verification cost is not separated.
- [V] The value objective matters only modestly. The proofsize objective beats the outcome objective by 0.7 pp pass@1 and 0.4 pp pass@8 on mathlib-valid (Table 1).
- [V] Stability: "global deduplication across iterations" of proofsteps and proofsize tuples "we found to be important to maintain the stability of the expert iteration procedure" (§4.5).
- [V] Model size: bigger models have higher pass@1, but "for a fixed amount of compute, sampling more attempts from a smaller model leads to a better final performance" (§7.1). No numbers are reported.
- [V] The authors do not frame the method as RL. They argue that naive RL is "unlikely to succeed" because of the infinite action space and the lack of self-play, and use statement curricula as the substitute for self-play (§1).
- [V] lean-gym (RQ2): a stdin/stdout REPL with `init_search(declaration)` and `run_tac`. It is stateful, it scaled to "thousands of cores running thousands of proof searches in parallel", and it is blocking, which prevents parallelism inside a single proof search (App. B). No per-call latency is given.

## Verified quotes
> "We show that at same compute budget, expert iteration, by which we mean proof search interleaved with learning, dramatically outperforms proof search only."

> "The pass@1 on mathlib-valid goes from 56.3% for θ1 to 62.6% for θ9 . The performance steadily improves and follows a clear logarithmic scaling law on mathlib-valid."

> "The number of statements proved in mathlib-train goes from 17390 (67.8%) at iteration 1 to 19476 (76.0%) at iteration 9"

> "By iteration 9, the model is trained on more than 90% generated data."

> "As shown by figure 2, the scaling exponent of expert iteration is substantially higher than the scaling exponent associated with solely scaling test-time compute (running more proof searches)"

> "The adjusted compute line is computed by fitting the sample only curve and shifting it to approximate a setup where we would focus all the additional compute used by expert iteration"

> "expert iteration is capable of closing 6 problems of difficulty ND = 6 without having been provided with any seed ground-truth proof for this difficulty level"

> "the sample only loop remaining stuck at 0 for ND = 6"

> "We achieve a 47.3% pass rate (using a = 64 attempts) on miniF2F-valid and a 36.6% pass rate on miniF2F-test"

> "24.6% 25.9% 27.2% 29.6% 29.2% 31.1% 33.0% 34.5% 33.6% 35.2% 36.6%"

> "48.4% 56.3% 62.6% 61.7% 66.3% 70.7% 69.8% 72.0% 75.8% 75.3%"

> "running a full expert iteration to train θ9full required about 2000 A100 days of compute. Running one full proof search (a = 1 d = 512 e = 8) when properly parallelised, requires on average about 0.1 A100 hour of compute."

> "The total number of attempts per iteration in our full loop is 25k + 5.6k + 8 ∗ 327 ≈ 33.2k"

> "56.3% 55.6% 57.6% 57.5% 66.3% 65.9%"

> "Note that we use a global deduplication across iterations for both proofsteps and proofsize tuples which we found to be important to maintain the stability of the expert iteration procedure."

> "for a fixed amount of compute, sampling more attempts from a smaller model leads to a better final performance"

> "These two differences make a naive application of reinforcement learning to formal mathematics unlikely to succeed."

> "At the end of the expert iteration, 100 out of the 327 statements from miniF2F-curriculum end up being closed"

> "Note that lean-gym is stateful, meaning that distributing proof searches on multiple lean-gym instances requires to track which instance is associated with which proof search. In practice, we were able to scale the use of lean-gym to thousands of cores running thousands of proof searches in parallel. Finally, lean-gym's REPL interface is blocking, preventing inner-proof search parallelization"

> "Preprint. Under review."

## Methods and evidence
- Data / setting: Lean 3 and mathlib (PACT splits; mathlib-train has 25k statements), synth-ineq (5,600 generated inequalities), miniF2F-curriculum (327 hand-formalized statements, disjoint from miniF2F), and miniF2F valid/test.
- Baselines: PACT (Han et al. 2021; Zheng et al. 2021), a sample-only loop, and an adjusted-compute extrapolation.
- Evaluation: pass@1/8/64. pass@1 and pass@8 are averaged over about 32 attempts to reduce noise. There are no seeds and no error bars, and there is one expert-iteration run per configuration.
- Artifacts: lean-gym (github.com/openai/lean-gym) and the miniF2F-curriculum statements are released. Models are not.

## Limitations and caveats
- Stated: the model cannot chain more than 2–3 non-trivial reasoning steps; cuts are shallow; only 100/327 curriculum statements are ever closed ("lack of density").
- Not stated: the matched-compute claim relies on a fitted, shifted curve rather than an actual run. The out-of-distribution gain on miniF2F-test is small (+3.7 pp pass@1). The environment (lean-gym) was later shown to reject 21.1% of correct proofs ([[yang2023leandojo]]), so reported rates are lower bounds and the training signal was noisy. Evaluation uses a=64 attempts per statement × (d=512, e=8) tactic samples each, far more verifier calls than "pass@64" suggests.
- The abstract's "dramatically outperforms" is supported by the exponent comparison in Fig. 2, which is on mathlib-valid, but the miniF2F gains are modest. I leave `claims_exceed_evidence=false` because the abstract's claims are qualitative and each is shown in a figure.

## Contradictions and tensions
- [[xin2024deepseeka]]: DeepSeek's online RL over expert-iteration SFT adds +1.2 pp at miniF2F pass@128 (51.6 vs 50.4). Polu's 8 expert iterations add +3.7 pp pass@1 / +3.0 pp pass@64 on miniF2F-test at ≈2000 A100-days. In both lineages, verifier-filtered self-training moves the out-of-distribution benchmark by only a few points per stage. The big gains come from data (curricula, statements), not from the RL/EI algorithm. The two are not directly comparable (Lean 3 tree search with a 774M model vs Lean 4 whole-proof generation with a 7B model).
- [[yang2023leandojo]]: attributes "25.9% → 29.6% MiniF2F with RL" to this paper. The numbers match Table 2 (θ1 → θ9full, miniF2F-test pass@1), but the method is expert iteration, not RL. LeanDojo's 21.1% lean-gym misjudgement rate means this paper's training loop discarded a sizeable share of correct proofs.
- [[lin2025goedela]]: Goedel-V2 still calls expert iteration "standard" and keeps statement-difficulty scaffolding (easier sub-goals, harder variants). That is a direct descendant of this paper's statement curriculum, now automated by LLMs as §8 anticipated.

## Open questions
- How much of expert iteration's advantage survives a real compute-matched run rather than the adjusted-compute extrapolation?
- What was the CPU/Lean-side cost per search (d=512 × e=8 run_tac calls), as opposed to A100 time?
- Would fixing lean-gym's 21.1% false-negative rate have changed the iteration curve?

## Leads for next round
- term: "expert iteration", "statement curriculum", "proofsize objective", "global deduplication", "sample-only loop / adjusted compute".
- cited: GPT-f (Polu & Sutskever 2020, arXiv:2009.03393); PACT (Han et al. 2021, arXiv:2102.06203); miniF2F (Zheng et al. 2021, arXiv:2109.00110); INT generator (Wu et al. 2020); Subgoal search (Czechowski et al. 2021); TacticZero / HOList "learning to reason without imitation" (Bansal et al. 2019b); Firoiu et al. 2021 (synthetic first-order prover training).
- author: Stanislas Polu, Jesse Michael Han, Kunhao Zheng; follow-up HTPS (Lample et al. 2022) for online RL in Lean.
