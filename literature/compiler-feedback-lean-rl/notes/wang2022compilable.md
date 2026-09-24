# wang2022compilable — Compilable Neural Code Generation with Compiler Feedback

Xin Wang, Yasheng Wang, Yao Wan, Fei Mi, Yitong Li, Pingyi Zhou, Jin Liu, Hao Wu, Xin Jiang, Qun Liu
Findings of ACL 2022 · doi:10.18653/v1/2022.findings-acl.2 · arXiv:2203.05132 · `pdf/wang2022compilable.pdf`

**Tier: T3** — peer-reviewed (Findings of ACL 2022, per DOI), but the "compiler" is Python's `codeop` syntax check, no functional-correctness metric, single run with no variance, and the headline system selects among 5 beam candidates while baselines are scored top-1 with no compiler-filter baseline at matched budget.
**Relevance: 2** — RQ1 (binary compile-success reward via PPO + compile discriminator); an early, weak-signal precedent. Not Lean, not proofs.
**Read:** full text

## Summary
CompCoder fine-tunes CodeGPT-small-py (GPT-2 based) for Python code completion and text-to-code, then alternates (a) PPO with a ±1 reward from a "compiler" and a KL penalty to the SFT reference, and (b) joint training of the generator with a 2-layer MLP discriminator (on the `<EOS>` hidden state) that classifies its own beam candidates as compilable or not. At inference, it beam-searches top-5 and returns the candidate the discriminator scores most compilable. Compilation rate rises from 46.84 to 94.48 (completion of 25 tokens) and 70.3 to 96.2 (text-to-code), with edit similarity unchanged. "Compilable" here means passing `codeop`, i.e. a syntax check, and the authors concede compilability does not imply correctness.

## Key points
- [V] The signal is a binary compile/no-compile bit, used as reward r=+1/−1 in PPO2 with a KL penalty to the SFT model (§2 Eq. 1, §3.2 Eq. 3–4).
- [V] The "compiler" is Python's `codeop` module, i.e. a parse/syntax check. There is no type checking, execution or tests (§4.1).
- [V] Reward hacking is observed: whitespace-only outputs, or trivial completions after an already-compilable prefix, "fool the compiler". It is patched by a KL term and a minimum generation length, and by treating whitespace output as a bad case (§3.2, §4.4).
- [V] Code completion (25 tokens): CR 46.84 (CodeGPT) → 94.48 (CompCoder), a +47.64 point gain. Edit similarity 64.47 → 64.53 (Table 1, §5.1).
- [V] Text-to-code: CR 70.3 (CodeGPT) → 96.2, and +23.1 / +24.3 over PLBART / CodeT5 (Table 2, §5.2).
- [V] Gains over CodeGPT at 30/35/40/45 tokens are 49.66/47.68/46.64/33.36 points, so the benefit shrinks at the longest completions (§5.1, Fig. 4).
- [V] Ablation (Table 3): CodeGPT 46.84; the discriminator in training only 64.88; RL only 76.48; RL+Dtrain 83.14; Dtrain+Dtest 81.96; everything 94.48. Rerank-at-test (Dtest) adds about 11–17 points (§5.3).
- [P] The prose in §5.3 swaps the row labels ("RL (Row 2) and Dtrain (Row 3)") relative to Table 3 (row 2 = w/ Dtrain, row 3 = w/ RL). Table 3 is taken as authoritative here.
- [V] RL uses only 5% of training data per epoch, beam 5 for candidates, and candidates are refreshed every 5 epochs. Hardware: 2× V100 (§4.4).
- [V] The authors concede that compilation rate "cannot guarantee the correctness of generated code" (§7).

## Verified quotes
> "improving the success rate of compilation from 44.18 to 89.18 in code completion on average"

> "where the compiler feedback is a binary value (compilable or non-compilable)"

> "We define r(s, t) = 1.0 iff the code can be compiled by the program compiler and r(s, t) = −1.0 otherwise."

> "if the generator generates a string composed of whitespace characters, the compiler will consider it as a good case. In the code completion task, if the previous code snippet is compilable, the generator can fool the compiler easily."

> "adopt the codeop1 module to simulate the pro"

> "It obtains 94.48 scores on the Compilation Rate, which is 47.64 points higher than the closest competitor"

