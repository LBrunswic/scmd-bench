# wang2026learning — Learning to Repair Lean Proofs from Compiler Feedback

Yiran Wang (listed as "Evan Wang" in the KB metadata), Simon Chess, Daniel Lee, Siyuan Ge, Ajit Mallavarapu, Jarod Alper, Vasily Ilin (University of Washington)
Workshop paper (header: "VerifAI - ICLR 2025"); arXiv v2 13 Mar 2026 · arXiv:2602.02990 · `pdf/wang2026learning.pdf`

**Tier: T3** — The paper is a workshop paper, and its header venue ("ICLR 2025") is chronologically impossible: it cites Goedel-Prover-V2 (Aug 2025), Aristotle (Oct 2025) and Gemini 3 (accessed 2026-01-24). It is effectively a preprint with released data and models. The evaluation is a single run on one synthetic test set of 1,835 mutations drawn from 200 theorems, with no variance reported. The abstract's headline, that the 4B model beats the best open baseline, rests on a 0.6 pp margin. The prose and the table disagree on per-type maxima.
**Relevance: 3** — RQ1: this is the one paper in the set that treats Lean error messages plus goal state as a **supervised input**, rather than as a scalar reward. It includes a repair-trajectory SFT dataset and an ablation on NL explanations. RQ2: mutation-based synthetic failure generation, using the Lean REPL through LeanInteract.
**Read:** full text including appendices A–E.

## Summary
APRIL takes 39,492 proofs that compile under Lean 4.22.0-rc4 (from Herald, Lean Workbook and NuminaMath-Lean) and mutates them into 260,125 failing proofs. There are four mutation types: theorem substitution with LeanExplore neighbours (59.5%), same-class tactic swaps, one-line LLM re-completion, and multi-line LLM re-completion. The failing proofs are compiled through LeanInteract/REPL to record the error message and the local goal state. DeepSeek-V3 writes a natural-language explanation and fix suggestion for each, given the original proof and the mutation metadata. Qwen3-4B, Kimina-8B and Goedel-8B are LoRA-finetuned to map (error, goal state, failing proof) to (diagnosis, repaired proof). Single-shot repair accuracy, defined as the output compiling, rises from 1.1% to 27.4% for Qwen3-4B, against 26.8% for Goedel-Prover-V2-32B. Training for repair alone, without explanations, raises accuracy further, to 31.2%.

## Key points
- [V] The signal is the compiler output as input: training tuples pair "systematically generated proof failures with compiler diagnostics" (error message and local goal state at the failure location) with a repair target and an NL explanation (Abstract, §4.1).
- [V] Scale: 260,125 incorrect proofs from 39,492 compiled theorems (§4.1). Theorem substitution accounts for 59.5% of the failures (§4.1).
- [V] Environment: the source proofs are filtered to those that compile under Lean 4.22.0-rc4, and Lean-Interact is used to query the REPL for feedback and compile rates (§3.1).
- [V] Headline result: 27.4% single-shot repair for the finetuned Qwen3-4B, against 1.1% for the base model and 26.8% for Goedel-Prover-V2-32B. The authors warn it "should be interpreted as an ablation of compiler-feedback-conditioned repair rather than end-to-end proving performance" (§1).
- [V] Finetuned 8B models reach "31–35% repair accuracy, outperforming the 32B Goedel baseline" (§5.1).
- [V] The success criterion is only "the model’s output compiles under Lean 4.22.0-rc4" (§5). The text does not say that the theorem statement is checked to be unchanged, or that `sorry` is rejected.
- [V] NL explanation supervision costs repair accuracy: "Specializing exclusively on repair increases pass@1 from 27.4% to 31.2%" (§5.3). The drop is also visible for Goedel-8B and Kimina-8B, at −2.1 and −5.0 pp on the full set (Table 3).
- [V] Explanations transfer: another model (DeepSeek) repairs at 4% with base-Qwen explanations and at 29% with the trained model's explanations (§5.3). The size of this demo is not given.
- [V] The motivating claim is quoted from Seed-Prover: iterative refinement with compiler feedback is "32-128x more efficient than pass@k" (§1). This is second-hand here.
- [V] The prose says tactic repair reaches "42.5%" at best and line repair "13.5%" at most (§5.2). Neither matches Table 2. Table 2's best tactic number is 41.7%, and Goedel-32B's base line-repair column is 28.5%. The caption mentions parenthesised per-type numbers, but a `pdftotext -layout` check shows none are printed in Table 2.
- [P] In Table 2, the base Goedel-Prover-V2-32B beats every finetuned model on the Line (28.5% vs ≤18.5%) and Multi-Line (32.6% vs ≤20.8%) columns. The finetuning gain is concentrated on the tactic and theorem mutations, which are synthetic and local. Finetuning even lowers Goedel-8B's line-repair score, from 20.0% to 18.5%. This is my reading of Table 2, with the column order confirmed through `pdftotext -layout`; the paper does not discuss it.
- [V] Negative result: a generate-then-repair pipeline did not produce repairs, because "Goedel-Prover typically rewrote the proof from scratch" (App. D).
- [V] Tactic-mutation prompts acknowledge that "The compiler error may only reflect the first encountered failure" (App. C.3). With up to 3 swapped tactics, the diagnostic under-describes the defect.

