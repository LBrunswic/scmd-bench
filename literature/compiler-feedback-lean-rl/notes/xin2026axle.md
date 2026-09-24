# xin2026axle — AXLE: A Cloud Infrastructure for Lean 4 Theorem Proving Utilities

Jimmy Xin, Alex Schneidman, Chris Cummins, Karun Ram, Srihari Ganesh, Jannis Limperg (Axiom Math; Thinking Machines Lab; Recursive Superintelligence)
arXiv 2026 · arXiv:2606.26442 (v1, 24 Jun 2026) · `pdf/xin2026axle.pdf`

**Tier: T3**: an industry preprint with concrete, reproducible benchmarks on public data (Goedel-workbook Lean 4.27) against a named competitor (Kimina), where the competitor wins. It includes a public service and SDK, and a well-known Lean author (Limperg, Aesop). The authors operate the service, and the headline production claims (500M requests, Putnam 12/12) carry no evidence in the paper. There is one run with no variance, and the strict-checker comparison uses internal production data.
**Relevance: 3**: RQ3 (independent throughput measurement of Kimina versus raw Lean; the cost of strict verification), RQ1 (reward hacking via sorry, axioms or restated theorems), RQ2 (sandboxed multi-version verification service).
**Read:** full text including appendices A–D

## Summary
AXLE is Axiom Math's hosted, multi-tenant Lean 4 service with 14 metaprogramming tools: `check`, strict `verify_proof`, `extract_decls`, `merge`, `normalize`, `rename`, `repair_proofs`, `simplify_theorems`, `disprove`, `have2lemma`, `sorry2lemma` and others. Each request runs in its own sandboxed process (no network, no filesystem writes) against a pre-loaded environment chosen per request (Lean + Mathlib version). On 5,000 Goedel-workbook proofs at concurrency 8 on 8 vCPU, AXLE and Kimina are within 2% on throughput (2.09 vs 2.13 req/s). Raw per-request Lean is about 2× slower (1.03 req/s) because it reloads Mathlib every time. `verify_proof` is 10× faster than SafeVerify and 99× faster than Comparator at the median, because it skips environment replay. The price is that it accepts kernel-bypass attacks that a replay checker catches.

## Key points
- [V] Check throughput on 5,000 proofs at c=8 on an r7a.2xlarge (8 vCPU, 64 GiB): AXLE median 1.05 s, p90 5.96 s, 2.09 req/s. Kimina median 0.75 s, p90 6.38 s, 2.13 req/s. Raw Lean median 5.14 s, p90 9.81 s, 1.03 req/s. Verdicts are identical at 4708/287/5 (Table 2).
- [V] Raw Lean is "about 2× slower" because it "pays the full coldstart cost on each request of reloading MATHLIB modules"; both AXLE and Kimina keep Mathlib preloaded (§5.1). This independently corroborates Kimina's 1.94× cache speedup.
- [P] The AXLE–Kimina gap comes from per-request sandbox isolation: a sandboxed worker process per request versus dispatch into a warm REPL (§5.1). The paper does not describe exactly how AXLE keeps Mathlib preloaded under per-request process isolation (e.g. a fork of a warm parent or a shared mmap). The mechanism is unstated.
- [V] Concurrency scaling on 8 vCPU: 0.29 → 0.57 → 1.11 → 2.09 req/s for c = 1, 2, 4, 8 (7.27× at c=8). At c=16 there is no throughput gain and the median latency rises to 4.68 s (Table 5). Throughput is ≈0.26–0.29 req/s per core.
- [V] Strict verification on 1,000 production requests (r7a.4xlarge, c=4, 600 s budget): verify_proof median 0.97 s, 0.43 req/s. SafeVerify 10.1 s, 0.107 req/s. Comparator 95.7 s, 0.026 req/s, 93.8% success (Table 3).
- [P] The alternatives are slow because both reload imports per request and run an environment-replay step that re-typechecks declarations. verify_proof trusts the environment (§5.2).
- [V] Agreement: 100% with Comparator on 938 conclusive pairs; 99.30% with SafeVerify, where all 7 disagreements come from private-name mangling (Table 4, App. C.2).
- [V] Known soundness gap: `Environment.addDeclCore (doCheck := false)` injects `false : False`, which verify_proof accepts and a kernel-replay checker rejects (App. C.3).
- [P] RL reward-hacking surface: plain compilation accepts `sorry`, non-whitelisted axioms, restated or weakened theorems and `unsafe` declarations. verify_proof checks all four (§4.1, App. C.1). The paper cites a FormalQualBench case in which Codex/OpenCode built an axiom via string concatenation (App. C.1).
- [V] Production scale: over 500 million requests served, and used for Axiom's 12/12 on Putnam 2025 (Abstract). These claims are unevidenced in the paper.
- [P] No memory-per-worker figure, cache hit rate, or cluster-level throughput is reported.

## Verified quotes
> "It has served over 500 million requests to date and is the underlying infrastructure for Axiom Math's proving efforts, including its 12/12 score on the 2025 Putnam competition."

> "1.05 s 0.75 s 5.14 s 5.96 s 6.38 s 9.81 s 2.09 req/s 2.13 req/s 1.03 req/s 2389 s 2351 s 4873 s"

> "raw LEAN is about 2× slower than the other two: it pays the full coldstart cost on each request of reloading MATHLIB modules, which dominates when the median proof needs less than a second of actual elaboration"

> "Kimina is marginally faster (0.75 s vs. 1.05 s latency, 2.13 req/s vs. 2.09 req/s throughput). This gap comes from AXLE's per-request isolation"

