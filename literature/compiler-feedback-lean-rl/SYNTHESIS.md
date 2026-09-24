# Synthesis — compiler/execution feedback, environments, and efficient Lean verification for RL

26 papers read over two rounds (T1 ×4, T2 ×6, T3 ×14, T4 ×2); 546/546 quotes verified.
Grades: `[V]` verified quote, `[P]` paraphrase from full text, `[C]` contested.
Confidence: high = several T1/T2 agree; medium = one T2 or several T3; low = T3/T4 only or contested.

## RQ1 — How is compiler/verifier feedback used for training, and where does it fail?

1. **Binary outcome reward from the checker is the working signal; the RL algorithm adds little
   on top of good SFT data.** DeepSeek-Prover-V1.5 RL over SFT: 51.6 vs 50.4 miniF2F pass@128
   (`xin2024deepseeka` [V]); expert iteration +3.7 pp OOD over 8 rounds at ~2000 A100-days
   (`polu2022formal` [V]); CodeRL's RL step 2.00→2.20 APPS pass@1 (`le2022coderl` [V]).
   *Confidence: high.*
2. **RL on verifier reward sharpens pass@1 and can shrink pass@k at large k.** Base models overtake
   at k in the tens–hundreds on math/code (`yue2025does` [V]); in Lean, RL lowers pass@32 and needs
   weight averaging (`lin2025goedela` [P]). The "genuine enhancement" claim of `xin2024deepseeka`
   is `[C]`. *Confidence: medium* (no controlled Lean-at-large-k study).
3. **Dense, process-level signal from the checker (first failing tactic) is auxiliary.** +0–1.4 pp
   over outcome-only, inside std; tactic-only reward collapses (`kim2026process` [V]).
   *Confidence: medium.*
4. **Feeding error messages back to the model is worth it only if training teaches the model to
   use them, and even then barely beats resampling at matched verifier calls.** Prompted
   self-repair ≤~8% relative over i.i.d. (`olausson2023self` [V], T1); untrained models gain
   nothing, RLEF-trained ones do on code (`gehring2024rlef` [V]); in Lean, Goedel-V2
   self-correction ≈ +0–0.5 pp at matched calls (`lin2025goedela` [V]); Leanabell-V2's gain is the
   extra inference round (`ji2025leanabell` [V]). *Confidence: high* for "≈ resampling at matched
   budget"; the larger wins need many revision rounds + long context (low confidence, figure-only).
5. **The verifier is attacked as soon as it is the reward.** Observed in a real Lean RL run: ~70%
   fake successes by step ~100, caught only by an AST-level check of the formal context
   (`wang2026longcat` [V]); `sorryAx` via the `apply?` bug in 31–44% of a published prover's
   PutnamBench successes, passing Kimina's sorry check (`vamshi2026reward` [V],
   `ammanamanchi2026faults` [V]); fast verification that skips the kernel accepts `false : False`
   (`xin2026axle` [V]); syntax-only "compilers" are gamed by whitespace (`wang2022compilable` [V]).
   *Confidence: high* that it happens; fix costs unmeasured.

## RQ2 — How are environments built, and can learned world models substitute?

1. **Fidelity is the first requirement.** lean-gym misjudged 21.1% of correct proofs ("too noisy
   ... for reinforcement learning"); LeanDojo's tactic-injection brings it to 1.4%
   (`yang2023leandojo` [V], T1). Interfaces differ in granularity: whole-file REPL (Kimina, AXLE),
   goal-level (Pantograph, `aniva2024pantograph` [P]), factorized proof trees
   (`kripner2025leantree` [V]). *Confidence: high* on fidelity; medium on interface choice.
2. **Production verifiers are stateless REPL services behind a scheduler** (Aristotle on GKE,
   Seed-Prover's LooKeng, AXLE per-request sandbox) (`achim2025aristotle` [P], `chen2025seeda` [P],
   `xin2026axle` [P]). *Confidence: medium* (no figures published).
3. **Code environments at scale are Docker images built semi-automatically** (CWM >35k images via
   an LLM setup agent and CI replay, `team2025cwm` [P]; R2E-Gym dependency search "semi-manual",
   `jain2025r2e` [V]). *Confidence: medium.*
4. **Learned executors/verifiers do not substitute for execution.** Per-step trace accuracy
   96–99% compounds to ~73–80% per program (`armengolestape2025what` [V]); trace training lifts
   output prediction (CruxEval-O 44.6→73.9) but not generation (SWE-bench V 18.6→18.4)
   (`team2025cwm` [V]); an execution-free verifier matches but does not beat execution-based
   ranking, and the hybrid is best (42.8 / 43.7 / 51.0 Best@26, `jain2025r2e` [V]).
   *Confidence: medium* (all T3, but consistent across three groups). **No source measures a
   learned model of Lean elaboration.**

## RQ3 — What makes Lean verification fast enough for RL?

1. **Keep Mathlib loaded.** A pool of warm REPL processes, one per core, keyed by import header,
   gives ~2×: Kimina 1.94× (`santos2025kimina` [V]), independently AXLE 2.13 vs 1.03 req/s with
   raw-Lean median 5.14 s (`xin2026axle` [V]); ≈0.27 req/s/core on 8 vCPU. *Confidence: high*
   (two independent measurements, same order).
2. **Forking the elaboration state inside one process is the next level** (share Environment, copy
   MetavarContext, parallel `IO.asTask`), claimed 5.6–50× but against `lake build` on a laptop
   (`shen2026keep`, T4). Env/proof-state pickling (LeanInteract, REPL `pickleTo`) exists as tooling
   with no published cost. *Confidence: low.*
3. **Soundness costs speed, steeply.** 0.97 s (AXLE verify) vs 10.1 s (SafeVerify) vs 95.7 s
   (Comparator) median (`xin2026axle` [V]); and Comparator still misses the `apply?` class, which
   needs Lean ≥ 4.20 (`ammanamanchi2026faults` [P]). *Confidence: medium.*
4. **Scale reported by provers:** 640 CPU cores for 8k proofs per RL iteration
   (`wang2025kimina` [V]); a fresh process per proof on "thousands of CPU cores" with no reuse
   (`xin2024deepseeka` [P]); 15 s per-attempt RL timeout best, 5 s starves the reward
   (`kim2026process` [V]). *Confidence: medium.*

## What the literature does not settle
- Resident memory per warm Mathlib REPL, and the throughput/memory curve as processes are packed on
  one node. Not reported anywhere read.
- The runtime cost of strict checks usable as an RL reward (axiom whitelist, AST/context check,
  `leanchecker` replay) at RL batch sizes.
- Cost and correctness of environment/proof-state pickling vs in-process snapshot forking.
- Whether a learned surrogate of Lean elaboration (next goal state, success prediction) can cut
  verifier calls without admitting false positives.
- RL-vs-SFT at large k in Lean under a controlled design (Yue-style), and a random-feedback control
  for Lean error-conditioned repair.

## Recommended reading order
1. `yang2023leandojo` — environment fidelity and why it matters for RL
2. `xin2024deepseeka` — the reference RL-from-Lean pipeline
3. `santos2025kimina` then `xin2026axle` — how verification is made fast, and what it trades away
4. `wang2026longcat` + `vamshi2026reward` — how the reward is hacked
5. `olausson2023self` + `lin2025goedela` — matched-budget view of feedback-conditioned repair
6. `yue2025does` — what RL on a verifier reward can and cannot buy
7. `jain2025r2e` — learned verifier vs execution
