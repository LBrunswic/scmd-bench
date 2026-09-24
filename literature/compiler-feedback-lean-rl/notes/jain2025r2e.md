# jain2025r2e — R2E-Gym: Procedural Environments and Hybrid Verifiers for Scaling Open-Weights SWE Agents

Naman Jain, Jaskirat Singh, Manish Shetty, Liang Zheng, Koushik Sen, Ion Stoica (UC Berkeley; ANU)
arXiv v1 (9 Apr 2025, "Preprint. Under review."). COLM 2025 according to the authors' GitHub README; not checked against proceedings · arXiv:2504.07164 · `pdf/jain2025r2e.pdf`

**Tier: T3** — The archived v1 is a preprint. COLM 2025 acceptance comes only from the authors' own repository; the OpenReview page could not be read. Methods are concrete, environments, models and trajectories are released, and Table 3 reports ± spreads. The verifier analysis is a single sampling run on SWE-Bench-Verified with no variance. The execution-free verifier's "accuracy" is not defined against a named held-out set, and the kb metadata abstract (a later version: "8.7K", "AgentGym", "SYNGEN") does not match the archived v1 text ("8.1K", "R2E-Gym", "SWEGEN"). Upgrade to T2 once the COLM version is confirmed and read.
**Relevance: 2** — RQ2: how executable code environments are built procedurally (commit mining → dependency search in Docker → Fail→Pass tests → back-translated issue). It also gives the closest code-domain measurement of a *learned, execution-free verifier vs execution*. RQ1 only indirectly: training is SFT on trajectories, not RL.
**Read:** full text (§1–6, App. A–C).

## Summary
R2E-Gym builds 8,135 executable SWE tasks from Python repository commits rather than human-written issues. Commits are filtered by size heuristics plus an LLM judge. Each is installed in Docker via a semi-manual search over dependency pins. Fail→Pass tests are harvested or generated from the ground-truth patch, and an LLM back-translates the commit and failing-test output into a synthetic issue. A 4,578-task subset with no repository overlap with SWE-Bench is used to collect 3,321 successful Claude-3.5-Sonnet trajectories, which are used for SFT of Qwen2.5-Coder 7B/14B/32B (32B: 34.4% pass@1 on SWE-Bench-Verified). The second half studies test-time selection among 26 rollouts. It compares an execution-based verifier (a trained testing agent that writes reproduction tests, plus regression-test filtering) with an execution-free verifier (Qwen2.5-Coder-14B fine-tuned to answer YES/NO on the trajectory). Each plateaus near 43% Best@26, while the oracle Pass@26 is 64.4%. A hybrid (execution-free top-n filter, then test score) reaches 51.0%.

## Key points
- [V] Environment construction: a Docker-based, search-based dependency resolution that tries candidate configurations until one builds. The authors say it "is semi-manual and challenging to scale" (App. A). No build success rate, build time or image size is reported.
- [V] Scale: 8,135 tasks in total, 4,578 after SWE-Bench-repo decontamination, across 10 repositories. SWEGEN collects "over 2.5 times more problems" than issue-based collection, and "over 3 times" more executable environments than prior sets (§1–2, Table 1).
- [V] Synthetic issues match real ones for training: 27.8% pass@1 with synthetic vs 28.0% with real issues, at 400 trajectories each (§3).
- [V] SFT scaling (Table 3): 32B reaches 34.4 ± 1.2 on SWE-Bench-Verified vs 20.6 ± 2.1 for SWE-Gym data. The 14B saturates around 800 trajectories (§3).
- [V] Both verifiers plateau: execution-based and execution-free Best@K "converging similarly to 43.7% and 42.8% respectively", against Pass@26 = 64.4% (§4.2). Neither recovers even two-thirds of the oracle.
- [V] Execution-free verifier quality: 71.82% accuracy with patch + trajectory, 68.01% with patch only, 68.77% without thoughts. Best@26 is 42.8 / 37.6 / 41.4 (Fig. 7a). The learned verifier leans on the agent's own narrative ("Great! The fix works"), not the code. Attention analysis shows it attending to thoughts on an incorrect trajectory it scored YES (§4.2, Fig. 7b, 13).
- [V] Execution-based (generated-test) verifier failure modes (§4.2, Fig. 5–6, App. C.3). For most problems "less than 20% of tests provide discriminative signal". Many generated tests either do not reproduce the bug or fail the correct patch. Toxic tests (pass an incorrect patch, fail the correct one) reach "up to 10% of total tests" on some problems.
- [V] Hybrid (Eq. 2): keep the execution-free top-n, then add the test score. This gives 51.0% Best@26, "additional 7-8%" over either alone (§4.3). Ablations: regression tests alone reach 47.4%, Agentless tests instead of the trained test agent 48.8%, no top-n 49.8% (§4.4).
- [V] Compute allocation: 5 more test-agent rollouts (→49.3%) beat 5 more editing-agent rollouts (16→21: 47.6→48.4%). Test rollouts are also "considerably cheaper" (§4.4).
- [V] Execution-free verifier training: Qwen2.5-Coder-14B with LoRA rank 64, on 5,700 balanced trajectories (App. C.2). Agent execution limits: 90 s per action during data collection and a 10-min trajectory cap (App. B).
- [P] This is **not** a world model of execution. The "execution-free verifier" is an outcome reward model over the trajectory. It never predicts program state or test output. RQ2's "can a learned model substitute for running the environment?" is answered only in the weak sense of ranking. There it matches, but does not beat, *generated-test* execution (42.8 vs 43.7). Both sit far below the ground-truth hidden-test oracle (64.4). The two are complementary, not substitutes.
- [P] RL is not used. Training is pure SFT on Claude trajectories. Wei et al. (SWE-RL) is described as "reinforcement learning ... without execution feedback" (§5).

