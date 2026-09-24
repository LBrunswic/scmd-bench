# wang2025kimina — Kimina-Prover Preview: Towards Large Formal Reasoning Models with Reinforcement Learning

Haiming Wang, Mert Unsal, Xiaohan Lin, ... Zhengying Liu, Jia Li (Numina & Kimi Team)
arXiv 2025 · arXiv:2504.11354 (v1, 15 Apr 2025) · `pdf/wang2025kimina.pdf`

**Tier: T3**: an industry technical-report preprint. It releases the distilled 1.5B/7B models and the autoformalizer, and its server is published separately ([[santos2025kimina]]). Later systems use Kimina-Prover as a baseline ([[chen2025seeda]] Table 3). Held down by `claims_exceed_evidence`. The "10× speedup" for the Lean server has no table and is contradicted by the server's own later benchmark (1.94×). The prose's scaling deltas do not match Table 1. The prior-SOTA figure in the prose differs from Table 1. There is a single run with no variance.
**Relevance: 3**: RQ1 (binary Lean reward RL at 1000×8 rollouts per iteration), RQ3 and plan rows #2/#3 (verifier cores during RL, server hardware, header-cached REPL pool).
**Read:** full text including appendices

## Summary
Kimina-Prover Preview is Qwen2.5-72B trained with the Kimi k1.5 RL pipeline to produce long "formal reasoning pattern" outputs, where informal reasoning is interleaved with Lean snippets that must mostly reappear in the final proof. A roughly 20K-example cold-start SFT set was synthesised with Claude 3.7 Sonnet. RL samples 1000 problems × 8 rollouts per iteration, uses a binary Lean-compile reward and a KL-regularised loss, and applies format filtering plus random discard of negative-gradient samples to prevent format collapse. Verification during RL uses the Numina Lean Server: a pool of Lean REPLs with LRU caching of environments keyed by import header. The paper claims 10× throughput and 100 it/s on 64 cores / 512 GB, and says only 640 CPU cores are needed for RL. The model reaches 80.74% miniF2F-test at pass@8192 and 52.94% at pass@1, with independently sampled attempts and **no** compiler-feedback refinement (listed as future work).

