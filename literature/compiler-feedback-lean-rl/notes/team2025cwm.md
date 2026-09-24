# team2025cwm — CWM: An Open-Weights LLM for Research on Code Generation with World Models

Meta FAIR CodeGen Team (Copet, Carbonneaux, Cohen, Gehring, Kahn, Kossen, … Armengol-Estapé, … Synnaeve)
arXiv 2025 · arXiv:2510.02387 (v1, 30 Sep 2025) · `pdf/team2025cwm.pdf`

**Tier: T3**: an unreviewed technical report from a large industrial lab, with released weights (mid-train, SFT and RL checkpoints) and inference code but no training data. The data-ablation evidence is one 8B run per datamix with no variance. The "world model helps reasoning" claim rests on qualitative figures, and the one quantitative test shows trace prediction *below* natural-language reasoning. The text also misquotes its own Table 8.
**Relevance: 2**: RQ2 (building execution environments at scale: 35k Docker repo images, a 3M-trajectory ForagerAgent corpus, an execution service at "tens of thousands of snippets/s", and measured accuracy of a learned Python execution model). It does not bear on RQ3's Lean throughput. Lean appears only as mid-training data (LeanUniverse state-tactic-state triples).
**Read:** sections 1–4.2, 6.2, 7.1–7.4, 8–9, App. D, I; skimmed §5 RL recipes

## Summary
CWM is a 32B dense decoder: 8T tokens of pre-training, then 5T tokens of "code world model" mid-training at 131k context, then SFT and multi-task asynchronous RL. The world-modelling data has two sources. The first is Python execution traces: 120M+ traced functions with LLM/fuzzer inputs, CodeContests solutions, repository unit tests traced across historical commits, and natural-language rewrites of traces. Each trace is a sequence of local-variable-state/executed-line pairs. The second is ForagerAgent: 3M SWE-agent trajectories over mutate-fix and issue-fix tasks in 10.2k Docker images, trained on both agent and environment turns. The environments come from >35k "executable repository images", built either by an LLM agent (RepoAgent) or by replaying GitHub Actions CI locally with `act` (Activ). An 8B ablation shows that trace data lifts CruxEval-O from 44.6 to 73.9 but leaves SWE-bench Verified unchanged. ForagerAgent data adds 3.7 points of SBV pass@1. Learned trace prediction has >96% per-step state/action exact match and 87.7% CruxEval-O via full traces, which is below the 94.3% from natural-language reasoning.

## Key points
- [V] Environment construction: over 35k unique executable repository images, built by RepoAgent (an LLM agent) and Activ (GitHub Actions replayed via `act`, with a pytest fixture that `docker commit`s the build state) (§2.1, App. D).
- [V] Image building runs about 500 repositories in parallel on an internal sandboxing platform (App. D).
- [V] Execution service for RL: "tens of thousands of code snippets per second", asynchronous and containerised, returning stdout, stderr, exit codes and environment state as feedback (§6.2). No latency or hardware breakdown is given.
- [P] The RL environment API is `start` (initial state and observation) and `step` (a token action giving a transition, observation and reward). Workers update weights mid-trajectory, so trajectories may use mixed policy weights (§6.2, Fig. 15).
- [V] The function-level trace corpus has more than 120M traced Python functions. Globals and external side effects are ignored, and unchanged variables are elided with "..".
- [V] CodeContests tracing yields 262k generated solutions, of which 33k snippets and 70k traces remain after dropping traces with more than 10k line events or larger than 1 MB (§2.2).
- [V] Repository tracing covers more than 21k repo images and about 70k traced commits, with at most 4 successful commits per repo out of up to 40 attempted (§2.2).
- [V] ForagerAgent yields 3M trajectories from 10.2k images and 3.15k repos, split 55/45 between issue-fix and mutate-fix. Trajectories are *not* filtered on success, and loss is masked on 50% of observations (§2.3, Table 1).
- [V] Ablation (8B, 6T pre-training plus 1T mid-training, then SFT without RL): adding tracing data moves CruxEval-O 44.6 → 73.9 and CruxEval-I 45.8 → 51.5, and leaves SBV unchanged (18.6 → 18.4). Adding ForagerAgent raises SBV to 22.1 (+3.7) (Table 4, §7.1).
- [P] The same ablation reports NLLs. The pdftotext table layout is ambiguous, but the prose says PR data helps oracle-SBV NLL, while only ForagerAgent improves agentic-SBV NLL (Table 4).
- [V] Learned execution model accuracy (greedy): on CruxEval, valid trace format is 99.6%, state exact match 96.9% and action exact match 96.5%. On function-level validation data the figures are 100.0%, 96.4% and 98.0%. Output pass@1 is 88.0% on CruxEval and 94.4% on function-level data (Table 9).
- [V] CruxEval-O for CWM: full trace prediction 87.7% vs natural-language reasoning 94.3%. Single-step trace prediction (58.1%) is below direct few-shot prompting (66.6%) (Table 8). The prose instead says "94.0 %" and "88 %".
- [V] Trace prediction is cheaper in tokens: 497 on average vs 1164 for language reasoning (§7.3).
- [V] SWE-bench Verified: 53.9% without test-time scaling (mean of 4 runs) and 65.8% with best@16 test-time scaling. The latter uses model-generated tests *executed* to rank the candidate patches (§7.2).
- [V] Termination prediction on HaltEval-prelim (115 terminating + 115 non-terminating programs) reaches about 0.94 pass@1 with reasoning. Qwen3-32B also reaches about 0.94, so this is not specific to CWM (Table 10, §7.4).
- [P] Lean appears only as mid-training data: LeanUniverse (initial state, tactic, resulting state) triples, described as "code world modeling in Lean", plus autoformalisation sets. No Lean evaluation is reported (App. I).
- [P] Conceded: world-model data covers only explicit Python execution, and robust ways to exploit it downstream remain open research (§8).

