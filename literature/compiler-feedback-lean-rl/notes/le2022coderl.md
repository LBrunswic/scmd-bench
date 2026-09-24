# le2022coderl — CodeRL: Mastering Code Generation through Pretrained Models and Deep Reinforcement Learning

Hung Le, Yue Wang, Akhilesh Deepak Gotmare, Silvio Savarese, Steven C.H. Hoi (Salesforce Research)
NeurIPS 2022 (read: arXiv v3, 3 Nov 2022) · arXiv:2207.01780 · `pdf/le2022coderl.pdf`

**Tier: T2** — Peer-reviewed at NeurIPS 2022. The archived text does not say so; it was confirmed from a proceedings.neurips.cc entry and the official GitHub README ("NeurIPS22") via web search on 2026-09-23. Code and models are released, and it is a standard execution-RL baseline (two round-1 notes chain to it). It is held back from T1 because the RL training's own contribution is small and single-run: CodeT5-770M APPS pass@1 goes 2.00 → 2.20 and *Intro drops* 6.60 → 6.20. Most of the headline comes from better pretraining and from inference-time critic sampling, which the abstract bundles as "CodeRL" (`claims_exceed_evidence`).
**Relevance: 2** — RQ1: the classic unit-test-reward actor-critic, with graded execution reward (compile < runtime < fail < pass), a learned critic as dense signal, and an error-conditioned repair model at inference. RQ2 (marginal): the critic is a *learned predictor of execution outcome*, reported at ">75%" 4-class accuracy.
**Read:** full text (§1–6, Tables 1–6, App. A); App. B–C skimmed.

## Summary
CodeRL fine-tunes a code LM (an improved CodeT5-large, 770M) on APPS with a policy-gradient loss added to cross-entropy. Each sampled program is compiled and run on unit tests. The return is −1.0 for compile error, −0.6 for runtime error, −0.3 for a failed test and +1.0 for passing all tests. The greedy decode's return is subtracted as a baseline. A separate smaller critic (CodeT5-small or GPT-2-small) is trained to classify the four test outcomes from (problem, program). Its token-level probability of the observed outcome weights each token's gradient, as a "dense" intermediate return. At inference, "Critic Sampling" runs example tests on N=200 samples. Passing programs are cut at the critic's highest-value prefix and resampled ("refine"). If none pass, the critic's top-M failing programs are sent with their error type/subtype to a seq2seq repair model trained on the RL samples. The result was SOTA on APPS: 2.69% pass@1, 6.81% pass@5, 20.98% pass@1000 and 8.48% 1@1000. It also gave 63.0% zero-shot pass@80 on MBPP.