## Key points
- [V] Verifier mechanism: the Numina Lean Server, built on LeanREPL, with "LRU-based caching" that "reuses preloaded environments based on import headers", running multiple REPL processes in parallel (§3.1).
- [V] **Infra numbers (plan #3):** a claimed "10× speedup in verification throughput", "up to 100 iterations per second on machines equipped with 64 CPU cores and 512 GB RAM". During RL, verification "does not become a bottleneck, requiring only 640 CPU cores for training" (§3.1). No table, baseline, definition of "iteration", timeout or per-REPL memory is given.
- [P] Derived, not stated: 100 it/s ÷ 64 cores ≈ 1.56 it/s/core, which is about 5× the per-core proof throughput measured by [[santos2025kimina]] (≈0.31 proofs/s/core) and [[xin2026axle]] (≈0.27 req/s/core). The provisioning is 512 GB ÷ 64 cores = 8 GB RAM per core. That is an upper bound on the memory budgeted per warm REPL, not a measurement. With 1000 × 8 = 8,000 proofs per RL iteration at the claimed rate, a 64-core box would verify one iteration's rollouts in about 80 s. 640 cores is 10 such boxes.
- [P] **Plan #2:** the paper does not measure Mathlib import time. The 10× figure conflates header caching with multi-process parallelism, so it cannot be converted into an import cost. It is contradicted in magnitude by the same server's later measurement (1.94×, cached vs uncached, [[santos2025kimina]]).
- [V] RL setup: N = 1000 problems × k = 8 rollouts per iteration; binary reward (1 for a correct proof, 0 otherwise); constant learning rate 2 × 10−6; KL τ = 0.4 (§2.3).
- [V] Stabilisers: tactic blocks must cover ≥60% of the final Lean code, and negative-gradient samples are discarded with probability ω = 0.5 to counter "format collapse" (§2.3).
- [V] Evaluation uses independent sampling only: "each attempt sampled independently", 32K context, up to 8192 attempts (§3.1). Iterative refinement from Lean feedback is listed as **future work** (§4).
- [V] Results: pass@1 52.94%, pass@32 68.85%, pass@8192 80.74% on miniF2F-test (Table 1). This matches the abstract's 80.7%.
- [V] Internal inconsistency: the prose says 72B beats 7B by "+0.44%, +5.75%, and +7.87%". Table 1 gives 77.87 − 70.8 = 7.07 pp at 1024, not 7.87. At pass@1 the gain is 0.44 pp (52.94 vs 52.5), so the "clear performance scaling with model size" rests on high-budget numbers.
- [V] Internal inconsistency: the prose calls prior SOTA "BFS Prover ... (72.95%)", but Table 1 lists BFS-Prover at 70.8%.
- [V] Accuracy during RL rose "from 61.8% to nearly 69%" as outputs grew "from 2,500 to over 10,000 tokens", with volatile mid-training regressions (§3.2.4).
- [V] Reward-hacking guard: after RL, a judge model checks whether proofs "merely leveraged a mistake in the formalization". Negation-proving filters wrong statements from the 200k-problem set (App. C).
- [V] The autoformalizer reaches "90% one-shot compilation rate and 66% accuracy" (App. C.2). The gap is the fraction of statements that compile but are judged wrong, a direct source of mis-specified reward.

## Verified quotes
> "Each iteration begins by sampling a batch of N = 1000 problems from our established problem set. For each problem, the current policy generates k = 8 candidate solutions (rollouts)."

> "A binary reward signal is assigned: 1 for a completely correct proof and 0 otherwise."

> "the Numina Lean Server employs an LRU-based caching mechanism that reuses preloaded environments based on import headers, significantly reducing initialization overhead."

> "Furthermore, it supports extensive parallelization across multiple CPUs by managing multiple Lean REPL processes concurrently."

> "These innovations result in a 10× speedup in verification throughput, achieving up to 100 iterations per second on machines equipped with 64 CPU cores and 512 GB RAM."

> "verification does not become a bottleneck, requiring only 640 CPU cores for training."

> "This efficiency contrasts with previous language model-based theorem proving approaches, which typically require thousands of CPU cores to sustain real-time verification at scale"

> "Evaluations utilize a 32K token context length and sampling budgets up to 8192 attempts, with each attempt sampled independently."

> "With just pass@1, the model already achieves 52.94%, and with pass@32, it reaches 68.85%"

> "the 72B model outperforms the 7B version by +0.44%, +5.75%, and +7.87% at those respective sampling budgets."

> "significantly surpassing prior SotA achieved by BFS Prover (R. Xin et al. 2025) (72.95%)."

> "We maintain a constant learning rate of (2 × 10−6 ) and a fixed KL divergence coefficient τ = 0.4 (Equation 1)."

> "tactic blocks must collectively cover at least 60% of the Lean code included in the final Lean 4 solution."

> "we randomly discard samples with negative gradients (probability ω = 0.5)."

> "As the model learns to generate longer proofs—from 2,500 to over 10,000 tokens—its accuracy rises from 61.8% to nearly 69%."

> "enabling iterative refinement using Lean compiler feedback to fix errors efficiently"

> "we use a judge model to assess whether the proofs generated by the model are correct or if the model has merely leveraged a mistake in the formalization."

> "reaching 90% one-shot compilation rate and 66% accuracy."

> "yielding a balanced and high-quality problem set of 200k total problems."

> "to synthesize a mini-SFT dataset of around 20K examples"

## Methods and evidence
- Data / setting: 200k RL problems (~10k human-annotated, resampled 1:1 with ~100k autoformalized). miniF2F in the DeepSeek-Prover-V1.5 Lean 4 version, with 8 unsolvable statements corrected and 13-gram decontamination.
- Baselines: prior provers' numbers are copied at their own budgets (Table 1), and o3-mini / Gemini 2.5 Pro are evaluated at pass@32 (Table 2).
- Evaluation: pass@k with independent samples. There is a single training run and no variance. The infrastructure claims have no table.
- Artifacts: distilled 1.5B/7B weights, Kimina-Autoformalizer-7B, and the Numina/Kimina Lean Server (documented later in [[santos2025kimina]]).

## Limitations and caveats
- The authors acknowledge volatile RL (regressions at 50–150 iterations) and early format collapse.
- Not acknowledged: the server "10×" has no baseline definition. It is 5× the later measured caching speedup, and "iterations per second" is undefined (REPL commands? proofs?). The model-size scaling claim is weak at pass@1, and the 7.87 vs 7.07 arithmetic does not match. The prior-SOTA number in the prose (72.95%) is not the one in the table (70.8%). → `claims_exceed_evidence`.
- There is no timeout, memory-per-REPL figure, or verification latency distribution. None of the plan #3 quantities are measured.

## Contradictions and tensions
- [C: vs santos2025kimina] This paper claims a "10× speedup in verification throughput" from the header-caching + multi-REPL server. The same server's own benchmark measures cached vs uncached at 1.94×, and [[xin2026axle]] independently measures warm vs cold at ≈2×. The 10× almost certainly bundles parallelism with caching, against an unstated (probably serial or fresh-process) baseline. It should not be reused as the caching speedup.
- [[xin2026axle]] / [[santos2025kimina]]: the claimed 100 it/s on 64 cores (≈1.56/s/core) is ~5× their measured per-core proof rates. The unit is probably not "whole proofs of a realistic mix".
- [[shen2026keep]]: offers no third import-cost measurement, so the 60 s vs ≈3–5 s contradiction is not resolved by this paper.
- [[xin2024deepseeka]] ("thousands of CPU cores", fresh process per proof) vs 640 cores here. This is consistent with header reuse cutting verifier cores, but the rollout rates differ, so it is not a matched comparison.
- [[chen2025seeda]] adds the compiler-feedback refinement this paper lists as future work, and it cites Kimina-Prover as prior SOTA on miniF2F.

## Open questions
- What is an "iteration" in "100 iterations per second"? What is the baseline for the 10×?
- What are the per-REPL RSS, the REPL count per 64-core box, and the RL-time timeout?
- How much of the 1000 × 8 rollout time is verifier wall-clock vs generation? The paper only says verification "does not become a bottleneck".

## Leads for next round
- term: Numina Lean Server; LRU header cache; formal reasoning pattern; format collapse; negative-gradient discard; negation proving for statement filtering; post-RL judge for formalization exploits.
- cited: "Numina. Numina Lean Server: Technical Report. arXiv preprint forthcoming. 2025" (= [[santos2025kimina]]); Kimi k1.5 (Kimi-Team 2025) for the RL loss; BFS-Prover (R. Xin et al. 2025); Leanabell-Prover (arXiv:2504.06122); HunyuanProver; Kimina-Prover (full, non-preview) and Kimina-Prover-72B/8B follow-ups.
- author: Haiming Wang, Jia Li, Marco Dos Santos (server), Zhengying Liu.