> "All three run at concurrency 8 on a single r7a.2xlarge AWS instance (8 vCPU, 64 GiB), with a 150 s per-request budget."

> "0.29 req/s 0.57 req/s 1.11 req/s 2.09 req/s 2.09 req/s"

> "throughput plateaus at 2.09 req/s while median latency jumps roughly 4.5× (to 4.68 s) and p90 nearly doubles"

> "0.97 s 10.1 s 95.7 s 0.43 req/s 0.107 req/s 0.026 req/s 9,205 s 37,258 s 151,267 s 100.0% 99.9% 93.8%"

> "verify_proof's median is sub-second, roughly 10× faster than SafeVerify and 99× faster than Comparator at the median."

> "both Comparator and SafeVerify run an environment replay step that re-typechecks each declaration to verify its soundness"

> "AXLE and Comparator agree on every one of the 938 conclusive pairs (Table 4)."

> "verify_proof accepts false : False as-is; a kernel-replay checker like lean4checker (Lean FRO, 2023) re-runs the environment through the kernel from a clean state, detects the ill-formed declaration, and rejects."

> "Each request runs in its own sandboxed process."

> "The Kimina Lean Server (Dos Santos et al., 2025) pools many REPL instances behind a REST API with header-level LRU caching, aimed at high-throughput verification in RL training. It matches AXLE in throughput."

> "or restated theorems would teach the policy to game the reward"

## Methods and evidence
- Data / setting: 5,000 random proofs (fixed seed) from banach1729/goedel-workbook-lean427 (Lean 4.27.0). Imports are normalised to `import Mathlib`, and non-Mathlib dependencies are dropped. The strict-checker comparison uses 1,000 internal production verify_proof requests.
- Baselines: Kimina Lean Server built from source on Lean 4.27.0 with default settings; raw Lean subprocess per request; Comparator; SafeVerify. AXLE's extra bookkeeping was disabled for fairness. All systems were pre-warmed.
- Evaluation: a single run with no variance, but latency percentiles are reported (median, p90). Verdict equality is checked across systems.
- Artifacts: a free hosted service, the `axiom-axle` PyPI SDK, an MCP server, and an example notebook. The server-side implementation is not clearly open source, and the strict-checker corpus is internal.

## Limitations and caveats
- Authors concede: there is no multi-file or arbitrary-dependency support, only a fixed header per environment. There is no interactive proof session or tactic-state tree search (it is stateless). verify_proof does not defend against adversarial kernel bypass.
- The service operator reports on its own service: a mild conflict of interest, although it is free and the paper honestly shows the competitor winning on throughput.
- The abstract's "500 million requests" and "12/12 Putnam" figures are not supported by any data in the paper. They are context, not evidence.
- The abstract says existing infrastructure lacks "scalable proof verification … at the throughput modern AI workflows require". Yet the paper itself finds that Kimina "matches AXLE in throughput". The abstract's gap is really about *strict* verification, isolation and multi-version support, not raw throughput.
- Single-box numbers only (8 vCPU). There is no cluster-scale throughput, even though the service is described as elastic.

## Contradictions and tensions
- Corroborates [[santos2025kimina]]: a warm Mathlib is ≈2× faster than a cold one (2.13 vs 1.03 req/s here; 1.94× there). The per-core throughput class is similar (≈0.27 req/s/core here vs ≈0.31 proofs/s/core in Kimina Table 2 at 64 cores, with different Lean versions and data).
- [C: vs shen2026keep] Raw Lean with a fresh Mathlib import has a median of 5.14 s per request end-to-end here, against Shen's ≈60 s import per branch. Shen's figure reflects an 8 GB laptop and `lake build`.
- Tension with the REPL-based white-box tools ([[kripner2025leantree]], and Pantograph as cited): AXLE is deliberately stateless and declaration-level, and it trades tactic-state interaction for isolation.
- [[achim2025aristotle]] and [[chen2025seeda]] (LooKeng) (round 2) also run stateless Lean backends, with state carried in the request, but give no latency or throughput numbers. AXLE remains the only one of the three with a measured cost.
- Round 2: [[wang2026longcat]] documents an actual RL run where the policy gamed a compile+target-consistency reward within ~80 steps (97.9% syntax-pass vs 27.9% AST-legal on 1,024 training problems), confirming the warning here; [[vamshi2026reward]] shows `sorryAx`-dependent proofs passing Kimina's sorry scan (an axiom whitelist as in verify_proof would reject them); [[ammanamanchi2026faults]] notes Comparator does not catch the pre-4.20 `apply?` bug class, so the 95.7 s tier is not strictly stronger on every exploit.

## Open questions
- How does AXLE get "Mathlib preloaded" with a fresh sandboxed process per request (fork-server? CRIU? mmap'd oleans)? The paper does not say.
- What would the RL reward-hacking rate be under `check` versus `verify_proof` in an actual RL run? Only anecdotes are given.

## Leads for next round
- term: strict proof verification; environment replay; kernel bypass (`addDeclCore doCheck := false`); axiom whitelist; per-request sandbox isolation; multi-version Lean environments.
- cited: lean4checker / `leanchecker` (Lean FRO, integrated in Lean v4.28.0); Comparator (Lean FRO, 2025); SafeVerify (GasStationManager, 2025); FormalQualBench (Math Inc.); jixia (FrenzyMath); lean-lsp-mcp; APOLLO (arXiv:2505.05758); Hilbert (arXiv:2509.22819); Numina-Lean-Agent (arXiv:2601.14027); Leanstral (Mistral 2026); Goedel-workbook-lean427 dataset.
- author: Jannis Limperg (Aesop; ABEL co-author), Chris Cummins.
