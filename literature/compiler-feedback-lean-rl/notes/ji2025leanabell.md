# ji2025leanabell — Leanabell-Prover-V2: Verifier-integrated Reasoning for Formal Theorem Proving via Reinforcement Learning

Xingguang Ji, Yahui Liu, Qi Wang, Jingyuan Zhang, Yang Yue, Rui Shi, Chenxi Sun, Fuzheng Zhang, Guorui Zhou, Kun Gai (Klear Team, Kuaishou Technology)
arXiv preprint 2025 (v1, 11 Jul 2025; no venue found by web search on 2026-09-23) · arXiv:2507.08649 · `pdf/ji2025leanabell.pdf`

**Tier: T3** — An unreviewed preprint with code, data and models released. Methods are concrete: the cold-start construction, the DAPO hyperparameters and the reward ablation are all described. The evaluation is thin. The authors report no variance for their own models. Gains on the DeepSeek base (+1.0 at pass@32) fall inside the baseline's reported ±0.5 std. The comparison with "vanilla RL" and with the base models is not budget-matched, because the proposed method uses an extra verifier call and generation round that is still labelled pass@32/pass@128. In the paper's own Table 3, the verifier-integrated model evaluated without its feedback round (64.7) scores *below* vanilla RL (65.5, Table 2).
**Relevance: 3** — RQ1: Lean verifier feedback placed *inside* the reasoning trace during RL (the Lean analogue of [[gehring2024rlef]]), feedback-token masking, and a negative result for AST-derived fine-grained rewards.
**Read:** full text (§1–4, Tables 1–6, Fig. 5–6, App. A–D).

## Summary
The paper post-trains two existing 7B provers (Kimina-Prover-Preview-Distill-7B and DeepSeek-Prover-V2-7B) to call the Lean 4 verifier in the middle of a long CoT. The model writes a proof inside `<code>`. Lean output goes inside `<interpreter>` ("Compilation failed. Find an error at line 12 …"), and the model then revises. Cold-start SFT uses about 7K synthesized samples. Claude-3.7-Sonnet rewrites failed proofs given Lean errors, and each rewrite is re-verified. Verifier tokens are masked from the loss. RL is DAPO with a binary compile reward (plus a small format reward). The prompts are 3.8K / 1.7K autoformalized NuminaMath statements with pass@8 in [1/8, 1/2], at rollout size 24, and the model makes one feedback-driven revision per CoT during training. On miniF2F-test, Kimina-7B improves from 63.1 to 68.4 at pass@32 (and 67.2 to 70.4 at pass@128). DeepSeek-7B improves from 75.6 to 76.6 at pass@32 (and 76.2 to 78.2 at pass@128).

## Key points
- [V] Headline: +3.2% (Kimina-Distill-7B) and +2.0% (DeepSeek-Prover-V2-7B) at pass@128 on miniF2F-test. This matches Table 1 (67.2 → 70.4; 76.2 → 78.2) (Abstract, Table 1).
- [V] Budget labelling: Table 1's method "employs a rollout size of 1 for subsequent Lean 4 verifier calling iteration cycles". The proposed method's pass@k therefore includes up to k extra verifier calls and revision generations that the baselines do not get (Table 1 caption).
- [V] Ablation against vanilla RL (same algorithm and reward, no feedback in the trace) at "32": Kimina 63.1 → vanilla RL 65.5 → verifier-integrated RL 68.4; DeepSeek 75.6 → 75.6 → 76.6 (Table 2).
- [P] **The gain comes from the extra inference-time round, not from better first attempts.** Table 3's "32 (Vanilla)" row, which evaluates only the first `<code>` block of the verifier-integrated model, gives 64.7 (KM) and 75.4 (DS). Both are slightly *below* vanilla RL in Table 2 (65.5, 75.6). The 68.4 / 76.6 come from "32-1", i.e. 32 rollouts plus one feedback revision each. The paper runs no vanilla-RL model at pass@64. So the "improvement over vanilla RL" is unmatched in verifier calls and generations (derived from Tables 2–3).
- [V] Most of the benefit is in the first revision round. Kimina goes from 64.7 to 68.4 (+3.7), DeepSeek from 75.4 to 76.6 (+1.2). Going from 1 to 3 iterations adds 0.8 on Kimina and nothing on DeepSeek. Widening each round from 1 to 4 rollouts adds 0.4 (68.4 → 68.8) on Kimina and nothing on DeepSeek (§3.1, Table 3).
- [V] Fine-grained AST-based rewards (tactic count, automation level, state-change efficiency) do not help. Success/failure only gives 68.4. With tactic count it gives 69.2, with automation 68.0, with state change 67.2 (App. B, Table 6). The authors call the structured-reward direction unresolved.
- [V] Stability: loss is masked on verifier tokens in both SFT and RL. Sample-level loss (GRPO-style averaging) caused "training collapse problems" on these long, variable-length trajectories. Token-level loss (DAPO) did not (§2.3, App. C).
- [V] Strong bases gain little. DeepSeek-Prover-V2-7B's pass@k curve is flat in the 32–128 range. Vanilla RL gives it no gain. The authors attribute this to prior RL having "already substantially activated" the model, and to fewer active prompts after pass-rate filtering (§3.1, §4 Limitations).
- [V] Generalisation is mixed. ProofNet-test pass@128 is 18.2 vs 11.8 for Kimina, but 25.2 vs 25.4 for DeepSeek. On ProverBench, DeepSeek-based V2 scores lower overall (48.7 vs 50.8 at pass@128) but solves one more AIME problem (2/15 vs 1/15) (Tables 4–5).
- [V] RL scale: batch 128, rollout size 24, max 16K tokens, lr 1e-6. The prompt sets are 3.8K (KM) and 1.7K (DS) statements. The "verifier use rate" rises to near 1 early in training (§2.3, §3, Fig. 5). [P] No verifier timeout, Lean server design, CPU budget or throughput is given. The evaluation environment is Lean 4.9.0, "the same testing environment as the DeepSeek Prover series" (§3).
- [V] The authors name the motivating constraint: practical RL "rarely exceeds 8–32 rollouts due to computational constraints", while evaluation uses pass@32–1024 (§1).