## Verified quotes
> "consisting of more than 8.1K tasks"

> "Figure 9: Repo distribution for our complete R2E-Gym dataset consisting of 8135 instances."

> "The resulting subset (R2E-GymSubset) consists of 4578 executable environments across 10 repositories"

> "we collect 3321 trajectories from 2048 unique task environments"

> "we can collect over 2.5 times more problems than relying on the data collection relying on G IT H UB issues"

> "increasing the number of executable environments by over 3 times"

> "We use a Docker-based approach with a search-based dependency resolution strategy to create reproducible environments for each commit."

> "This process is semi-manual and challenging to scale and we aim to rely more on LLM S in the future."

> "models trained on synthetic data achieve nearly identical performance (27.8% PASS @1) to those trained on real data (28.0%)"

> "20.6 (±2.1) 34.4 (±1.2) +13.8"

> "the 14B model begins to saturate at approximately 800 samples"

> "These trajectories achieve PASS @26 =64.4%"

> "B EST @K rate quickly plateaus for both methods, converging similarly to 43.7% and 42.8% respectively"

> "Accuracy (%) Best@26 (%) 71.82 68.01 68.77 42.8 37.6 41.4"

> "the final B EST @26 drops from 42.8% to 37.6% when we remove the trajectory from the verifier input (i.e., only use the final patches)"

> "execution-free verifiers heavily rely on trajectory features, such as agent thoughts, to make predictions"

> "for the majority of problems, less than 20% of tests provide discriminative signal"

> "testing agents generate toxic tests (up to 10% of total tests) that can erroneously rank incorrect patches above correct ones"

> "yielding significant performance improvements (additional 7-8%); achieving a B EST @26 performance of 51% on the challenging SWEB ENCH -V ERIFIED benchmark"

> "While regression tests alone improve performance from 42.9% to 47.4%, using generated tests further enhances performance to 51.0%"

> "our agent-generated tests yield superior results (51.0% versus 48.8%)"

> "this selective application strategy improves performance from 49.8% to 51.0%"

> "increasing the number of editing-agent rollouts from 16 to 21 improves the B EST @K performance from 47.6% to 48.4%. In contrast, simply sampling 5 more test-rollouts can yield better gains (B EST @K 49.3%)."

> "Note that test-agent rollouts are also usually considerably cheaper than editing-agent rollouts."

> "we perform LORA finetuning using a rank of 64"

> "The overall dataset consists of 5700 total trajectories including both positive and negative samples."

> "we also use a maximum timeout of 10-min for the overall trajectory and 90 seconds for each action execution"

> "Wei et al. (2025) explores reinforcement learning on large scale data collected from real-world G IT H UB issues without execution feedback."