## Key points
- [V] Graded execution reward: −1.0 compile error, −0.6 runtime error, −0.3 failed any test, +1.0 pass all (§3.3.1, Eq. 4–7). Variance is reduced with a greedy-decode baseline (§3.3.2).
- [V] The critic is a learned *execution-outcome predictor*. It is trained to predict one of {CompileError, RuntimeError, FailedTest, PassedTest}, and its token-level probabilities serve as intermediate returns (§3.3.3, Eq. 9–10). A GPT-2-small critic "can achieve over 75% error prediction accuracy on synthetic samples" (§5). No held-out calibration or per-class breakdown is given.
- [V] RL alone fails. With only Lrl "we note the problem of vanishing gradients during finetuning ... the final models actually deteriorate". Only Lce + Lrl works, on top of a 10-epoch CE warm start (§4.4, Table 3).
- [V] The RL training gain is small (CodeT5-770M, APPS, beam search) (Table 3). Warm-started model: pass@1 All 2.00, pass@5 All 2.90. After Lce+Lrl: 2.20 and 3.10. Introductory pass@1 *falls* from 6.60 to 6.20. Continuing CE alone overfits (All 1.50).
- [V] Return-estimate ablation: no baseline is worst; baseline plus learned critic is best (§4.4, Table 2). The table is mostly unreadable in the extracted text, so only the direction is used here, [P].
- [V] Inference-time Critic Sampling contributes more than RL training (Table 4). Pass@1000 All is 17.78 without CS, 19.36 with refine only, and 20.98 with refine + repair (M=1). Pass@200 goes 12.12 → 14.38. More repair candidates (M=2, 4) do not help pass@1000.
- [V] The CS budget is not matched. Refine and repair are "maximum one round", but each round regenerates N programs, "the same number of output programs N as in the first round" (§3.3.4, §4.1). Pass@k with CS therefore uses about 2× the generations of pass@k without it. The authors note that refining generates only partial programs (§3.3.4).
- [V] Pretraining explains a large share of the headline (Table 5, CE-only fine-tuning). Adding GCPY data moves pass@1 from 1.3 to 1.56. Adding the NTP objective moves pass@5 from 2.06 to 2.9.
- [V] Execution failure modes after RL: compile errors fall but runtime errors rise. "This leads to a higher probability that a CodeRL program contains runtime errors" (§4.6, Fig. 8).
- [V] Example tests are a weak, false-positive-prone proxy for hidden tests. The gap between them "limit[s] the positive impacts of our CodeRL generation procedure due to false positives" (§4.6).
- [V] The authors claim RL gains grow with k on competition-level problems, for both CodeT5 and GPT-J, up to k=200 without CS (§4.4, Fig. 5). Figure only, with no numeric table.
- [V] MBPP zero-shot: 63.0% pass@80 vs fine-tuned GPT-137B's 61.4%. Overlap check: "only 12.6% MBPP programs with > 50% lines duplicated in APPS training data" (§4.5).

## Verified quotes
> "-1.0 , if W s cannot be compiled (i.e. compile error)"

> "-0.6 s , if W cannot be executed with unit tests (i.e. runtime error)"

> "we use a greedy decoding strategy as a baseline and any generated samples that outperform this baseline are given positive return estimation, and negative return estimation otherwise"

> "The critic is trained to infer the unit test outcome; one of {CompileError, RuntimeError, FailedTest, PassedTest}"

> "a finetuned critic model initialized from a pretrained GPT-2 (small) can achieve over 75% error prediction accuracy on synthetic samples"

> "when we experiment with using only Lrl , we note the problem of vanishing gradients during finetuning"

> "Therefore, the final models actually deteriorate and lead to performance drops."

> "CodeT5-770M 6.60 1.03 0.30 2.00 8.80 1.67 0.70 2.90"

> "6.20 1.50 0.30 2.20 9.39 1.90 0.42 3.10"

> "4.60 0.93 0.10 1.50 7.00 1.37 0.20 2.26"

> "by using only Lce for further finetuning, despite improvement in losses during training time, the model performance indeed degrades during test time"

> "All 12.12 13.52 14.38 14.46 14.42"

> "All 17.78 19.36 20.98 20.92 20.62"

> "we found the best overall performance with M = 1 and performance starts to drop from M = 2 to M = 4"

> "In practice, we limit to maximum one round of repairing and/or refining only."

> "This results in the same number of output programs N as in the first round of generation."

> "we are only required to generate partial programs in the re-generation stage, making this stage less expensive than conventional generation"

> "employ nucleus sampling with a batch size of N = 200"

> "our approach achieved new SOTA results of 2.69% pass@1, 6.81% pass@5, and 20.98% pass@1000"

> "achieve SOTA results of 8.48% 1@k and 12.62% 5@k"

> "from 1.3 to 1.56 pass@1"

> "adding NTP pretraining task can improve the performance from 2.06 to 2.9 pass@5"

> "This leads to a higher probability that a CodeRL program contains runtime errors."

> "limit the positive impacts of our CodeRL generation procedure due to false positives"

> "as k increases, the performance gain of CodeRL is more significant on both GPT-J and CodeT5 models"

> "setting a new SOTA result of 63.0% pass@80 over GPT-137B’s 61.4% pass@80"

> "Only 12.6% MBPP programs have more than half of their lines matched somewhere in the APPS training data."