## Verified quotes
> "a dataset of 260,000 supervised tuples pairing systematically generated proof failures with compiler diagnostics"

> "we generate 260,125 incorrect proofs using four mutation operators"

> "In total, APRIL contains 39,492 unique compiled theorems"

> "Theorem substitution errors constitute the largest fraction of incorrect proofs (59.5%)"

> "retaining only those that compile under Lean 4.22.0-rc4"

> "To retrieve compiler feedback and compilation rates, we use Lean-Interact to interact with the Lean REPL"

> "27.4% correction accuracy in our single-shot repair evaluation (no search/iteration), compared to 1.1% for the base model and 26.8% for Goedel-Prover-V2-32B under the same protocol."

> "this comparison should be interpreted as an ablation of compiler-feedback-conditioned repair rather than end-to-end proving performance"

> "Finetuned 8B models reach 31–35% repair accuracy, outperforming the 32B Goedel baseline."

> "A repair is considered successful if the model’s output compiles under Lean 4.22.0-rc4."

> "We evaluate proof repair accuracy on a held-out test set of 1,835 erroneous proofs spanning all four mutation types."

> "Specializing exclusively on repair increases pass@1 from 27.4% to 31.2%."

> "DeepSeek succeeds with a rate of 4% when aided by base Qwen’s explanations and 29% when aided by the trained model’s explanations"

> "Recent work has also shown that iterative proof refinement using compiler feedback is 32-128x more efficient than pass@k"

> "Tactic mutations yield the highest repair rates, with top performance reaching 42.5%"

> "line mutations are the most challenging, with maximum accuracy of 13.5%"

> "41.7%"

> "28.5%"

> "32.6%"

> "-2.1%"

> "-5.0%"

> "18.5%"

> "20.8%"

> "20.0%"

> "Goedel-Prover typically rewrote the proof from scratch, substantially altering the proof structure and reasoning."

> "The compiler error may only reflect the first encountered failure."

## Methods and evidence
- Data / setting: Lean 4.22.0-rc4, queried through LeanInteract. The split is by original theorem, stratified by source and length, with theorem names anonymised to `lean_problem`. Train/val/test have 38,292 / 1,000 / 200 theorems and 249,027 / 9,263 / 1,835 erroneous proofs (App. A, Tables 4–5).
- Baselines: base Qwen3-4B-Instruct-2507, Kimina-Prover 1.7B/8B, and Goedel-Prover-V2 8B/32B, all under the same single-shot repair prompt.
- Evaluation: compile success of a single output. No seeds, no variance and no confidence intervals. The test set is synthetic mutations only; there is no real model-generated failure set and no end-to-end proving benchmark.
- Training: LoRA r=32, α=64, lr 1e-4, effective batch 8, max length 2048, up to 15k steps with early stopping. Run on L40S/H200.
- Artifacts: dataset at HF `uw-math-ai/APRIL`; models `uw-math-ai/gAPRIL-w-exp` and `gAPRIL-wo-exp`.