## Verified quotes
> "Experiments show that Leanabell-Prover-V2 improves performance by 3.2% (pass@128) with Kimina-Prover-Preview-Distill-7B and 2.0% (pass@128) with DeepSeek-Prover-V2-7B on the MiniF2F test set."

> "Kimina-Prover-Preview-Distill-7B [30] 32 128 1024 63.1% 67.2% 70.8%"

> "Leanabell-Prover-V2-KM (Ours) 32 128 68.4% 70.4% Leanabell-Prover-V2-DS (Ours) 32 128 76.6% 78.2%"

> "DeepSeek-Prover-V2-7B (CoT) [20] 32 128 1024 75.6% ± 0.5% 76.2% 79.9% ± 0.3%"

> "Our proposed method employs a rollout size of 1 for subsequent Lean 4 verifier calling iteration cycles."

> "Kimina-Prover-Preview-Distill-7B (Wang et al., 2025) + Vanilla RL + Our RL 32 63.1% 65.5% 68.4% DeepSeek-Prover-V2-7B (Ren et al., 2025) + Vanilla RL + Our RL 32 75.6% 75.6% 76.6%"

> "Leanabell-Prover-V2-KM (Ours) 32 (Vanilla) 32-1 32-4 64.7% 68.4% 68.8% 68.8% - 69.2% -"

> "Leanabell-Prover-V2-DS (Ours) 32 (Vanilla) 32-1 32-4 75.4% 76.6% 76.6% 76.6% - 76.6% -"

> "“Vanilla” refers to evaluating the generated proof in the first <code></code> block in the long CoTs."

> "Leanabell-Prover-V2-KM improves from 64.7% to 68.4% (i.e., an increase of 3.7%), and LeanabellProver-V2-DS improves from 75.4% to 76.6% (i.e., an increase of 1.2%). When continuously increasing the iteration cycles from 1 to 3, we can also achieve an improvement by a margin of 0.8%."

> "when the rollout size is increased from 1 to 4 within an iteration cycle, we can achieve a slight improvement of 0.4% (i.e., 68.4% → 68.8%) with Leanabell-Prover-V2-KM. Similarly, we do not obtain improvements with LeanabellProver-V2-DS."

> "we discover that the vanilla RL method achieves no gain on DeepSeek-Prover-V2-7B"

> "Although we train the model to perform verifier feedbackbased reflection only once per long CoT during training"

> "+ Success/failure reward only w/ 𝜆 𝑡𝑐 = 1.0 w/ 𝜆 𝑎𝑡 = 1.0 w/ 𝜆 𝑠𝑐 = 1.0 Sample budgets MiniF2F-test 32 63.1% 68.4% 69.2% 68.0% 67.2%"

> "We find that when using 𝑅tactic count , we achieve slight gains, but the other two rewards (i.e., 𝑅automation and 𝑅state change ) both perform slightly worse than using the simple 𝑅failed and 𝑅success reward strategy."

> "As shown in Figure 11, we encounter training collapse problems with such a sample-level loss."

> "we mask the token sequences provided by the Lean 4 verifier in the four scenarios of the synthesized cold-start data"

> "Similar to the cold-start fine-tuning, we also mask the token sequences provied by the Lean 4 verifier for stable RL training."

> "The previous RL training has already substantially activated the model's problem-solving abilities, making it very challenging to achieve significant gains through an additional RL training."

> "for very strong base models (such as DeepSeek-Prover-V2-7B), our RL framework may suffer from limited active training prompts used during training"

> "Leanabell-Prover-V2-KM (Ours) 7B 32 128 13.4% 18.2%"

> "Kimina-Prover-Preview-Distill-7B [30] 7B 32 128 10.3% 11.8%"

> "Leanabell-Prover-V2-DS (Ours) 7B 32 128 23.7% 25.2%"

