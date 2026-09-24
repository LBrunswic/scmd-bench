# santos2025kimina — Kimina Lean Server: A High-Performance Lean Server for Large-Scale Verification

Marco Dos Santos, Hugues de Saxcé, Haiming Wang, Ran Wang, Mantas Bakšys, Mert Ünsal, Junqi Liu, Zhengying Liu, Jia Li (Project Numina / Cambridge / Moonshot AI)
NeurIPS 2025 Workshop (AI for Math) 2025 · arXiv:2504.21230 (v3, 16 Dec 2025) · `pdf/santos2025kimina.pdf`

**Tier: T3**: workshop paper with released code, and its throughput independently reproduced by [[xin2026axle]] (2.13 req/s on 8 vCPU, which matches its own ~0.31 proofs/s/core). Evaluation is thin: one dataset, one run, no variance, and one of the two baselines was configured without its session cache.
**Relevance: 3**: RQ3 (the reference Level-1 verifier: REPL pool plus header-keyed LRU import cache), RQ2 (Lean interaction tooling for RL).
**Read:** full text (4 pp. plus appendices A–C)

## Summary
Kimina Lean Server is a REST service wrapping the official Lean FRO REPL. It is the verifier used to train Kimina-Prover with RL. Two mechanisms produce the speed. (1) A pool of single-threaded REPL processes, one per core, with each request routed to an idle REPL. (2) An LRU cache keyed on the import header: each script is split into an import-only header H and a body B, and a request whose header matches a "warmed" REPL only elaborates B. On 9,419 NuminaMath-LEAN proofs (Lean v4.15.0, GCP C4, SMT off) it beats leanclient and LeanInteract at every core count. Caching halves wall time relative to a fresh REPL per proof. The Python client also parses infotrees into non-overlapping (goalsBefore, tactic, goalsAfter) triples for tree-search data.

## Key points
- [V] Headline: 1.5–2× faster than the next-best parallel tool (LeanInteract) on verification wall time (Abstract; Table 1). Recomputed from Table 1, the ratio is 2.05× at 8 cores, 2.10× at 16, 2.09× at 32 and 1.63× at 64. The advantage shrinks at the highest core count.
- [V] Absolute wall times for 9,419 proofs: 42:40 (8 cores), 21:48 (16), 11:33 (32), 7:56 (64) (Table 2).
- [V] Scaling from 8 to 32 cores is "nearly 4x". From 32 to 64 cores it is only 11:33 → 7:56 (~1.46×), so scaling is sub-linear past 32 cores (§3, Table 2). The paper does not comment on this.
- [V] Import caching: 15:28 → 7:56 at 64 cores, "0.099 seconds to 0.051 seconds, a 1.94x speedup" (§3, Table 3).
- [P] "Average Verification Time (s)" in Tables 2–3 is wall time ÷ number of proofs (476 s / 9,419 ≈ 0.0505 s). It measures inverse throughput, not per-proof latency. Implied per-proof core time is ≈ 0.051 × 64 ≈ 3.2 core-s with caching and ≈ 6.3 core-s without, so the import cost is ≈ 3 core-s per proof. This is derived; the paper does not state it.
- [V] Mechanism: pool of REPLs, one process each, routing to an idle REPL (§2.1). LRU cache keyed on the import header, which reuses a "warmed" worker so that only the body is verified (§2.1, Fig. 1). One persistent REPL per dedicated core, because "A single Lean REPL process is single-threaded" (§3).
- [P] Memory per REPL is a configurable knob (`LEAN_SERVER_MAX_REPL_MEM`), but no value or per-process footprint is reported (App. B.3). No cache hit rate is reported. In the benchmark every proof shares `import Mathlib`, so the hit rate is effectively 100% by construction.
- [P] The LeanInteract baseline ran with one AutoLeanServer per process and **without** `add_to_session_cache=True` (App. B.3). The paper argues that pooling is exactly the engineering Kimina contributes. It still means the baseline did not use LeanInteract's own reuse mechanism.
- [P] Used as the verification engine for Kimina-Prover RL training (§3). No RL-side throughput, cluster size or request volume is given.
- [P] The infotree-based extractor supports `have`/`let`/`calc`/`conv`, which the REPL's tactic mode does not always support (§2.2, App. A).

## Verified quotes
> "achieving a 1.5 to 2 times speedup in verification time"

> "leanclient LeanInteract Kimina Lean Server 109:55 87:35 42:40 56:58 45:51 21:48 30:16 24:11 11:33 18:01 12:56 7:56"

> "Scaling from 8 to 32 cores reduces the total time from 42:40 to 11:33, a nearly 4x speedup."

> "8 16 32 64 42:40 21:48 11:33 7:56 0.272 0.139 0.074 0.051"

> "caching reduces the average verification time from 0.099 seconds to 0.051 seconds, a 1.94x speedup"

> "Cached Non-Cached 7:56 15:28 0.051 0.099"

> "The server maintains a pool of Lean REPLs, each running in its own process to ensure optimal CPU core usage."

> "The server then uses the header as a key in a Least Recently Used (LRU) cache to find a "warmed" worker that has already processed the same imports."