## Verified quotes
> "Running both RepoAgent and Activ methods in parallel, we created over 35 k unique executable repository images."

> "Therefore, we also developed the Activ (Act in virtual) pipeline to repurpose GitHub Actions CI execution for building executable repository images."

> "To achieve the scale required for our dataset, we run on an internal sandboxing platform to execute approximately 500 repositories in parallel within secure, isolated virtual environments."

> "Our training pipeline leverages an internal code execution service to safely execute tens of thousands of code snippets per second, in parallel across multiple programming languages and asynchronously in isolated containerized environments."

> "The final dataset contains over 120 M traced Python functions."

> "we disregard global variables and external side effects"

> "Generations are filtered to ensure a balance of incorrect and correct submissions, leading to an overall count of 262 k."

> "leaving us with 33 k effective code snippets and 70 k traces."

> "Repository-level tracing. We also performed Python execution tracing for the unit tests of more than 21 k"

> "This process resulted in around 70 k execution-traced commits."

> "We gather 3 M trajectories from 10.2 k images and 3.15 k underlying repositories. The trajectories are split 55–45 between issue- and mutate-fix tasks."

> "we do not filter trajectories based on whether they succeed at bug or issue resolution"

> "although we stochastically mask loss for 50 % of observations as they exhibit limited diversity"

> "CruxEval-O↑ CruxEval-I↑ 45.4 44.6 73.9 44.1 45.8 51.5 74.5 54.8"

> "14.6 18.6 18.4 ... 0.29 22.1"

> "Further incorporating execution trace data significantly improves CruxEval-input and -output prediction but leaves all SBV-related metrics unaffected."

> "The ForagerAgent data is further able to improve SBV pass@1 scores by another 3.7 %"

> "Valid Trace Format State Exact Match Action Exact Match 99.6 96.9 96.5 100.0 96.4 98.0"

> "88.0 94.4"

> "Language w/ CoT Trace Full 83.3 94.3 87.3 87.7"

> "CWM achieves a best score of 94.0 % in natural language reasoning mode, while full trace prediction achieves 88 %."

> "using 1164 tokens on average compared to 497 tokens for full trace prediction"

> "Single-step trace prediction is not competitive with classic few-shot prompting for either CWM model."

> "rates of 65.8 % with test-time-scaling and 53.9 % without test-time scaling (averaged over 4 runs)"

> "We obtained a balanced dataset consisting of 115 terminating (T) and 115 non-terminating (NT) Python programs."

> "however under the reasoning setup, both models significantly improved, reaching comparable performance of ∼0.94 pass@1."

> "LeanUniverse (Aram H. Markosyan, 2024), a dataset of (initial proof state, tactic, resulting proof state) triples from Lean's mathematical library"

> "Our code world modeling dataset collection efforts focus on explicit Python execution, and expanding this set to include other programming languages or symbolic execution is left for future work."