## Methods and evidence
- Data / setting: Python repos found via SEART GitHub search. Tasks are Docker images per commit. The agent is an OpenHands-based ReAct scaffold with bash, editor and search tools.
- Baselines: SWE-Gym data at the same base model and size (Table 3). Agentless tests. Published open and proprietary systems (Table 4, copied numbers).
- Evaluation: SWE-Bench-Verified / Lite pass@1 with ± (Table 3). Verifier study: 26 rollouts (1 at T=0, 25 at T=0.8/0.9) and 7 test-agent samples, a single run. The execution-free "accuracy" split is not specified.
- Artifacts: environments, models and trajectories promised and released (R2E-Gym GitHub / HuggingFace).

## Limitations and caveats
- Authors concede that environment installation is semi-manual and hard to scale (App. A), and that context length is capped at 20K for compute reasons (App. B).
- Not stated: no environment-build cost, failure rate or per-execution latency. For RQ2/RQ3 this is the missing number, since you cannot tell what an environment-step costs.
- The "execution-based" verifier uses *model-generated* tests, not the hidden ground-truth tests. "Execution vs learned" here is really "learned tests executed" vs "learned judge", with ground truth only as the oracle Pass@K. The paper therefore does not measure how a learned judge compares to *real* verification. The oracle gap (64.4 vs ~43) is the closest proxy.
- The execution-free verifier's 71.82% accuracy has no stated evaluation split or base rate. Its training set was balanced by construction.
- Version drift: kb metadata abstract (later arXiv version) says "8.7K tasks", "AgentGym", "SYNGEN"; the archived v1 says 8.1K / R2E-Gym / SWEGEN. Prose "34.2% vs 30.4% in Table 3" (thoughts ablation) does not correspond to Table 3, which reports 34.4 for 32B.

## Contradictions and tensions
- [[team2025cwm]]: CWM builds >35k Docker repo images with an LLM setup agent and CI replay. R2E-Gym builds 8.1k with a semi-manual dependency search. The two are consistent that environment *construction* is the bottleneck, and CWM's automation addresses the scaling limit R2E-Gym concedes. Neither reports build cost per image.
- [[armengolestape2025what]] / [[team2025cwm]]: learned execution models reach high per-step accuracy but compound to 73–80% whole-program accuracy. R2E-Gym's learned outcome judge sits in the same band (71.82%) and is fooled by the agent's self-narration. Both lines of evidence say a learned model is a *filter*, not a substitute, for executing.
- [[le2022coderl]]: its learned critic predicts execution outcome at ">75%" (4-class, in-distribution). That is the same regime, and it is likewise used only to rank or select, never to replace the test run.
- [[yang2023leandojo]]: an environment-fidelity analogue. Toxic or non-reproducing generated tests (up to 10%) are the SWE counterpart of lean-gym's 21.1% misjudged proofs. Lean's kernel check avoids this *if* the ground-truth statement is fixed, which is an argument that Lean RL does not need R2E's hybrid machinery for correctness, only for ranking partial progress.

## Open questions
- Would a Lean execution-free judge (predict "kernel accepts" from proof text + goal) reach better than ~72% accuracy? Unlike SWE, Lean gives a cheap exact label for every sample, so the training data is unlimited.
- What does one R2E-Gym environment step cost (container start, test run), and how does it compare with a warm Lean REPL check (~0.27 req/s/core in round 1)?

## Leads for next round
- term: "execution-free verifier", "outcome-supervised reward model for agent trajectories", "test distinguishability", "toxic tests", "hybrid test-time scaling", "back-translation of commits".
- cited: SWE-Gym (Pan et al. 2024, arXiv 2412.21139), the trajectory-verifier origin. SWE-RL (Wei et al. 2025, arXiv 2502.18449). R2E (Jain et al., ICML 2024). CodeT (Chen et al. 2022, arXiv 2207.10397), dual execution agreement. "Fault-aware neural code rankers" (Inala et al., NeurIPS 2022). "The counterfeit conundrum" (Gu et al. 2024, arXiv 2402.19475), LLMs failing to judge code correctness.
- successor: DeepSWE (RL on R2E-Gym, 2025; repo has DEEPSWE_TTS_REPRODUCTION). It would supply the missing *RL-with-execution* result on these environments. SWE-smith.
- author: Naman Jain, Koushik Sen, Ion Stoica (Berkeley Sky Lab).