> "outperforms CodeGPT by 49.66, 47.68, 46.64, and 33.36 points in the setting of completing 30, 35, 40, and 45 tokens, respectively."

> "achieves 23.1 points and 24.3 points improvements when compared with PLBART and CodeT5 respectively."

> "(1) CodeGPT (2) w/ Dtrain (3) w/ RL (4) w/ RL+Dtrain (5) w/ Dtrain +Dtest (6) w/ RL+Dtrain +Dtest (Ours) 64.47 65.46 64.71 64.43 65.24 64.53 46.84 64.88 76.48 83.14 81.96 94.48"

> "First, both RL (Row 2) and Dtrain (Row 3) effectively increase the code Compilation Rate"

> "In each epoch, we only randomly select 5% training data for the stability of RL training (Stage 2)."

> "To generate candidates (at Stage 3), we set the beam size as 5 in beam search."

> "considering the compilation rate is not the whole story as it still cannot guarantee the correctness of generated code."

## Methods and evidence
- Data / setting: 50k compilable CodeSearchNet-Python methods of 64–96 tokens (45k train / 5k test), with the last 25–45 tokens masked. AdvTest text-to-code: about 41k pairs (40k/1k), code of 128–170 tokens. Python 3 only.
- Baselines: BiLSTM, 6-layer Transformer, GPT-2, CodeGPT, PLBART, CodeT5, all top-1 without compile filtering.
- Evaluation: Compilation Rate (via `codeop`) and Levenshtein edit similarity. No pass@k, no tests, single run, no variance or seeds.
- Artifacts: none stated in the text. The base is the public CodeGPT-small-py checkpoint.

## Limitations and caveats
- The signal is only syntactic validity (`codeop`). It carries no semantic or type-checking information, and the gain on a "compiler-feedback" metric is a gain on a parser.
- **No matched-compute baseline.** CompCoder's inference picks the best of 5 beam candidates with a learned discriminator. The obvious baseline is to run `codeop` on CodeGPT's 5 beams and return any that parse, and it is not reported. A parser is essentially free at test time, so the discriminator (Dtest) buys little over an oracle filter. The Dtest gain (Table 3: 64.88 → 81.96) is therefore not evidence for learned verification over a real verifier.
- Reward hacking (empty or whitespace outputs) is acknowledged. Mitigations are ad hoc (minimum length, KL).
- The abstract's "44.18 → 89.18 on average" appears only as a figure-derived average. It is consistent with the per-length gains quoted (mean ≈ 45 points), but only the 25-token row is tabulated. I do not set `claims_exceed_evidence`: the numbers match, but the headline's meaning is narrower than "compilable" suggests.
- The ablation prose mislabels rows (see Key points).
- Small models (GPT-2 small scale) and short snippets.

## Contradictions and tensions
- Unlike [[gehring2024rlef]], the reward here is a syntax bit rather than test pass. Gehring also adds a −0.2 "invalid code" penalty, which is a compile-validity shaping term of the same kind, but there it is auxiliary to the test reward.
- [[olausson2023self]] would object to the missing matched-budget comparison. None is done here: CompCoder's best-of-5 inference is compared against top-1 baselines.

## Open questions
- How much of the RL gain survives against compile-filtered best-of-k from the SFT model at the same k?
- Does optimizing a syntax-validity reward move functional correctness (pass@k) at all, or only surface validity?

## Leads for next round
- term: compilability reward; "fool the compiler" reward hacking; compilability discriminator; energy-based model with compilability constraints
- cited: Korbak et al. 2021 (energy-based model constrained to compilable sequences); Yasunaga & Liang 2020 (DrRepair, graph-based repair from compiler diagnostics); Yasunaga & Liang 2021 (Break-It-Fix-It); Kulal et al. 2019 (SPoC, compilation rate metric); Chen et al. 2021 SequenceR (67–97% of generated patches non-compilable)
- follow-ups to check: StepCoder (Dou et al. 2024, RL from compiler feedback), PPOCoder (Shojaee et al. 2023), CodeRL (Le et al. 2022), RLTF (Liu et al. 2023)
- author: Yao Wan; Qun Liu (Huawei Noah's Ark)
