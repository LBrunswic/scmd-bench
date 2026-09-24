# gehring2024rlef — RLEF: Grounding Code LLMs in Execution Feedback with Reinforcement Learning

Jonas Gehring, Kunhao Zheng, Jade Copet, Vegard Mella, Quentin Carbonneaux, Taco Cohen, Gabriel Synnaeve (Meta FAIR)
ICML 2025 (PMLR 267:19034–19055; confirmed via proceedings.mlr.press/v267/gehring25a and icml.cc/virtual/2025/poster/45358, since the arXiv v2 text itself states no venue) · arXiv:2410.02089v2 · `pdf/gehring2024rlef.pdf`

**Tier: T2** — peer-reviewed at ICML 2025, with strong ablations (SFT, single-turn RL, a separate repair model, random feedback, no-feedback RL) and evaluation at matched sample budgets. Held back from T1 by single training runs with no across-seed variance, 288–2304 H100s (not practically reproducible), and small internal number inconsistencies between prose and tables in v2.
**Relevance: 3** — RQ1 core: multi-turn RL where execution feedback is both the reward and an in-context observation, evaluated at matched sample budget against independent sampling.
**Read:** full text incl. appendices A–C

## Summary
Code generation is framed as a multi-turn MDP. The model writes code, and the code is run on *public* tests. On failure, a textual feedback message (wrong output with expected/got values, the stack trace, a timeout, or out-of-memory) is appended and the model tries again, up to 3 turns. The episode reward is +1/−1 for passing public *and private* tests, with a −0.2 penalty for turns without valid code and a KL penalty (β=0.05). Training uses PPO with a turn-level value function and token-level policy. On CodeContests, Llama 3.1 70B goes from 27.5 to 40.1 1@3 solve rate on test, and 8B from 10.5 to 16.0. The central result for RQ1 is that at a fixed sample budget, base models (including GPT-4o) do *not* benefit from multi-turn feedback over independent sampling, and after RLEF they do. Random-feedback ablations show the model actually uses the feedback content.

## Key points
- [V] Reward: +1 if all tests pass at episode end, −1 if any fail, −0.2 for a turn with no valid code, minus a KL term. There is no discounting (γ=1) (§2.2).
- [V] Public tests give the in-context feedback and early stopping. Private tests give the reward, which guards against copying expected outputs (§2.1).
- [V] Budget accounting: every turn counts as one sample in n@k, so 1@3 is a single rollout of up to 3 responses. This matches independent sampling at the level of responses, not tokens or execution calls (§3.1).
- [V] CodeContests test 1@3: Llama 3.1 8B 10.5 → 16.0, 70B 27.5 → 40.1. Llama 3.0 8B 3.2 → 12.1 (Table 1).
- [V] 10@100 test: 70B 50.3 → 54.5, 8B 24.8 → 28.7. Relative gains shrink at larger budgets, which the authors attribute to reduced output diversity from RL (Kirk et al. 2024) (Table 1, §3.2).
- [V] Without RLEF, multi-turn ≈ or < single-turn at matched budget. gpt-4o is 25.3 single-turn vs 24.3 multi-turn on CodeContests test. After RLEF, 70B single-turn 30.3 vs multi-turn 40.1 (Table 2).
- [V] Where it does *not* help: after RLEF the 8B model's single-turn score *drops* on CodeContests (11.8 → 9.7) and MBPP+ (58.3 → 57.0). Increasing the turn limit to 10 gives no benefit at a fixed budget, and 5 turns is best (Table 2, §3.3).
- [V] Random execution feedback severely impairs error recovery and reduces pass@1. pass@10 barely moves, so part of the multi-turn gain is resampling diversity rather than targeted repair (Fig. 3–4a, §3.3).
- [V] Base Instruct models "frequently output the same code solution despite inline feedback", i.e. minimal edits (§3.3).
- [V] Ablations (8B, 1@3 valid/test): SFT on 313,639 mined successful trajectories 10.3/10.0 (no test-set gain), single-turn RL 10.2/10.9, single-turn RL plus a separate repair model 14.8/12.6, RL with feedback withheld from the prompt 12.2/10.9, token-level value function 13.1/13.7, full RLEF 17.2/16.0 (Table 3, App. B.3–B.5).
- [V] More feedback at inference (20 tests incl. private, up to 8 failures shown) is mixed: 8B test 16.0 → 14.4 (drop), 70B test 38.0 → 41.2 (App. B.2).
- [V] Compute: about 20 wall-clock hours on 288 H100s (8B) or 2304 H100s (70B), with asynchronous inference and training and importance-sampling correction in PPO. Execution uses the AlphaCode codebase, Python 3.10, and defaults of 1 GB / 10 s per test (App. A.1–A.2).
- [P] The authors position the work explicitly against [[olausson2023self]] and Kapoor et al. 2024: prompting-only self-repair loses to independent sampling, and RL training is what turns feedback into a net gain (§4).

