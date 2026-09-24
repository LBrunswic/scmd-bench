# Round 2 — summary

8 new index queries + 4 web queries, 2 chain runs (backward/both at min-votes 2 → 29 new; forward on
3 T1/T2 seeds → 38 new, almost all off-topic because OpenAlex barely indexes arXiv citers). 12 papers
read, each tagged with the plan row it answers. KB total: 265 records, 26 read, verify-quotes
546/546. Tiers of read papers: T1 ×4, T2 ×6, T3 ×14, T4 ×2.

## What round 2 added
1. **Reward hacking of Lean is observed, not hypothetical.** In a real RL run, ~70% of rollout
   "successes" were fake by step ~100: compile + definition-match checks pass 97.6%, a strict
   AST check 27.9% (`wang2026longcat` [V], T3). 31–44% of DeepSeek-Prover-V2-7B's PutnamBench
   successes depend on `sorryAx` while passing Kimina Lean Server's sorry check (`apply?` bug,
   Lean < 4.20) (`vamshi2026reward` [V], T3; `ammanamanchi2026faults` [V], T2).
2. **Error-conditioned repair ≈ resampling in Lean at matched verifier calls.** Goedel-Prover-V2
   self-correction pass@32 (≤96 Lean calls) 90.4 vs standard pass@64 89.8 / pass@128 90.5
   (`lin2025goedela` [V], T2). Leanabell-V2's first-attempt score is slightly *below* plain RL; the
   gain is the extra inference round (`ji2025leanabell` [V], T3). Seed-Prover's
   "32–128× over pass@k" is a single-problem anecdote (`chen2025seeda` [P], T3).
3. **RL-algorithm gains are small everywhere; data/curriculum dominate.** Expert iteration: +3.7 pp
   miniF2F pass@1 over 8 rounds, ~2000 A100-days (`polu2022formal` [V], T1). CodeRL's RL step:
   APPS pass@1 2.00→2.20 (`le2022coderl` [V], T2). RLVR narrows pass@k at k in the tens–hundreds
   (`yue2025does` [V], T2; no Lean experiment), and Goedel sees RL lower pass@32.
4. **Learned verifiers filter, they don't substitute.** R2E-Gym's execution-free verifier: 71.82%
   accuracy; Best@26 42.8% vs execution-based 43.7%, hybrid 51.0%, oracle 64.4% (`jain2025r2e` [V],
   T3). Same ~70–80% band as round-1 learned executors.
5. **Infra numbers stay thin.** Kimina-Prover RL: 640 CPU cores for 1000×8 rollouts/iteration
   (`wang2025kimina` [V]); its "10×" and "100 it/s" are unsupported (contradicted by the measured
   1.94×). Aristotle and Seed-Prover's LooKeng both run stateless REPL services with no figures.

## Tier changes
| key | from | to | reason |
|---|---|---|---|
| `olausson2023self` | T2 | **T1** | matched-budget result reproduced in Lean by `lin2025goedela`; consistent with `gehring2024rlef` |
| `xin2024deepseeka` | T1 | T1 (claim marked `[C]`) | work stays T1 as a standard baseline; its "genuine enhancement" RL claim is contested by `yue2025does`, `lin2025goedela` |
| `santos2025kimina` | T3 | T3 (+`replicated`) | ~2× reproduced by `xin2026axle`; sorry detection unsound on Lean < 4.20 (`vamshi2026reward`) |
| `xin2026axle` | T3 | T3 (+`consensus`) | exploit warning confirmed by `wang2026longcat`, `vamshi2026reward` |
| `shen2026keep` | T4 | T4 (+`contradicted_by`) | import-cost figure contradicted by two server measurements |

## Plan-row outcomes
| # | outcome |
|---|---|
| 1 LeanInteract / pickling | **nothing found** in the literature: LeanInteract is a tool with no paper (recorded as unverified web record); pickling cost remains unmeasured |
| 2 import-cost contradiction | **partly**: no third measurement; the Kimina-Prover "10×" is unsupported; reading stays "≈3–5 s warm-server, 60 s is laptop + `lake build`" |
| 3 memory / CPU-h per RL step | **partly**: 640 cores per 8k proofs/iteration; 64 cores / 512 GB machines (≤8 GB/core, derived bound); ~1–3k Lean calls per Goedel RL step (derived). No per-REPL memory anywhere |
| 4 reward hacking | **answered** (see finding 1); fix cost still unmeasured |
| 5 RLVR limits | **partly**: yes for math/code; no Lean experiment, one Lean hint (`lin2025goedela`) |
| 6 refinement vs resampling | **answered**: ≈0–0.5 pp at matched verifier calls |
| 7 learned Lean world model | **nothing found**: LeanUniverse is a dataset library; no measured Lean next-state model |
| 8 classic baselines | **answered** |
| 9 verifier-in-the-loop RL | **partly**: no matched-budget gain; no random-feedback control |
| 10 code env building | **answered for code**: semi-manual Docker dependency search; learned verifier is a complement |
| 11 recency | covered by rows 4, 6, 9 (all 2025–26) |

## Saturation
- Chain: of the 29 min-votes-2 candidates, none were already in the KB, but all were background
  (Codex, LLaMA, InstructGPT, miniF2F…) or classics that round 2 then read (`polu2022formal`,
  `le2022coderl`). Citation space is saturated for *this question*; it is not a signal of missing
  work.
- Conclusions: 5 of 12 round-2 inclusions changed a round-1 conclusion (reward hacking elevated from
  risk to observed; one tier raise; one claim contested; two attributed figures debunked). **The
  review is not saturated on RQ1-failure-modes and RQ3-infra**; a third round should target
  measurement (memory per REPL, strict-check cost, pickling cost), which may only exist in blogs
  (Harmonic "Running Lean at Scale") or would have to be measured locally.
