# kim2026process — Process-Verified Reinforcement Learning for Theorem Proving via Lean

Minsu Kim, Se-Young Yun (KAIST AI)
ICLR 2026 (per the paper's own header "Published as a conference paper at ICLR 2026"; arXiv v1 18 Jun 2026) · arXiv:2606.20068 · `pdf/kim2026process.pdf`

**Tier: T2** — The paper declares itself an ICLR 2026 conference paper; the header was not checked against the proceedings. The method is concrete and ablated: token placement, first-error rule, baseline, d1/d2 values, timeout and return-based credit are each varied. Against that, the evaluation is small: 10k RL prompts, G=4, LoRA, 4×A6000, and one pass@32/64 setting. Gains over outcome-only GRPO are 0 to 1.4 pp, typically inside the reported std, and the number of seeds is not stated. No code link is given.
**Relevance: 3** — RQ1: the clearest experiment in the KB isolating *what granularity* of Lean signal is worth what: binary outcome vs tactic-level vs both. RQ3: verifier timeout as a training hyperparameter (5/10/15/30 s).
**Read:** full text including appendices B–J.

## Summary
The paper uses Lean as a *process* oracle during GRPO training rather than only as a pass/fail checker. Each sampled whole proof is parsed via the REPL into its tactic sequence. A tactic absent from Lean's error log counts as "locally sound". The first erroneous tactic, and every tactic after it (first-error propagation), is penalised. Each tactic gets a score: 1 if the whole proof passes, d1 = −0.05 for pre-error tactics of a failed proof, d2 = −0.1 for the error and everything after. The score minus the group mean outcome reward is added as an advantage **only to the first token of each tactic**, on top of the usual GRPO outcome advantage. On STP-Lean and DeepSeek-Prover-V1.5 (7B), outcome+tactic RL beats outcome-only GRPO in 7 of 8 benchmark/budget cells and ties in the eighth. The margins are small (≤1.4 pp).

## Key points
- [V] The Lean signal used: "(i) a global outcome signal and (ii) fine-grained tactic-level feedback via info trees and error logs" (§1). A tactic not in the error log "has been elaborated successfully and passed Lean’s internal rule-based verification" (§3.1).
- [V] First-error propagation: once a tactic errors, "we propagate this failure to all subsequent tactics" (§4.1). Removing this rule "significantly reduces performance" (§5.3, Table 4). In Table 4 the reduction is 59.2 → 58.2 at pass@64 on MiniF2F.
- [V] Credit placement: "we assign the tactic advantage only to the first token of each tactic" (§4.2). This beats all-tokens, last-token and entropy-selected placement (Table 3).
- [V] Main gains on STP-Lean over the untrained STP baseline: MiniF2F "+2.5%p (pass@64)", ProofNet "+1.4%p (pass@32)", "a negligible decrease" at ProofNet pass@64 (§5.2).
- [V] Against outcome-only GRPO, the comparison that isolates the tactic signal, STP-Lean MiniF2F pass@64 shows "+2.5%p over the baseline, compared to +1.2%p with GRPO" (§5.2). The net tactic-signal effect is therefore about 1.3 pp.
- [V] Outcome-only GRPO on the DeepSeek-Prover-V1.5 base: the authors report it "even underperforms relative to the supervised baseline" in some cases on ProofNet (§5.2).
- [V] Tactic-only (no outcome) training "provides dense feedback but lacks a global objective, resulting in premature convergence" (§5.3). Both signals are needed.
- [V] Verifier timeout is a real hyperparameter. A 5 s limit "gave the worst results", because even simple proofs exceeded it and "produced too few valid reward signals"; 15 s was best (§5.3, Fig. 3). Timeouts count as failures (App. B).
- [V] Setup: Lean 4.9.0-rc1 through a REPL; 10k STP prompts drawn from 3.26M proofs; G = 4; LoRA rank 64; 4×A6000 for about 21–23 h (§5.1, App. B).
- [V] The authors claim the tactic parsing adds negligible cost over outcome-only RL, because both already make REPL calls (§5.2).
- [V] The method approaches search baselines at single-shot budgets: "59.2% vs. 58.5% pass@64 on MiniF2F" against InternLM2.5-StepProver's 4×32×600 expansions (§5.2, Table 1). The authors footnote that the budgets are not comparable.
- [V] Documented failure mode: the scheme "only punishes the terminal failing step". Locally valid but strategically useless tactics (intro/have/simp before a doomed `omega`) receive no penalty beyond d1 (App. H).
- [V] Admitted limitations: there is no learned-PRM baseline, and d1/d2 are "somewhat sensitive across different models and datasets" (Limitations).
- [P] The paper does not discuss `sorry`/axiom handling. A `sorry` tactic elaborates with a warning rather than an error, so under the stated rule ("not in the error log" ⇒ locally sound) it would receive d1 rather than d2, unless the REPL wrapper treats sorries specially. Not addressed (inferred from §3.1; the word "sorry" does not appear in the text).

## Verified quotes
> "For each generated proof, Lean provides (i) a global outcome signal and (ii) fine-grained tactic-level feedback via info trees and error logs."

> "If a tactic does not appear in the error log, then it has been elaborated successfully and passed Lean’s internal rule-based verification"

> "Proof attempts are parsed into tactic sequences, and Lean’s elaboration marks both locally sound steps and the earliest failing step"

> "we propagate this failure to all subsequent tactics"

> "removing this rule significantly reduces performance"

> "we assign the tactic advantage only to the first token of each tactic"

> "our method improves MiniF2F performance up to +2.5%p (pass@64), and ProofNet performance by +1.4%p (pass@32), while showing a negligible decrease"

> "STP-Lean + Ours improves by +2.5%p over the baseline, compared to +1.2%p with GRPO"

> "and in some cases even underperforms relative to the supervised baseline"

> "tactic-only training provides dense feedback but lacks a global objective, resulting in premature convergence"

> "A 5s limit gave the worst results, since even relatively simple proofs often exceeded this window and produced too few valid reward signals."

> "with 15s giving the best overall balance"

> "Each proof attempt was given a maximum of 15 seconds for verification; longer runs were treated as failures"

> "We use Lean 4.9.0-rc1 for all experiments in the paper."

> "We trained on 10k samples randomly drawn from the STP dataset (3.26M proofs)."

> "we used G = 4 generations per prompt"

> "We fine-tuned the models with LoRA (rank 64, α = 64) using bf16 precision."

> "Training was conducted on 4 × NVIDIA A6000 GPUs, requiring approximately 21-23 hours."

> "We used tactic-level rewards d1 = −0.05 and d2 = −0.1 for the main experiment."

> "the additional sorting and scoring overhead is negligible"

> "59.2% vs. 58.5% pass@64 on MiniF2F"

> "58.2% ± 0.7"

> "our current scheme only punishes the terminal failing step"

> "which proved effective but somewhat sensitive across different models and datasets"

> "We did not compare against learned PRMs"

> "since the vanilla model produced low-quality proofs during RL training"

## Methods and evidence
- Data / setting: RL prompts are 10k random STP samples. DeepSeek-Prover-V1.5-SFT first gets 500k STP samples of additional SFT, because the vanilla model "produced low-quality proofs during RL training". Non-CoT prompts. Max response 1,024 tokens. Temperature 0.9 in training, 1.0 with top-p 0.95 in evaluation.
- Baselines: untrained STP-Lean / DS-V1.5+STP; outcome-only GRPO under identical settings; tactic-only; ablations of the reward rule; return-based advantage (App. G). Search baselines (InternLM, RMaxTS) are quoted from their papers.
- Evaluation: pass@32 and pass@64 on MiniF2F-test and ProofNet-test, as mean ± std. The number of evaluation runs or seeds is not stated, and results come from the final checkpoint only. Baselines were re-evaluated under the same non-CoT protocol.
- Artifacts: none linked. Built on HF `trl`.

## Limitations and caveats
- Effect sizes are small relative to the noise. Against outcome-only GRPO, the differences are +1.4/+1.3/+1.2/0.0 pp on STP and +1.0/+0.4/+0.8/+0.9 pp on DS-V1.5 (Table 2), with stds of 0.3–1.0. Training-seed variance is not reported. The abstract's "outperforms outcome-only baselines in most settings" is accurate as worded. The intro's "consistently improves" is somewhat stronger than the evidence. Not flagged as `claims_exceed_evidence` because the abstract itself hedges.
- The setup is small: G = 4 is a tiny GRPO group, LoRA only, 10k prompts, a single dataset, and only 7B models of one lineage (DeepSeek-Prover-V1.5 and STP, which is built on it).
- Local soundness is not progress (App. H). The d1 penalty is the same for a useful lemma and for a useless `have`.
- The rewards are not potential-based in any guaranteed sense. App. J states explicitly that there is no optimality-preservation claim.
- `sorry`/axiom handling and reward hacking are not discussed.
- The timeout ablation confounds verification cost with a length prior: shorter timeouts bias training toward short proofs, which the authors themselves note.

## Contradictions and tensions
- [[xin2024deepseeka]]: DeepSeek reports RLPAF (binary GRPO) as a stable, general gain. Here, outcome-only GRPO on the same base model gives no ProofNet gain and sometimes regresses. The settings differ a lot (G=4 LoRA with 15 s timeout here, against G=32 full fine-tuning), so this is weak counter-evidence. It is still the only independent re-run of binary-reward GRPO on that model in the KB.
- [[xin2024deepseeka]] names a "partial-proof critic" performing temporal credit assignment as future work. This paper replaces the learned critic with the verifier's own first-error signal. Its failure case (App. H) shows why a learned value model may still be needed: local validity is not progress.
- [[wang2026learning]] uses the error *text* and goal state as model input for supervised repair. This paper discards the error content and keeps only its *position*, as a scalar credit. The two are complementary uses of the same REPL output.
- [[santos2025kimina]] / [[shen2026keep]]: the 15 s per-proof timeout here is wall-clock per REPL call. The paper gives no verifier throughput, so it cannot be compared with Kimina's server numbers.
- Round 2: [[vamshi2026reward]] / [[ammanamanchi2026faults]] show a worse case than sorry-as-warning: `apply?` on Lean < 4.20 creates a synthetic sorry with no warning at all; only `#print axioms` (sorryAx) catches it. [[wang2026longcat]] lists a macro expanding to `sorry` among cheats its RL policy used.
- [[ji2025leanabell]] (round 2): an independent Lean result in the same direction. AST-derived fine-grained rewards (tactic count, automation level, state change) add −1.2 to +0.8 pp over a binary compile reward (Table 6, single run), and the authors leave structured reward as unresolved.

## Open questions
- Does the tactic signal still help with long-CoT provers, or once G is large (e.g. 32 as in DeepSeek)? A small G is exactly where outcome-only advantages are most often zero.
- How are `sorry` and warnings scored? Can the policy learn to emit locally valid filler to raise its d1 share? The d1 < 0 choice partly guards against this, but it is untested.
- What does it cost in verifier calls relative to a learned PRM or a Monte-Carlo value estimate (e.g. VinePPO)?

## Leads for next round
- term: process-verified RL; first-error propagation; first-token credit assignment; symbolic process oracle; tactic-level MDP; potential-based reward shaping (Ng et al. 1999); RLVR.
- cited: Leanabell-Prover-V2 (Ji et al. 2025, arXiv:2507.08649), verifier-integrated RL; STP self-play prover (Dong & Ma 2025, arXiv:2502.00212); Goedel-Prover-V2 (arXiv:2508.03613), self-correction; Lu et al. 2024 "Process-driven autoformalization in Lean 4" (arXiv:2406.01940), origin of first-error propagation; VinePPO (Kazemnejad et al. 2024); PRIME implicit PRM (Cui et al. 2025); Prover Agent (Baba et al. 2025, arXiv:2506.19923); DAPO (Yu et al. 2025).
- cited (Lean-as-verifier during training): Wang et al. 2025a, Zhang et al. 2025, Ren et al. 2025 (DeepSeek-Prover-V2).
- author: Minsu Kim, Se-Young Yun (KAIST).
