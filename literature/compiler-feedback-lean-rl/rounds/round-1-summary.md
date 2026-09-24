# Round 1 — summary

180 records screened (22 queries: 16 index + 6 web), 51 screened out, 14 read. Tiers: T1 ×2
(`yang2023leandojo`, `xin2024deepseeka`), T2 ×3 (`gehring2024rlef`, `olausson2023self`,
`kim2026process`), T3 ×8, T4 ×1 (`shen2026keep`). verify-quotes: 273/273.

## Findings per research question

### RQ1 — feedback as a training signal
- Binary whole-proof Lean reward + GRPO is the working default, but its marginal gain over SFT/expert
  iteration is small: 51.6% vs 50.4% miniF2F pass@128 (`xin2024deepseeka` [V], T1). Sparse reward is
  handled by filtering prompts to medium difficulty, not by denser signal.
- Denser tactic-level signal from Lean's first-error position adds 0–1.4 pp over outcome-only GRPO,
  inside reported std; tactic-only reward collapses early (`kim2026process` [V], T2).
- Feedback **as model input** only pays at matched budget once the model is *trained* to use it:
  untrained models (incl. gpt-4o) gain nothing from multi-turn feedback; RLEF-trained 70B goes
  27.5→40.1 1@3 on CodeContests (`gehring2024rlef` [V], T2). Prompted self-repair is ≤~8% relative
  over i.i.d. resampling at matched sample count and sometimes worse (`olausson2023self` [V], T2).
  These two agree rather than contradict.
- Lean error-conditioned repair via SFT on 260k synthetic mutations (APRIL) is a weak, single-run
  result; the untuned base model beats finetuned ones on line/multi-line repair (`wang2026learning`
  [P], T3).
- Failure modes seen: reward hacking of a syntax-only "compiler" by whitespace output
  (`wang2022compilable` [V], T3); fast verifiers that skip the kernel re-check accept an injected
  `false : False` (`xin2026axle` [V], T3); the old REPL tactic mode accepted 12 wrong miniF2F proofs
  (`kripner2025leantree` [V], T3); environment infidelity (lean-gym misjudged 21.1% of correct proofs
  → "too noisy ... for reinforcement learning", `yang2023leandojo` [V], T1).

### RQ2 — environments and world models
- Lean environments: LeanDojo injects interaction as a tactic at the original location to get
  fidelity (1.4% misjudged) (`yang2023leandojo`, T1); Pantograph exposes goal-level state, dormant
  goals and metavariable coupling but has no timing evidence (`aniva2024pantograph`, T3).
- Code environments at scale: CWM builds >35k Docker repo images via an LLM setup agent and local CI
  replay (`team2025cwm` [P], T3).
- Learned executors ("world models"): per-step accuracy is high (CWM 96.9% state exact match;
  E.T. 96–99%) but compounds to ~73–80% whole-program accuracy (`armengolestape2025what` [V], T3).
  Trace training lifts output-prediction benchmarks (CruxEval-O 44.6→73.9) but not generation
  (SWE-bench Verified 18.6→18.4) (`team2025cwm` [V], T3). **No round-1 source measures a learned
  model of Lean elaboration/verification.**

### RQ3 — efficient Lean verification
- Dominant, reproduced mechanism: keep Mathlib imported in a pool of warm REPL processes and reuse
  the environment by header → ~2× throughput. Kimina 1.94× (7:56 vs 15:28, 9,419 proofs, 64 cores)
  (`santos2025kimina` [V]); independently AXLE measures Kimina 2.13 req/s vs raw Lean 1.03 req/s on
  8 vCPU, 5.14 s median cold start (`xin2026axle` [V]). Roughly 0.27 req/s per core.
- Deeper reuse (fork the elaboration snapshot at each `sorry`, share the Environment, copy only the
  MetavarContext) claims 5.6–50× but against `lake build` on a laptop (`shen2026keep`, T4,
  `claims_exceed_evidence`).
- Strict checking is expensive: AXLE `verify_proof` 0.97 s vs SafeVerify 10.1 s vs Comparator 95.7 s
  (`xin2026axle` [V]). Speed and soundness trade off directly.
- DeepSeek-Prover-V1.5 uses a fresh process per proof on thousands of CPU cores — i.e. no reuse
  (`xin2024deepseeka` [P]).

## Consensus (≥2 T1/T2)
- Environment/verifier fidelity is a precondition for RL; noisy verdicts poison the signal
  (`yang2023leandojo`, `kim2026process` on timeouts starving reward).
- Feedback text helps only when training teaches its use; prompting alone ≈ resampling
  (`gehring2024rlef`, `olausson2023self`).
- Outcome reward remains necessary; process signals are auxiliary (`kim2026process`, `xin2024deepseeka`).

## Contradictions
- `shen2026keep` vs `santos2025kimina`/`xin2026axle`: Mathlib import ≈60 s vs ≈3 core-s / 5.14 s.
  Most likely reason: 8 GB laptop and `lake build` baseline vs server hardware with warm processes.
- `team2025cwm` conclusion vs its own Table 4: credits world-model data for agentic gains that the
  ablation attributes to Docker trajectories.
- `kripner2025leantree` 1.9× vs the "3.4×" `shen2026keep` attributes to it.

## Gaps
1. Memory per warm Mathlib REPL process; verifier CPU-hours per RL step; RL-time timeout choices.
2. REPL environment/proof-state pickling (`pickleTo`/`unpickleEnvFrom`), LeanInteract — not read.
3. Learned surrogate verifiers / next-tactic-state models for Lean (LeanUniverse) — unmeasured.
4. Soundness hardening (`sorry`, axioms, `native_decide`, statement tampering) as an RL
   reward-hacking defence.
5. Lean-specific matched-budget comparison of repair-from-errors vs resampling (Seed-Prover's
   refinement-efficiency claim).
6. Classic code-RL baselines (CodeRL, PPOCoder, StepCoder, RLTF) not read.

## Vocabulary learned
`RLPAF`, `truncate-and-resume`, `RMaxTS`, `process oracle / first-error propagation`, `import/header
caching`, `Level 0/1/2 state reuse`, `elaboration snapshot`, `MetavarContext fork`, `pickleTo /
unpickleEnvFrom`, `SafeVerify`, `Comparator`, `lean4checker/leanchecker`, `dormant goals`,
`white-box proof search`, `factorized states`, `execution tuning`, `dynamic scratchpad`,
`ForagerAgent`, `LeanUniverse`, `hybrid verifier`, `matched budget / compute-matched`.
