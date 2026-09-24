# shen2026keep — Keep the Proof State Live: Snapshotting for Efficient Tactic Search in Lean 4

Austin Shen, Yunong Shi (University of Michigan; Amazon Web Services)
arXiv 2026 · arXiv:2605.25556 (v2, 27 May 2026) · `pdf/shen2026keep.pdf`

**Tier: T4**: an unreviewed preprint on a single 8 GB laptop with a weak baseline (`lake build` per branch, which also compiles `.olean`s, at W≈2 because of RAM). Key cost components (18–735 s of theorem-body elaboration, Level-1 comparison) are estimated or back-computed, not measured. Code is only promised. The mechanism itself is sound and relevant.
**Relevance: 3**: RQ3 (proof-state snapshot/fork inside the Lean server; the "Level 0/1/2" taxonomy of state reuse).
**Read:** full text

## Summary
In portfolio tactic search over DSP sketches, each branch (a tactic substituted for a `sorry`) is normally checked by rebuilding the whole file: import Mathlib, then re-elaborate the theorem body up to the hole. The authors patch Lean v4.25.1's `Lean.Server.FileWorker` with three JSON-RPC methods: `dspSnapshotPing`, `dspSnapshotCapture` and `dspSnapshotBranch`. These expose the language server's existing per-position elaboration snapshot so that it can be forked. The immutable Environment (≈2–4 GB) is shared by reference, and only the MetavarContext (≈KB) is copied per branch. The branches run in parallel via `IO.asTask`. On 45 hand-crafted miniF2F-v2 sketches and 3 end-to-end DSP runs, wall time drops 5.6–50× against the `lake build` fallback. Accuracy is unchanged by construction.

## Key points
- [V] Headline: "5.6–50× wall-time speedup over the standard fallback (average 14×, median 9.7× across the 45 hand-crafted benchmarks)" (Abstract; Table 1).
- [V] Speedup grows with hole count: 7.9× at 1 hole, 9.4× at 2, 13.8× at 3, 24.6× at 4 and 29.8× at 5, with B = 7·H branches (Table 1).
- [V] The claimed per-branch cost decomposition is ≈60 s import loading plus an "estimated 18–735 s" of theorem-body elaboration, together >99% of per-branch wall time (Abstract, §4.3). The 18 s and 735 s bounds are **back-computed** from `lake build` timings (footnote 1), not measured directly.
- [V] The authors concede that the LSP body elaboration is only ≈15 s, and that "the lake build fallback is much slower because it also compiles to .olean" (§4.3). Much of the baseline cost is therefore `.olean` emission, not re-elaboration.
- [V] Tactic execution per branch: a few ms to 500 ms, P95 = 289 ms over 833 branches, and aesop sometimes takes several seconds (Abstract, §4.4). Mean tactic CPU is 45 ms (Table 2).
- [V] Native per-branch cost averages 6.8 s (LSP round-trip plus snapshot retrieval), not the "≪1 ms" fork shown in Fig. 1 (Table 2, §4.3).
- [V] Memory: the fallback needs ≈3 GB per concurrent branch, so W ≈ 2 on a laptop. Snapshotting copies only the KB-sized MetavarContext (§1).
- [V] A 7-tactic portfolio on a simple theorem gives branch-dispatch wall time ≈0.58 s against a sequential 1.43 s, a 2.5× reduction (§3.1).
- [V] Fitted model: native ≈ 120 + 0.045B s; fallback ≈ 75 s/branch; crossover at B ≈ 2 (Table 4, §4.4).
- [V] The Level-1 (Kimina-style) comparison is **estimated** (~330 s), as is Level 1+2 (~17 s/theorem, ">100×", not implemented). Only Levels 0 and 2 are measured (Table 3).
- [P] Taxonomy: Level 0 rebuilds per branch; Level 1 caches the post-import Environment across theorems (Kimina); Level 2 snapshots at the `sorry` boundary after body elaboration. Levels 1 and 2 are presented as composable (§1, §2).
- [P] The paper notes that Lean 4.19 parallel elaboration of theorem bodies targets batch builds, not runtime forking (§2).
- [P] The paper states the Harmonic Aristotle REPL service operates at "Level 0". This is the authors' reading of Aristotle, not verified here (§2).

## Verified quotes
> "our approach achieves a 5.6–50× wall-time speedup over the standard fallback (average 14×, median 9.7× across the 45 hand-crafted benchmarks)"

> "import loading, which deserializes pre-compiled libraries (≈60 s per branch); and (2) theorem-body elaboration, which re-checks the theorem context up to the target goal (estimated 18–735 s depending on proof complexity)"

> "The 18 s lower bound is min(native_s)−T"

> "Tbody ≈ 15 s (LSP elaboration time; the lake build fallback is much slower because it also compiles to .olean)"

> "7.9× (6.3–9.6×) 9.4× (5.6–19.9×) 13.8× (6.5–20.2×) 24.6× (13.1–50.0×) 29.8× (20.1–45.2×)"

> "P95 = 289 ms across 833 measured branches"