> "7B 32 128 23.0% ± 0.4% 25.4% ± 0.7%"

> "DeepSeek-Prover-V2-7B 7B 32 128 49.0% ± 0.3% 50.8% ± 0.5% 1/15 1/15 Leanabell-Prover-V2-KM (Ours) 7B 32 128 39.8% 42.9% 1/15 1/15 Leanabell-Prover-V2-DS (Ours) 7B 32 128 47.8% 48.7% 1/15 2/15"

> "this filtering process results in a curated training dataset of 3.8K valid formal statements"

> "this filtering process results in a curated training dataset of 1.7K valid formal statements"

> "maximum token length = 16K, batch size = 128, rollout size = 24, learning rate = 1e-6"

> "we select formal statements achieving pass rates in the range of 1/8 to 1/2 to constitute our training dataset"

> "after brief training, almost all problems utilize verifier validation"

> "All experimental results are conducted with Lean 4.9.0, using the same testing environment as the DeepSeek Prover series"

> "practical RL training rarely exceeds 8–32 rollouts due to computational constraints and training efficiency"

## Methods and evidence
- Data / setting: Lean 4.9.0. Cold start uses about 7K samples (2K+2K+2K+1K across four scenarios), with Claude-3.7-Sonnet as the corrector. RL prompts come from NuminaMath, autoformalized by Kimina-Autoformalizer-7B and filtered by pass@8.
- Baselines: the two base models, plus "vanilla RL" (same DAPO and reward, no verifier feedback in the trace). Other provers' numbers are quoted from their papers.
- Evaluation: miniF2F-test, ProofNet-test, ProverBench, at pass@32/128. There is no variance or seeds for the authors' own models, and no budget matching in verifier calls or tokens.
- Artifacts: code, data and models at github.com/Leanabell-LM/Leanabell-Prover-V2.

## Limitations and caveats
- Stated: diminishing returns on strong bases because few prompts remain active after filtering; multi-round feedback not helping on DeepSeek-7B; context grows by naive concatenation.
- Not stated: the proposed method gets one extra Lean call and generation per sample, but is compared at the same "pass@k". The first-attempt ("vanilla") accuracy of the verifier-integrated model is *lower* than vanilla RL. What RL added is the use of the second round, not better proofs. `claims_exceed_evidence` is set for this reason, even though the abstract's numbers match Table 1.
- The DeepSeek-base gains (+1.0 at 32, +2.0 at 128) have no variance reported, while the baseline's pass@32 std is ±0.5. ProverBench overall declines.
- There is no information on verifier infrastructure (timeout, parallelism, `sorry`/axiom checks).

## Contradictions and tensions
- [[gehring2024rlef]]: this is the Lean analogue (verifier output in context, RL on the outcome). It agrees that the extra feedback round is where the gain appears, and that untrained bases cannot use the feedback, which is why a cold start is needed. It is weaker on the key control: RLEF counts every turn as a sample (1@3), while Leanabell labels a 2-round rollout as one sample. Leanabell's result therefore does not show a matched-budget win.
- [[olausson2023self]]: consistent. Returns concentrate in the first repair. Widening the repair (1 → 4 rollouts) adds 0–0.4 pp, and more rounds add 0–0.8 pp.
- [[kim2026process]]: confirms from a different angle that denser, structure-derived reward adds little over binary outcome reward on Lean (Table 6: −1.2 to +0.8 pp, single run).
- [[lin2025goedela]]: both use a stored or inline Lean error as a revision prompt. Goedel reports that removing the error text hurts (Fig. 7). Leanabell has no equivalent ablation (e.g. random or empty feedback), so it cannot distinguish use of the error content from a free second sample.
- [[xin2024deepseeka]]: same difficulty filtering for sparse binary reward (pass rate 1/8–1/2 here). Leanabell adds that vanilla RL gives *zero* gain on the already-RL'd DeepSeek-Prover-V2-7B, which tempers claims that outcome RL keeps paying.

## Open questions
- At matched Lean calls (e.g. vanilla-RL pass@64 vs verifier-integrated 32-1), is there any gain?
- Does the model use the error content? A random-feedback control is missing.
- What is the RL-time Lean timeout and throughput, and how many verifier calls per training step (up to 128×24×2)?

## Leads for next round
- term: "verifier-integrated reasoning", "feedback token masking", "tool-integrated RL" (ReTool, Search-R1, ToolRL, OTC), "partial rollout", "active prompts".
- cited: Leanabell-Prover V1 (Zhang et al. 2025, arXiv:2504.06122); Kimina-Prover Preview (arXiv:2504.11354); DeepSeek-Prover-V2 (arXiv:2504.21801); ReTool (Feng et al. 2025, arXiv:2504.11536); OTC: optimal tool calls via RL (Wang et al. 2025, arXiv:2504.14870); DAPO (arXiv:2503.14476); self-play with execution feedback (Dong et al. 2024, arXiv:2406.13542).
- author: Klear Team (Kuaishou): Yahui Liu, Qi Wang.