## Methods and evidence
- Data / setting: APPS (5,000 train / 5,000 test; ~21 unit tests per problem) and MBPP zero-shot. The actor is CodeT5-large 770M, pretrained 21 days on 16 A100s. The critic is CodeT5-small or GPT-2-small. The actor is frozen while the critic trains, then Lce + Lrl are applied with equal weights, one sample per step.
- Baselines: GPT-2/Neo/J, GPT-3 and Codex from Hendrycks et al. / Chen et al., plus AlphaCode n@k. Ablations over return estimates, loss combinations, CS components and pretraining variants.
- Evaluation: pass@k and n@k on hidden tests. Ablations use beam search pass@1/5. **Single runs, no variance.** Baselines are copied from prior papers, with different decoding and budgets.
- Artifacts: code and CodeT5-large checkpoints released (github.com/salesforce/CodeRL).

## Limitations and caveats
- Authors concede the extra cost of training a critic, but argue it is minor (§5). They also concede that example tests yield false positives.
- Not stated by the authors: the RL objective by itself moves overall pass@1 by +0.2 pp (2.00 → 2.20) and lowers Introductory pass@1. The abstract's SOTA claim attaches to the whole bundle (new pretraining + RL + critic sampling), and Tables 3–5 show that RL is the smallest of the three contributions.
- Critic Sampling pass@k is reported against baselines at the same nominal k while using about 2N generations (one extra round). That is an unmatched budget in exactly the sense [[olausson2023self]] criticises.
- The "dense" critic signal is an outcome classifier's per-token probability, not a verified process signal. Its accuracy (">75%" on 4 classes, on synthetic in-distribution samples) is the only quality figure.
- A 2022-scale model (770M, APPS pass@1 ≈ 2.7%). It is unclear whether the conclusions transfer to modern instruction-tuned LLMs.

## Contradictions and tensions
- [[gehring2024rlef]]: RLEF also uses execution feedback both as reward and as input for repair, but trains a *single* policy end-to-end with PPO over multi-turn episodes. CodeRL uses a separate SFT repair model and one fixed round. RLEF's ablation "single-turn RL plus a separate repair model" (14.8/12.6) underperforms full RLEF (17.2/16.0), which suggests CodeRL's decoupled design leaves gains on the table.
- [[olausson2023self]]: CodeRL's repair and refine are not budget-matched against i.i.d. sampling, so its CS gain (17.78 → 20.98 pass@1000) cannot be separated from the extra N samples. Olausson's matched-budget protocol is the needed control.
- [[wang2022compilable]] is the same era's syntax-only compiler reward. CodeRL's graded reward (compile −1 < runtime −0.6 < fail −0.3) is the richer version. CodeRL also records the flip side: fewer compile errors but more runtime errors after RL.
- [[yue2025does]]: CodeRL claims RL gains *grow* with k (Fig. 5), the opposite of Yue's large-k narrowing. The two are not directly comparable. CodeRL keeps Lce in the loss (anchoring diversity), goes only to k = 200, and gives no numbers. See the mirrored entry.
- [[jain2025r2e]]: both use a learned verifier (CodeRL's critic; R2E's execution-free verifier) and find it imperfect: >75% 4-class accuracy here, 71.82% binary accuracy there. Neither substitutes for execution. R2E combines the two for ranking, while CodeRL uses the critic to weight tokens and select repair candidates.

## Open questions
- Would a Lean analogue of the graded reward help (parse error < elaboration error < unsolved goals < kernel accept), or does [[kim2026process]]'s tactic-level signal already dominate it?
- How well does a small learned critic predict Lean outcomes (compile / error / sorry / accept) from proof text? CodeRL gives only a code number.

## Leads for next round
- term: "critic sampling", "graded execution reward", "error predictor critic", "program repair from error subtype".
- cited follow-ups (not in this paper, known successors to check): PPOCoder (Shojaee et al. 2023), RLTF (Liu et al. 2023, fine-grained unit-test feedback), StepCoder (Dou et al. 2024), "Fault-aware neural code rankers" (Inala et al., NeurIPS 2022, cited by jain2025r2e).
- cited: Bahdanau et al. 2016 actor-critic for sequence prediction. AlphaCode (Li et al. 2022) filtering by example tests.
- author: Hung Le, Steven Hoi (Salesforce).