## Verified quotes
> "to date, utilizing such feedback for code generation with LLMs has failed to yield substantial improvements when taking computational demands into account; indeed, obtaining samples independently often results in higher accuracy for a fixed inference budget"

> "In our multi-turn setup, each turn counts as a sample."

> "a scalar reward is provided corresponding to whether all public and private tests are passing. We do not use reward discounting (i.e., γ = 1)."

> "we found that a possible failure mode concerns the generation of invalid code in non-final responses, which we address by providing a small penalty for invalid responses."

> "−0.2, if at does not contain valid code"

> "1@3 1@3 1@3 1@3 1@3 1@3 4.1 12.5 8.9 17.2 25.9 37.5 3.2 12.1 10.5 16.0 27.5 40.1"

> "10@100 10@100 10@100 10@100 21.7 29.8 50.2 54.5 24.8 28.7 50.3 54.5"

> "The relative improvements over the initial models, while still significant, are reduced in the 10@100 setting as compared to the 1@3 setting."

> "Llama 3.1 8B Instruct + RLEF Llama 3.1 70B Instruct + RLEF 11.8 9.7 26.2 30.3 10.5 16.0 27.4 40.1 65.3 67.5 73.2 78.6 63.9 69.5 75.0 80.4 58.3 57.0 66.9 67.6 60.5 63.1 70.2 72.2 gpt-4o-2024-05-13 25.3 24.3 82.8 80.7 68.8 71.7"

> "when considering a fixed sample budget, base models rarely benefit from access to faulty solutions and execution feedback in the multi-turn code generation setup."

> "with the exception of the 8B model on CodeContests and MBPP+ where single-turn performance drops."

> "With random execution feedback, error recovery is severely impaired."

> "we observe that they frequently output the same code solution despite inline feedback pointing out errors."

> "In all cases, increasing the turn limit to 10 provides no benefits under a fixed sample budget."

> "the single-turn and repair model obtain 1@3 solve rates of 14.8 on the validation set and 12.6 on the test set"

> "For each problem in the training set we collect 100 multi-turn rollouts and obtain 313,639 successful trajectories."

> "Supervised fine-tuning improves Instruct model performance on the validation set only; we do not see improvements on the test set."

> "The resulting model, starting from Llama 3.1 8B Instruct, obtains a 1@3 solve rate of 12.2 on the validation and 10.9 on the test set"

> "we achieve a 1@3 solve rate of 13.1 on the validation and 13.7 on the test set"

> "the 8B RLEF model can improve from 17.2 to 18.1 on the valid set, whereas on the test set we see a drop from 16.0 to 14.4."

> "on the test set we obtain 41.2 compared to 38.0 with feedback limited to public tests."

> "a training run takes approx. 20 wall time hours. With the above parameters we use 288 (128 for traning, 160 for inference) and 2304 (1024 for training, 1280 for inference) GPUs for 8B and 70B models, respectively."

> "we use a 1GB memory limit and maximum wall clock time of 10 seconds per test case."

> "Notably, on the test set the 70B model beats AlphaCodium with GPT-4, the previous state-of-the-art, with a single rollout compared to 5 solutions from 100 samples (38.0 and 29)."

## Methods and evidence
- Data / setting: CodeContests train (13,328 problems minus 669 without tests), valid 117, test 165. Python 3 output. Transfer evaluated on HumanEval+ and MBPP+ (base tests give feedback, plus tests score).
- Baselines: the same model with no RL, single- vs multi-turn; few-shot; SFT on mined rollouts; single-turn RL; single-turn RL plus a separate repair model (CodeRL-style); literature numbers (AlphaCode, AlphaCodium, MapCoder, Code Llama 34B + PPO).
- Evaluation: n@k with the AlphaCode estimator over 200 rollouts (Table 1) or 20 rollouts (Table 2). Checkpoint selection on valid. **One training run per configuration, no across-seed variance.**
- Artifacts: prompts in App. C, base models public. No trained weights or code are mentioned in the text.

