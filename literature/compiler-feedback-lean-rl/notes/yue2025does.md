# yue2025does — Does Reinforcement Learning Really Incentivize Reasoning Capacity in LLMs Beyond the Base Model?

Yang Yue, Zhiqi Chen, Rui Lu, Andrew Zhao, Zhaokai Wang, Yang Yue, Shiji Song, Gao Huang (LeapLab, Tsinghua; SJTU)
NeurIPS 2025 (read: arXiv v5, 24 Nov 2025) · arXiv:2504.13837 · `pdf/yue2025does.pdf`

**Tier: T2** — Peer-reviewed at NeurIPS 2025. The archived text does not state the venue; it was confirmed from a proceedings.neurips.cc entry and a neurips.cc/virtual/2025 poster page found by web search on 2026-09-23. It is broad: 4 model families, 6 RL algorithms, and math, code and vision tasks, with an unbiased pass@k estimator and manual checks of CoT validity. It is held back from T1 because the headline rests largely on third-party RL checkpoints, uses single runs with no seeds or variance, and its own controlled table (Table 3) shows pass@256 differences of about 1 pp that sometimes favour RL (`claims_exceed_evidence`). **It contains no formal or Lean experiment.**
**Relevance: 3** — RQ1: this is the main adversarial evidence on what outcome-reward RL (RLVR) can buy. It sharpens pass@1 and does not enlarge, and can shrink, the set of problems solvable at large k. Code (unit-test reward) is one of the three domains. Lean/formal proof is not tested.
**Read:** full text (§1–7, App. A, C.5–C.8, Tables 2–6).

## Summary
The paper asks whether RL with verifiable rewards teaches models to solve problems the base model cannot, or only reweights paths the base model already samples. Its lens is pass@k at large k (up to 1024), computed with the Chen et al. unbiased estimator. Across Qwen2.5 7B/14B/32B, LLaMA-3.1-8B, Oat-Zero, DAPO, Code-R1, DeepCoder, Qwen2.5-VL and Magistral-Medium, RL models win at small k. Base models catch up and overtake as k reaches "the tens or hundreds". On AIME24 and MATH500 the RL-solvable set is almost a subset of the base-solvable set, and RL outputs have low perplexity under the base model. In a controlled VeRL re-implementation of six RL algorithms on Omni-MATH, all six behave similarly and stay more than 40 points below the base model's pass@256. Longer GRPO training raises pass@1 and lowers pass@256. Distillation from a stronger teacher (R1-Distill), by contrast, lifts the whole pass@k curve. The authors conclude that current RLVR mostly improves sampling efficiency. They point to exploration, curricula, process rewards and multi-turn agentic RL as ways past the bound.