> "Native per-branch cost (6.8 s average) reflects LSP round-trip latency, file-worker snapshot retrieval, and per-branch elaboration of only the tactic step—not a full Mathlib reload."

> "the fallback requires ≈3 GB per concurrent branch (limiting a typical laptop to W ≈ 2 workers)"

> "The Environment (all Mathlib constants and type-class instances, ≈2–4 GB) is immutable and shared across branches by reference; only the MetavarContext (open proof obligations, ≈KB) is copied per branch."

> "wall time is ≈0.58 s (≈1.20× the slowest branch at 0.49 s), versus a sequential prediction of 1.43 s"

> "Level 1 (import cached, W = 2 workers) Level 2 (this work, snapshot) Level 1+2 (persistent server + snapshot, not yet implemented ) 2,641 s (meas.) ∼330 s (est.) 133 s (meas.) ∼17 s/theorem (est.)"

> "Native model: Tnative ≈ 120 + 0.045B s."

> "All experiments run on a MacBook Pro (Apple M-series, 8 GB RAM, macOS) with the dsp-patched Lean binary and Lean toolchain leanprover/lean4:v4.25.1."

> "The current implementation starts a fresh LSP server for each theorem, paying the Mathlib import cost (≈60 s) once per theorem rather than once per session."

> "reporting a 1.94× speedup on NuminaMath-LEAN"

## Methods and evidence
- Data / setting: 48 miniF2F-v2 problems. 45 have hand-crafted sketches with 1–5 holes, built so that some portfolio tactic closes every hole; 49 were built and 4 were excluded. 3 are full GPT-4.1-mini DSP runs. The portfolio is 7 tactics: aesop, norm_num, omega, ring, linarith, decide, simp.
- Baselines: only the `lake build`-per-branch fallback (Level 0), at W≈2 for the 45 benchmarks and W=1 for the 3 end-to-end runs. No REPL-based baseline (Kimina, LeanInteract, Pantograph) is run.
- Evaluation: each problem is timed twice (once native, once fallback). There are no repeats or variance, and all runs are on one machine.
- Artifacts: the patched binary and pipeline are "will be released" (github.com/A2DR1/Lean_Snapshot). None had been released when the paper was written.

## Limitations and caveats
- Authors concede: the method is acceleration only; it needs a patched Lean binary; it restarts the LSP per theorem; everything ran on one 8 GB Mac; and the benchmark is a small slice.
- Not conceded: the baseline is a strawman for RL use. Nobody verifying RL rollouts runs `lake build` per branch with `.olean` emission on 8 GB of RAM. The headline 5.6–50× is thus largely "LSP vs. lake build + swap-constrained concurrency". The ≈60 s Mathlib import figure is also far above the ≈3 core-s implied by [[santos2025kimina]] Table 3 and the ~5 s median cold-start in [[xin2026axle]] Table 2, most likely because of the 8 GB RAM machine.
- The abstract's "estimated 18–735 s" of theorem-body elaboration conflicts with the paper's own statement that LSP body elaboration is ≈15 s and with Fig. 1's "~15–300 s". The large figures bundle `.olean` compilation. → `claims_exceed_evidence=true`.
- The Level-1 comparison (the relevant one against Kimina) and the ">100×" Level 1+2 figure are projections, not measurements.
- Fig. 1's "fork ≪1 ms" contrasts with the measured 6.8 s native per-branch cost.

## Contradictions and tensions
- [C: vs santos2025kimina] Import-load cost: Shen assumes ≈60 s per branch. Kimina's cached vs non-cached runs imply ≈3 core-s per proof on a 540 GB server. The discrepancy is hardware- and baseline-driven, so Shen's absolute numbers should not be transferred.
- [C: vs xin2026axle] AXLE measures raw per-request Lean (fresh process, Mathlib import) at a median 5.14 s latency. That is an order of magnitude below Shen's 60 s import.
- [[kripner2025leantree]] is cited here with a "3.4× accuracy improvement". That figure is white-box vs black-box *linear rollout* (18.36/5.32). Against black-box whole-proof generation (9.59%) the ratio is ~1.9×.

## Open questions
- What speedup does snapshotting give over a properly warmed REPL pool (Kimina/LeanInteract with `pickle` or `env` reuse), on server hardware?
- How does it compare with the REPL's own `proofState` reuse and `pickleTo` of proof states, which already allow branching from a stored tactic state?
- Is `IO.asTask` fan-out inside a single server process safe against aesop and other heavy tactics blowing memory?

## Leads for next round
- term: proof-state snapshotting; Level 0/1/2 state reuse; `IO.asTask` branch fan-out; Lean `SavedState`; Lean 4.19 parallel elaboration; portfolio tactic search.
- cited: Draft-Sketch-Prove (Jiang et al., ICLR 2023); "Reviving DSP" (Cao et al., arXiv:2506.11487); Aristotle (Harmonic, arXiv:2510.01346), described as a REPL service with "compressed state serialization"; miniF2F-Lean revisited / miniF2F-v2 (Ospanov et al., arXiv:2511.03108); Aesop (Limperg & From, CPP 2023); Pantograph (arXiv:2410.16429); LEGO-Prover.
- author: Yunong Shi (AWS).