## Limitations and caveats
- Authors concede: single-solution tasks only, and the method needs test cases (public tests have a median of 1 per problem).
- Budget is matched in *responses*, not tokens: multi-turn prompts grow with history, so prefill cost per turn increases. Execution calls are not costed. This is the same simplification [[olausson2023self]] flags for its main-body metric.
- **Internal inconsistency (v2):** the prose and App. B.2 give 70B test 1@3 as 38.0, while Tables 1 and 3 give 40.1. B.4 gives the 8B Instruct baseline test as 10.2, while Table 1 gives 10.5. The headline "beats AlphaCodium ... (38.0 and 29)" thus uses a number that differs from the table. Both still beat 29, so the claim holds, but the numbers were not synchronized between versions. I set `claims_exceed_evidence=false`, because the abstract's "order of magnitude fewer samples" is supported by Table 1 (1@3 vs 5@100 / 10@1000), and record the inconsistency instead.
- The comparison against literature baselines mixes models (Llama 3.1 vs GPT-4 scaffolds), so part of the "SOTA" is the base model: the stock 70B already beats all prior results at 10@100.
- Part of the multi-turn gain is diversity rather than feedback use (pass@10 barely changes under random feedback).
- Compute (2304 H100s for 70B) puts replication out of reach for most groups.

## Contradictions and tensions
- [[olausson2023self]]: finds that prompted self-repair is often no better than i.i.d. sampling at matched budget. RLEF *agrees* for untrained models (Table 2: base models and gpt-4o do not gain from multi-turn) and claims RL training reverses it. This is a refinement, not a contradiction: the dissent applies to inference-only self-repair, and RLEF's positive result is conditional on RL training with ground-truth execution feedback.
- [[wang2022compilable]]: both use PPO with a KL penalty and a ±1 terminal reward, but Wang's reward is syntax-only while RLEF uses test pass, keeping compile-validity only as a −0.2 shaping term.
- [[ji2025leanabell]] (round 2), the Lean analogue of RLEF (verifier output inside the CoT, DAPO on the binary compile reward): it counts a 2-round rollout as one sample, so its gains over vanilla RL are *not* budget-matched. Its first-attempt accuracy (64.7) is below vanilla RL (65.5), and it has no random-feedback control. [[lin2025goedela]] does report that removing the Lean error text hurts revision (Fig. 7), which matches RLEF's random-feedback finding, but it abandoned true multi-turn RL as immature and used single-turn multi-task RL.
- [[yue2025does]] (round 2) *confirms* the shrinking-gain-at-large-budget pattern seen here (1@3 → 10@100, and the 8B single-turn drop). Yue attributes it to RLVR narrowing coverage rather than adding solvable problems. RLEF's multi-turn setting is the regime Yue names as a possible escape but does not test.

## Open questions
- Does the matched-budget advantage survive when budgets are measured in tokens (including growing multi-turn context) and verifier calls? For Lean, where each check is expensive, verifier calls may be the binding cost.
- The feedback is used for targeted repair only partly (random-feedback ablation). How much would a Lean error message (goal state, type mismatch) carry compared with a failing test I/O?
- Is the single-turn drop for 8B a capacity effect, or a sign of RL-induced diversity collapse?

## Leads for next round
- term: RLEF; iterative code synthesis; turn-level value function; n@k with each turn counted as a sample; random-feedback ablation; public/private test split as a reward-hacking guard
- cited: Kapoor et al. 2024 "AI Agents That Matter" (independent sampling beats Reflexion/LDB at equal cost); Kumar et al. 2024 SCoRe (arXiv:2409.12917, RL for self-correction without external feedback); Le et al. 2022 CodeRL (critic sampling); Liu et al. 2023a RLTF (TMLR); Xu et al. 2024 (PPO on Code Llama 34B, CodeContests); Dou et al. 2024 StepCoder (arXiv:2402.01391, RL from compiler feedback); Shojaee et al. 2023 PPOCoder; Yu et al. 2024 B-Coder; Zhou et al. 2024 ArCHer (hierarchical multi-turn RL); Kirk et al. 2024 (RLHF reduces diversity); Chen et al. 2024b Self-Debug (ICLR 2024)
- follow-ups to check: later multi-turn RL-with-verifier work in Lean (e.g. DeepSeek-Prover-V1.5 RLPAF / truncate-and-resume, Kimina-Prover, error-message-conditioned proof repair) as the Lean analogue
- author: Jonas Gehring, Gabriel Synnaeve, Taco Cohen (Meta FAIR CodeGen)