## Key points
- [V] Headline: RLVR models beat their base at small k, while "base models achieve higher pass@k score when k is large". The boundary "often narrows as RLVR training progresses" (Abstract).
- [V] The crossover comes at moderate k: "as k increases to the tens or hundreds, base models consistently catch up and surpass RL-trained models" (Fig. 2 caption, math). Largest gap quoted: Minerva, 32B, base ahead by "approximately 9% at k = 128" (§3.1).
- [V] Code is covered, with the same trend. Code-R1-Zero-Qwen2.5-7B (12K LeetCode/TACO, 832 steps) and DeepCoder-14B show pass@k curves "highly consistent with those observed in mathematical benchmarks" on LiveCodeBench v5 (279 problems), HumanEval+ and MBPP+ (§3.2, Fig. 3–4). The code evidence is curves only. Numeric support is Table 6, where the base solves 23 of LiveCodeBench problems 400–450 and Code-R1 solves 20, one of them not solved by the base (count derived from Table 6 indices, [P]).
- [V] For code, the start model is an **instruct** model, not a pretrained base. Code, like vision, uses instruction-tuned starting points "due to the training instability and limited effectiveness of using a pure zero-RL setting" (§2.1). So the code result compares instruct with instruct+RL.
- [V] The authors argue that unit-test verifiers are the cleanest case for the pass@k lens: "Since passing all unit tests is nearly impossible to achieve by guesswork, pass@k provides a reliable measure" (§3.2). A Lean kernel verdict would be cleaner still, but it is not tested.
- [V] Coverage (Table 2): on AIME24 (k=1024), 13.3% of problems are solved only by the base model and 0.0% only by the RL model. On MATH500 (k=128) the figures are 3.6% and 1.0%. The rare RL-only MATH500 problems are all solved by the base at 1024 samples (App. C.7).
- [V] Controlled experiment (Qwen2.5-7B, Omni-MATH-Rule 2,000 train / 821 test, 6 algorithms, KL removed, lr 1e-6, 8 rollouts/prompt) (§4.3, Table 3). Pass@1 rises from 10.2 to 23.8–28.1 on the in-domain test. Pass@256 barely moves (base 69.1; RL 67.0–69.7), and on MATH500 **RL pass@256 is higher** than base in every algorithm (96.4–97.4 vs 96.2).
- [V] Training length is what narrows the boundary (Table 4). GRPO step 150 → 450: train pass@1 26.1 → 42.5, test pass@256 68.3 → 63.9 (base 69.1), MATH500 pass@256 97.2 → 95.4 (base 96.2).
- [V] More rollouts help a little: n = 32 gives higher pass@128 than n = 8, "but the RL-trained model is still eventually outperformed by the base model". A KL term (0.001) gives similar pass@1 "but with a much lower pass@128" (§4.4).
- [V] Entropy is only part of the story. Raising the RL model's temperature to match base entropy still leaves it below the base across pass@k (§4.5).
- [V] Distillation is different: R1-Distill-Qwen-7B's pass@k curve is "consistently and significantly above" the base model's (§4.2, Fig. 7).
- [V] Near-frontier check (Magistral-Medium vs Mistral-Medium-3, AIME24/25): about 7 and 8 more problems solved at k=1, with the gap narrowing as k grows. Here the result is "little or no improvement at higher k", not base overtaking (§4.6, Fig. 9).
- [P] Internal inconsistency: the prose gives ΔSE as "GRPO's 43.9 to RLOO's best 42.6" on the in-domain test. From Table 3 (base pass@256 69.1 minus RL pass@1) this computes to 44.0 for GRPO and 41.0 for RLOO. The ranking holds, but the numbers do not reproduce.
- [P] Authors' proposed remedies: exploration in program-level abstraction (AlphaEvolve), curriculum, process reward / fine-grained credit assignment, and multi-turn agentic RL with environment feedback (§5).

## Verified quotes
> "We observe that while RLVR-trained models outperform their base models at smaller values of k (e.g., k=1), base models achieve higher pass@k score when k is large."

> "we observe that the reasoning capability boundary of LLMs often narrows as RLVR training progresses"

> "When k is small, RL-trained models outperform their base versions. However, as k increases to the tens or hundreds, base models consistently catch up and surpass RL-trained models."

> "on the Minerva benchmark with a 32B-sized model, the base model outperforms the RL-trained model by approximately 9% at k = 128"

> "which trains zero-RL models on 12K LeetCode and TACO samples over 832 steps, based on Qwen2.5-7B-Instruct-1M"

> "assessed on LiveCodeBench v5, comprising 279 problems that span from August 2024 to January 2025"

> "the effects of RLVR on three code generation benchmarks exhibit trends that are highly consistent with those observed in mathematical benchmarks"

> "Since passing all unit tests is nearly impossible to achieve by guesswork, pass@k provides a reliable measure of a model’s reasoning boundary."

> "for coding and visual reasoning tasks, open-source work typically uses instruction-tuned models as starting points, primarily due to the training instability and limited effectiveness of using a pure zero-RL setting"

> "13.3% 3.6% ... 0.0% 1.0%"