> "A single Lean REPL process is single-threaded, and its CPU usage does not exceed one core."

> "which contains 9,419 valid, sorry-free proofs"

> "The machine was configured with 72 vCPUs, 540 GB of RAM (7.5 GB per vCPU)"

> "We did not specify add_to_session_cache=True when calling run on a command because each proof gets its own AutoLeanServer"

> "We also increased the request timeout (LEAN_SERVER_MAX_WAIT) and memory-per-REPL (LEAN_SERVER_MAX_REPL_MEM)."

## Methods and evidence
- Data / setting: 9,419 sorry-free complete proofs from NuminaMath-LEAN (deduplicated; 26 sorry proofs and 3 non-compiling proofs removed). Lean v4.15.0. GCP C4, 72 vCPU, 540 GB RAM, SMT disabled, run locally.
- Baselines: leanclient (LSP-based), LeanInteract (a multi-REPL setup without session cache).
- Evaluation: a single run per configuration, with no variance or repeats. Everything is measured on valid proofs only, with no failing or timeout-heavy proofs, which is unlike RL rollouts. Wall time is the only metric; there are no latency percentiles.
- Artifacts: code at github.com/project-numina/kimina-lean-server; the client is on PyPI (`kimina_client`). Baseline scripts are in the supplement.

## Limitations and caveats
- Table 2's text says "full NuminaMath-LEAN dataset", yet the numbers are identical to Table 1's filtered 9,419-proof subset. This is probably an editorial slip.
- The benchmark contains only correct proofs. RL rollouts are mostly failing or timing-out candidates, and the paper does not report how REPL crashes, timeouts or state pollution affect throughput. [[xin2026axle]] raises state leakage in shared-process designs as a risk.
- The "1.5 to 2" headline is roughly supported (1.63–2.10×), but the lower end occurs at the highest core count, which suggests that the gap narrows with scale.
- The "average verification time" of 0.051 s can easily be misread as per-proof latency. [[xin2026axle]] measures Kimina's median latency at 0.75 s on a different dataset and Lean version.
- There is no memory figure per REPL process and no cache-hit or eviction statistics. The LRU is trivially saturated by a single-header workload.
- The v3 text describes only header-level (import) caching, not REPL environment pickling or proof-state reuse.

## Contradictions and tensions
- [[shen2026keep]] models Kimina as "Level 1" (import caching only). It claims import loading costs ≈60 s per branch and that Kimina's gain is at most ~5×. Kimina's own data implies the import cost is only ≈3 core-s per proof on server hardware: the non-cached run is just 1.94× slower. Shen's 60 s comes from an 8 GB laptop and a `lake build` baseline.
- [[xin2026axle]] independently reproduces the Kimina throughput class: 2.13 req/s against AXLE's 2.09 req/s, and raw Lean at 1.03 req/s, i.e. about 2× from import preloading. This is consistent with Kimina's 1.94×.

- [[xin2024deepseeka]] runs verification at "Level 0": a fresh sandboxed REPL per proof on thousands of CPU cores, with no header cache. On Kimina's own numbers, that throws away roughly a 2× throughput gain. [[kim2026process]] uses a 15 s per-attempt timeout at RL time, which puts a hard floor on how cold-start cost trades against reward density.
- [[wang2025kimina]] (round 2) attributes a "10× speedup in verification throughput" and "up to 100 iterations per second" on 64 cores / 512 GB to this same server, with no table or baseline. That is about 5× this paper's own measured cache gain (1.94×) and per-core rate. Treat 1.94× as the caching figure. Kimina Preview's RL used 640 CPU cores for 1000×8 rollouts per iteration.
- Round 2: Kimina Lean Server's sorry detection is not a sound RL reward on its own — [[vamshi2026reward]] (Kimina 2.0.0, Lean 4.15) finds 31–44% of DeepSeek-Prover-V2-7B PutnamBench successes depend on `sorryAx`; [[wang2026longcat]]'s Kimina-derived server was gamed during RL via editable formal context.

## Open questions
- What are the per-REPL RSS with Mathlib loaded and the maximum REPLs per GB? This is needed to size a pool on a 94 GB host.
- What throughput results on a realistic RL mix (mostly failing proofs and timeouts)?
- Does reusing a REPL across requests leak state (e.g. `set_option`, attributes) between proofs?

## Leads for next round
- term: header-keyed LRU REPL cache; "warmed" REPL; infotree tactic extraction; REPL environment pickling (`pickleTo`/`unpickleEnvFrom` in leanprover-community/repl, not mentioned here).
- cited: LeanInteract (Poiroux et al., 2025); leanclient (Dressler, 2025); Pantograph (Aniva et al., TACAS 2025); ProofWala (Thakur et al., arXiv:2502.04671); Kimina-Prover Preview (Wang et al., arXiv:2504.11354); Seed-Prover (arXiv:2507.23726).
- dataset: NuminaMath-LEAN (AI-MO/NuminaMath-LEAN).
- author: Marco Dos Santos, Haiming Wang (Project Numina).