## Limitations and caveats
- **Abstract vs table:** "a finetuned 4B-parameter model outperforms the strongest open-source baseline" rests on 27.4% vs 26.8%. On n = 1,835 correlated items from only 200 theorems, with a single run, that 0.6 pp gap is well within sampling noise. The binomial SE alone is about 1 pp, before clustering. The same baseline also beats all finetuned models on line and multi-line errors. ⇒ `claims_exceed_evidence=true`.
- The prose and the table disagree on the per-type maxima (42.5% and 13.5% vs Table 2). The parenthesised per-type-trained values the caption promises are absent from the table as printed, so the prose numbers cannot be traced to any table.
- The failures are synthetic mutations of correct proofs. The authors' own attempts to elicit "realistic" LLM errors failed (App. D). How well this transfers to a prover's own failure distribution is untested.
- The success criterion (it compiles) does not guard against statement edits or `sorry`, as far as the text says. Base-model scores near 0% suggest this was not exploited, but it is not ruled out.
- The venue header ("VerifAI - ICLR 2025") is inconsistent with the paper's own references. Treat it as unreviewed.
- Test theorems overlap in *source distribution* (Herald is mathlib4-derived) with the models' pretraining. Goedel/Kimina may have seen the originals.

## Contradictions and tensions
- [[xin2024deepseeka]] discards everything after the first error and resumes from the tactic state (truncate-and-resume). APRIL trains the model to *edit* the full failing proof, given the error text. The two are not compared. Kimina/Goedel-style models, per App. D, tend to re-prove from scratch rather than repair, which is consistent with DeepSeek's choice of discarding the suffix.
- [[kim2026process]] converts the same REPL output (first-error position) into scalar RL credit and throws away the message content. APRIL keeps the content as a supervised input. These are complementary uses of the same REPL output, and no paper in the KB yet combines them, e.g. RL on repair with error-conditioned prompts.
- [[santos2025kimina]]: the Kimina models are used here as repair baselines. The Kimina server is the same kind of REPL wrapper as LeanInteract, which is used for data generation here. No throughput is reported for generating 260k compiles.
- [[chen2025seeda]] (round 2): the "32-128x more efficient than pass@k" phrase does not appear in Seed-Prover v2. It is derivable only from one problem (IMO 2022 P2: light Pass@64–256 vs "can only be proved in Pass@8192"). No matched-budget table exists, so the motivating citation overstates its source.

## Open questions
- Does APRIL-style repair SFT improve end-to-end pass@k when the model is used inside an iterative refine loop, which is the claimed motivation? This is not measured.
- How does repair on the model's *own* failures compare with repair on synthetic mutations?
- What compile budget and wall time did data generation take? Mutation → compile → filter over hundreds of thousands of proofs is a sizeable verifier workload.

## Leads for next round
- term: proof repair; feedback-conditioned repair; error-centric supervision; mutation-based failure synthesis; iterative refinement vs pass@k; diagnostic-conditioned SFT.
- cited: Seed-Prover (Chen et al. 2025, arXiv:2507.23726), source of the "32-128x" refinement efficiency claim; Zhou et al. 2025, "Solving formal math problems by decomposition and iterative reflection" (arXiv:2507.15225, Delta Prover); Aristotle (Achim et al. 2025, arXiv:2510.01346); Break-It-Fix-It (Yasunaga & Liang 2021); DrRepair (Yasunaga & Liang 2020); TFix; DeepFix; SWE-RL self-play (Wei et al. 2025, arXiv:2512.18552); LeanExplore (arXiv:2506.11085); LeanInteract (Poiroux 2025); Goedel-Prover-V2 self-correction.
- dataset: `uw-math-ai/APRIL` (HF); Herald (ICLR 2025); NuminaMath-Lean.
- author: Vasily Ilin, Jarod Alper (UW Math AI).