> "Even in the rare type 3 cases (e.g., 1% or about 5 problems in MATH500), the base model is able to solve all of them when sampling 1024 times."

> "Table 6: Indices of solvable problems in LiveCodeBench (ranging from 400 to 450, starting from 0)."

> "into a training set (2,000 samples) and an in-domain test set (821 samples)"

> "we remove the KL term to avoid constraining model learning"

> "with a constant learning rate of 10−6 . For rollout, we employ a prompt batch size of 256 and generate 8 responses per prompt"

> "9.9 26.1 27.2 24.4 28.6 28.2 31.4 10.2 25.1 26.8 23.8 28.1 28.0 26.5"

> "67.2 66.3 65.8 65.5 66.4 67.7 66.1 69.1 68.3 69.2 67.5 69.2 69.7 67.0 96.2 97.2 97.2 96.6 97.4 96.8 96.4"

> "ranging from GRPO’s 43.9 to RLOO’s best 42.6 on the in-domain test set"

> "∆SE remains consistently above 40 points across different algorithms"

> "pass@1 on the training set consistently improves from 26.1 to 42.5"

> "67.2 66.3 65.3 64.3"

> "69.1 68.3 66.6 63.9"

> "96.2 97.2 96.0 95.4"

> "pass@k improves slightly over n = 8, but the RL-trained model is still eventually outperformed by the base model"

> "the KL-regularized model achieves similar pass@1 to GRPO without KL, but with a much lower pass@128"

> "although the RLVR model performs slightly better pass@k at higher temperatures compared to its own performance at T = 0.6, it still underperforms the base model across pass@k"

> "the pass@k curve of the distilled model is consistently and significantly above that of the base model"

> "at k = 1, the RLVR-enhanced model solves approximately 7 more prob ... lems on AIME24 and 8 more on AIME25 compared to its base version"

> "RLVR provides significant gains at low k, but little or no improvement at higher k"

> "Our key finding is that all reasoning paths in the RLVR model are already present in the base model."

## Methods and evidence
- Data / setting: math uses zero-RL from base checkpoints (SimpleRLZoo GRPO on GSM8K+MATH, Oat-Zero, DAPO). Code uses instruct→RL (Code-R1, DeepCoder). Vision uses EasyR1 GRPO on Geometry3K. The controlled experiments are the authors' own VeRL runs on Omni-MATH-Rule. Sampling: T=0.6, top-p 0.95, up to 16,384 tokens (32k for code).
- Baselines: the base / instruct model in each pair, with a distilled model as the contrast. Six RL algorithms.
- Evaluation: unbiased pass@k with n = largest k (128/256/1024). Manual CoT validity checks on the hardest solved GSM8K/AIME24 items. **No seeds or variance.** Most RL models are third-party releases, so training data differs per pair.
- Artifacts: project page (limit-of-RLVR.github.io). Uses public checkpoints.

## Limitations and caveats
- Authors concede that the most capable pipelines are proprietary, and that RL is evolving fast enough that newer methods may remove the bound (§7). They also leave open whether scaling RL compute changes the picture (§4.4, §4.6).
- **No formal / Lean / theorem-proving domain.** Plan row #5's question "does this hold for formal proof?" is not answered here. Transfer is by analogy: a Lean kernel is an even stricter binary verifier than unit tests, so the pass@k lens applies, but the effect size is unmeasured.
- The abstract says base models surpass RL "when k is large", and the intro says "consistently ... across all benchmarks and LLM families". The authors' own controlled Table 3 shows RL pass@256 ≥ base on MATH500 for all six algorithms, and ≥ base on Omni-MATH-Test for PPO, RLOO and Reinforce++. Narrowing appears with longer training (Table 4), not uniformly. Magistral shows convergence, not overtaking. Hence `claims_exceed_evidence`.
- Code evidence is thin in numbers. It rests on curves plus one 51-problem index table. The code start points are instruct models, so "base" there already includes SFT/RLHF.
- Pass@k at k=1024 is a coverage measure, not deployable accuracy. The paper says so (§2.2), but readers applying this to RL-for-provers should remember that verified pass@k with a real Lean checker *is* deployable (the checker is the selector). So coverage loss matters more for provers than for math QA.
- ΔSE numbers in prose do not reproduce from Table 3 (see Key points).

