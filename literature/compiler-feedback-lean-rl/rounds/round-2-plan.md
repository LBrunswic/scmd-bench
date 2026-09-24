# Round 2 — plan

Every row traces to a round-1 key point, gap, contradiction or lead. Budget: 12 read in full.

| # | derived from | strategy | query or seeds | what would change our view |
|---|---|---|---|---|
| 1 | Gap 2; lead `pickleTo/unpickleEnvFrom`, LeanInteract (santos2025kimina, shen2026keep leads) | terminology expansion | arXiv/web: "LeanInteract", "Lean REPL pickle environment", "Lean proof state serialization" | a measured cost for env/proof-state pickling would give a Level-1.5 option between Kimina and Shen |
| 2 | Contradiction shen2026keep vs santos2025kimina/xin2026axle (Mathlib import 60 s vs ~3–5 s) | contradiction resolution | web/arXiv: "Mathlib import time", "Lean 4 verification throughput", Kimina-Prover RL infra (2504.11354), Aristotle REPL service (2510.01346) | a third independent import-cost measurement settles which regime is realistic |
| 3 | Gap 1 (memory per warm REPL, verifier CPU-h per RL step) | gap filling | Kimina-Prover, Seed-Prover, DeepSeek-Prover-V2 infra sections; web "Lean REPL memory" | any memory/CPU figure bounds how many parallel verifiers a node can run |
| 4 | Gap 4 + failure modes (wang2022compilable whitespace hack, xin2026axle `false:False`, kripner2025leantree 12 false accepts) | adversarial | arXiv: "reward hacking" Lean `sorry` / `native_decide`; SafeVerify; lean4checker; gabor2025evilgenie | a documented RL run that learned an exploit would make strict checking a hard requirement |
| 5 | RQ1 leading conclusion "outcome reward + GRPO works" (xin2024deepseeka) | adversarial | "does reinforcement learning really incentivize reasoning capacity beyond the base model" (RLVR boundary) | evidence that RLVR only sharpens pass@1 and shrinks pass@k would cap what compiler reward can buy |
| 6 | Gap 5; lead Seed-Prover "refinement 32–128× more efficient than pass@k" (xin2024deepseeka/wang2026learning leads) | named-work follow-up | Seed-Prover (2507.23726), Goedel-Prover-V2 self-correction (2508.03613) | a Lean result where error-conditioned refinement beats resampling at matched verifier calls would contradict the olausson2023self analogue |
| 7 | Gap 3; lead LeanUniverse "code world modeling in Lean" (team2025cwm lead) | gap filling | arXiv: "tactic state prediction", "proof state world model", "learned verifier" Lean | any accuracy figure for a learned Lean next-state model answers RQ2's second half |
| 8 | Gap 6; chain votes (le2022coderl, polu2022formal, lample2022hypertree) | citation snowballing | read CodeRL, lean-gym expert iteration, HTPS | classic baselines for execution-RL and online RL in provers |
| 9 | kim2026process first-error rule; Leanabell-V2 lead | named-work follow-up | Leanabell-Prover-V2 (2507.08649) | verifier feedback inside the reasoning trace during RL — the Lean analogue of RLEF |
| 10 | RQ2 code env building (team2025cwm; R2E-Gym/SWE-Gym leads) | terminology expansion | arXiv: "R2E-Gym", "SWE-Gym", "executable environments" | how code-RL environment builders validate environments; transferable to Lean |
| 11 | Recency on T1s | recency | arXiv `--since 2025`: "Lean prover reinforcement learning verifier" | new RL provers with infra detail |