## Methods and evidence
- Data / setting: the corpora are described above. CWM-specific data is 30% of the mid-training mix. RL covers SWE, competitive programming, math and agentic coding, with asynchronous GRPO variants.
- Baselines: open-weight models of similar size (Qwen3-32B, gpt-oss, Gemma-3) and leaderboard numbers for closed models. The world-model ablation is internal only, at 8B.
- Evaluation: CruxEval-O and -I, SBV NLLs and pass@1, Terminal-Bench, LiveCodeBench, math, and HaltEval-prelim (a new benchmark built by LLM translation). The ablation is a single run per datamix. SBV base is averaged over 4 runs. The world-model analysis uses validation splits of CruxEval and the in-house function data.
- Artifacts: weights for pretrain, SFT and final checkpoints under a non-commercial research licence, plus inference code (github.com/facebookresearch/cwm). No training data, tracer or image pipeline is released.

## Limitations and caveats
- Conceded: world-model data is Python-only, and the authors say research is needed to "consistently leverage" world-model benefits. The model is not meant as a chat assistant.
- The abstract says the report shows "early results of how reasoning can benefit from" step-by-step execution simulation. The only quantitative test (Table 8) has full trace prediction at 87.7% against 94.3% for natural-language reasoning, and the "benefit" is shown only qualitatively (Fig. 5, B.23–B.27). The 8B ablation also shows trace data does **not** move SWE-bench (18.6 → 18.4). → `claims_exceed_evidence=true`.
- The prose (94.0%, 88%) disagrees with Table 8 (94.3%, 87.7%), and Table 9 gives 88.0% greedy for trace mode.
- The ~96–98% exact-match figures are *per step* on in-distribution validation data with short CruxEval functions. Compounding error on long executions is not measured here; compare [[armengolestape2025what]].
- CruxEval gains from trace data are close to in-distribution (Python output prediction). The downstream transfer that matters (SBV) comes from ForagerAgent environment trajectories, not from the execution world model.
- The execution-service throughput ("tens of thousands per second") has no hardware, latency or container-count detail, so it cannot be reused quantitatively beyond order of magnitude.

## Contradictions and tensions
- vs [[armengolestape2025what]] (same group, precursor): both find execution-trace training greatly improves output prediction (CruxEval-O), and both find little or no transfer to downstream code generation. E.T.: "no conclusive improvements on downstream coding benchmarks". CWM 8B ablation: tracing leaves SBV unaffected. CWM's conclusion, that "world modeling data, Python execution traces, and executable Docker environments can be directly beneficial for downstream task performance", attributes to the bundle a gain that its own Table 4 attributes to ForagerAgent, not to traces.
- vs [[yang2023leandojo]]: CWM treats LeanUniverse (state, tactic, next-state) triples as "world modeling in Lean". That is exactly the LeanDojo/Pantograph extraction product, reused as next-state prediction data, but CWM reports no Lean evaluation, so its value is untested.
- [[jain2025r2e]] (round 2): R2E-Gym builds 8,135 Docker SWE environments by a *semi-manual* dependency search that it concedes is hard to scale. This is consistent with CWM's view that construction is the bottleneck, and CWM's LLM setup agent is the automated answer. Its learned execution-free verifier (71.82% accuracy) only complements executed tests (hybrid 51.0 vs ~43 each). It does not replace them.

## Open questions
- Does a learned Lean "next goal state" model (trained on LeanDojo/LeanUniverse triples) reach per-step exact match comparable to CWM's 96% on Python? Could it pre-filter candidate proofs before calling the real Lean checker in RL?
- Does world-model mid-training reduce RL sample complexity? The conclusion asserts it should, but no RL-with/without-world-model experiment is reported.
- What does the execution service's per-snippet latency distribution look like, and how would a Lean verifier fit that architecture?

## Leads for next round
- term: "code world model"; "neural code interpretation"; "executable repository images"; "Activ" / `act` GitHub Actions replay; "ForagerAgent"; mutate-fix / issue-fix; "neural debugger"; best@k with generated tests; HaltEval.
- cited: LeanUniverse (Markosyan, 2024), a Lean 4 dataset library; Armengol-Estapé et al. 2025 (E.T.); Zhang et al. (trace training); SWE-RL (Wei et al., 2025); SWE-Gym; R2E-Gym (hybrid verifiers, arXiv 2504.07164); Gehring et al. 2025 (RLEF, RL from execution feedback); PipelineRL (Piche et al.); Cummins et al. 2024 (LLM Compiler IR data); Goedel-Pset; Lean Workbook.
- follow-ups: any 2026 papers evaluating CWM checkpoints as world models, or building "Lean world models" (next-state prediction for tactic states).
- author: Gabriel Synnaeve; Jonas Gehring; Quentin Carbonneaux; Aram H. Markosyan (LeanUniverse); Taco Cohen.