## Contradictions and tensions
- [[xin2024deepseeka]]: DeepSeek-Prover-V1.5 claims RL gives "a genuine enhancement of fundamental capabilities" that stays stable as the sample budget grows, based on +0.7 to +2.3 pp at pass@128 on Lean. That is a mild *tension*, not a contradiction. Yue's crossovers often occur between k ≈ 64 and 1024, DeepSeek's RL gain is small, and V1.5's RL starts from an SFT/expert-iteration model (like Yue's code setting). No KB source measures Lean pass@k above ~128 for RL vs its SFT start *without* tree search.
- [[lin2025goedela]] (round 2, Lean) **partly confirms in the formal domain**. Goedel-Prover-V2 reports that late SFT/RL raises pass@1 while pass@32 declines ("diversity collapse"), and it recovers pass@N by averaging weights with the base model. This is the only KB evidence of Yue's effect on a Lean prover. It is observed at N=32, not by a large-k crossover.
- [[gehring2024rlef]] **confirms** the pattern in execution-feedback code RL. Relative gains shrink from 1@3 to 10@100 (70B 27.5→40.1 vs 50.3→54.5), and the 8B single-turn score *drops* after RLEF. Gehring attributes this to reduced diversity, which is Yue's mechanism.
- [[olausson2023self]] is consistent: most "repair" gain is resampling diversity. If RL shrinks diversity, the value of i.i.d. sampling at large k falls with it.
- [[kim2026process]] is consistent. Its outcome-only GRPO re-run on DeepSeek-Prover-V1.5 "fails to yield any gains on ProofNet", and process reward adds only 0–1.4 pp on top. RLVR looks like a small-magnitude sharpener in the formal domain too, though neither paper measures pass@k at large k.
- [[le2022coderl]]: CodeRL reports RL gains that *grow* with k on APPS competition problems (Fig. 5, up to k = 200). This contradicts Yue's direction, but the settings differ: a 770M CodeT5, RL mixed with the CE loss (Lce + Lrl), and critic-weighted tokens. CodeRL's Fig. 5 has no numeric table.

## Open questions
- Does the pass@k crossover happen for Lean whole-proof RL (e.g., DeepSeek-Prover-V1.5-SFT vs -RL at k = 1024–6400 without RMaxTS)? What k is the crossover?
- Does the boundary result change under multi-turn RL with verifier feedback (RLEF-style, Leanabell-V2)? The authors name this as the fix, but it is not tested here.
- For a set-conditioned prover (BASE given), is "coverage" dominated by premise selection, which RL might sharpen without shrinking?

## Leads for next round
- term: "reasoning boundary", "sampling efficiency gap ΔSE", "pass@k-aware RL / pass@k training", "diversity collapse", "zero-RL".
- cited: Dang et al. 2025 "Assessing diversity collapse in reasoning" (OpenReview AMiKsHLjQh). Brown et al. 2024 "Large language monkeys" (arXiv 2407.21787). QuestA (arXiv 2507.13266, question augmentation to expand capacity). Liu et al. 2025b "Understanding R1-zero-like training" (2503.20783). Huang & Yang 2025 IMO verification-and-refinement (2507.15855).
- counter-evidence to search: "ProRL" / prolonged RL expands reasoning boundary (NVIDIA 2025), "RL squeezes, SFT expands", "pass@k as reward" / "Pass@k training". Any Lean-prover paper reporting RL vs SFT at pass@k ≥ 1024.
- author: Yang Yue, Gao Huang (Tsinghua LeapLab).
