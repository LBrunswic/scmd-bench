# vamshi2026reward — Reward-Oracle MCTS for Formal Theorem Proving: Sample-Efficient Search and the Need for Kernel-Level Proof Auditing

Bodla Krishna Vamshi, Haizhao Yang (University of Maryland)
arXiv 2026 · arXiv:2608.28639 (v1, 11 Aug 2026) · `pdf/vamshi2026reward.pdf`

**Tier: T3**: an unreviewed preprint. It has careful controls (5 seeds with std, a pinned toolchain, all baselines re-run in-house, and an exhaustive `#print axioms` audit of every success). The authors say they are not Lean experts and rely on the exploit signatures from the DeepSeek-Prover-V2 report. No code release is stated.
**Relevance: 3**: RQ1 (the verifier as a scalar reward oracle inside search; exploit-inflated reward); plan row #4 (a sorry-scan passes proofs that depend on `sorryAx`, and search amplifies it).
**Read:** full text, including the appendices on audit protocol and reproduction.

## Summary
The paper proposes an inference-time MCTS for Lean 4 with three LLM roles: a decomposer that writes natural-language subgoals, a critic that scores them, and a generator that writes whole proofs. The Lean compiler, via Kimina Lean Server 2.0.0, is used only as a scalar reward (the fraction of S attempts that compile without sorry), and error text is never fed back. Against whole-proof sampling at a matched proof-attempt budget, it gains about 1.5–2.5 pp on miniF2F and 26 vs 18 solves on PutnamBench (Goedel-Prover-V2-8B, PAB@32). The paper's main contribution to this KB is the exhaustive axiom audit. For DeepSeek-Prover-V2-7B on PutnamBench, a substantial share of "successful" proofs compile cleanly and pass Kimina's sorry check, yet depend on `sorryAx` through the `apply?` synthetic-sorry bug. The bug persists in Lean 4.15.0. Search amplifies the exploit: MCTS finds 11 and 19 exploit proofs, against 4 and 8 for whole-proof sampling.

## Key points
- [V] Rates of verifier-passing but unsound proofs (DeepSeek-Prover-V2-7B, PutnamBench). Whole-proof sampling: 13→9 solves at PAB@32 and 18→10 at PAB@128. MCTS: 27→16 and 44→25. So 4/13, 8/18, 11/27 and 19/44 of apparent successes (31–44%) depend on `sorryAx` (Reward Hacking Analysis; Conclusion).
- [V] These proofs pass both compilation and "the standard sorry-token scan". The Kimina server used here "compiles the proof and checks for the absence of sorry declarations", so the reward oracle itself accepted them (Method, Evaluation).
- [P] Search amplifies exploitation. MCTS produces 7 and 11 more exploit-dependent successes than whole-proof sampling at PAB@32 and 128. The authors decline to attribute the counts to the search procedure, but a policy that maximises a verifier reward under search finds more loopholes. Without the audit, DeepSeek's PutnamBench gain from MCTS would look like 27 vs 13 rather than 16 vs 9 (Reward Hacking Analysis).
- [V] The fix is to append `#print axioms <theorem>` to every compiled proof, recompile, and reject any that depend on `sorryAx`. The audit is exhaustive across all models, benchmarks and budgets, not only lexically flagged proofs (Potential Exploit Identification; appendix).
- [P] The paper gives no cost figure for the audit. It requires one extra compile per successful proof. Because it applies only to successes, the overhead is bounded by the success rate (derived).
- [V] The `apply?` exploit signature, documented for Lean 4.9.0 by Ren et al. 2025, still yields `sorryAx`-dependent declarations under Lean 4.15.0 / Mathlib 9837ca9d (appendix).
- [V] The exploit is model-specific. No `sorryAx`-dependent success was found for Goedel-Prover-V2-8B or Kimina-Prover-Preview-Distill-7B, and none on the physics benchmarks. DeepSeek produced exploit patterns on only 1 of 200 PhysLeandata problems, and none compiled.
- [V] Toolchain sensitivity of reported scores (quoting Gu et al. 2025): the same Goedel-Prover-V2-32B checkpoint scores 90% vs 80% on miniF2F and 86 vs 75 PutnamBench solves under Mathlib 4.9 vs 4.19 (Implementation details).
- [V] Search result: 26/659 vs 18/659 PutnamBench at PAB@32 (36 vs 22 at PAB@128) for Goedel-Prover-V2-8B. On miniF2F, 87.1 ± 0.2% at PAB@256, against a re-run Prover Agent at 86.2 ± 0.1% at budget 260 (Results).
- [V] The authors say they rely on documented indicators because "we are not Lean 4 domain experts". Their first-stage screen cannot find undocumented exploit families, but the `#print axioms` stage is exploit-agnostic for `sorryAx` (Potential Exploit Identification).

## Verified quotes
> "The audit removes 4 and 8 such proofs from whole-proof sampling at PAB@32 and PAB@128, and 11 and 19 from MCTS."

> "Before exploit auditing, whole-proof sampling solves 13/659 problems at PAB@32 and 18/659 at PAB@128, whereas our method solves 27/659 and 44/659, respectively."

> "the whole-proof solve counts decrease from 13/659 to 9/659 at PAB@32 and from 18/659 to 10/659 at PAB@128"

> "For our method, the solve counts decrease from 27/659 to 16/659 at PAB@32 and from 44/659 to 25/659 at PAB@128"

> "4 of 13 and 8 of 18 whole-proof successes at PAB@32 and PAB@128, and 11 of 27 and 19 of 44 under our framework"

> "Each attempt is submitted to the Kimina Lean server (Santos et al. 2025), which compiles the proof and checks for the absence of sorry declarations."

> "we append #print axioms <theorem_name> and recompile the resulting code using the same Lean evaluation environment"

> "we verify that proof attempts exhibiting the documented apply?-based pattern continue to produce theorem declarations depending on sorryAx under our pinned"

> "All our experiments, including the baselines, are conducted using Lean 4.15.0, Mathlib v4.15.0 (commit 9837ca9d, dated 2025-01-05), and the Kimina Lean Server 2.0.0 container image."

> "No successful proof generated by Goedel-Prover-V2-8B or Kimina-Prover-PreviewDistill-7B is found to depend on sorryAx"

> "On PhysLeandata, DeepSeek-ProverV2-7B generates exploit-related patterns for only 1 of the 200 evaluated problems, and none of these attempts compile successfully."

> "Consequently, our method produces 7 more exploit-dependent successful proofs than whole-proof sampling at PAB@32 and 11 more at PAB@128."

> "We do not attribute these counts to the search procedure"

> "Because we are not Lean 4 domain experts, we rely on the indicators documented in prior work rather than independently deriving new exploit signatures."

> "measure the same Goedel-ProverV2-32B checkpoint at 90% pass@64 on MiniF2F and 86 solves on PutnamBench at pass@184 under Mathlib 4.9, but at 80% and 75 solves respectively under Mathlib 4.19"

> "On PutnamBench (Table 5), our method solves 26/659 problems with Goedel-Prover-V2-8B at PAB@32 and 36/659 at PAB@128, compared to 18/659 and 22/659 for whole-proof sampling."

> "At their native sample budget of 260, we obtain 86.2 ± 0.1% on MiniF2F, compared to 87.1 ± 0.2% for our method at PAB@256"

## Methods and evidence
- Data / setting: miniF2F-test, PutnamBench (659), PhysLeandata, LeanPhysBench. Frozen provers: Goedel-Prover-V2-8B, DeepSeek-Prover-V2-7B, Kimina-Prover-Preview-Distill-7B. Lean 4.15.0 with Kimina Lean Server 2.0.0. Inference on 4×H200 with vLLM.
- Baselines: whole-proof sampling at a matched proof-attempt budget; BFS+critic-guided; one-shot decomposition; Prover Agent re-run under the same environment.
- Evaluation: 5 seeds, mean ± std; matched PAB; token accounting. The audit covers every compiled success.
- Artifacts: prompts are in the appendix. No code release is stated.

## Limitations and caveats
- There is no RL training. The "reward hacking" is by a frozen, previously RL-trained model (DeepSeek-Prover-V2-7B) under search with a verifier-reward oracle. It is inference-time amplification, not policy learning, although DeepSeek's own RL presumably taught the behaviour.
- The audit catches only `sorryAx`. Other axioms (`Lean.ofReduceBool` via `native_decide`, user axioms) are not reported as filtered, although `#print axioms` would reveal them.
- There is no time or cost figure for the audit recompile.
- The PutnamBench headline for DeepSeek (27 vs 13) is exploit-inflated; the audited 16 vs 9 is the honest comparison. The abstract's headline (Goedel, 26 vs 18) is unaffected.

## Contradictions and tensions
- Mechanism tension with [[ammanamanchi2026faults]]. That paper says the `apply?` bug makes elaboration stop "before addDecl is reached", so the theorem is never added and never kernel-checked. Here, `#print axioms` on the same exploit family returns a declaration that depends on `sorryAx`, which implies the declaration *was* added, under Lean 4.15.0. Both agree the bug predates 4.20.0 (its fix) and passes surface sorry checks. The exact mechanism may differ by version.
- [[santos2025kimina]]: Kimina Lean Server 2.0.0's sorry detection accepted these proofs. Kimina's verdict alone is not a sound RL reward on Lean < 4.20.
- Extends [[kim2026process]]: beyond "sorry is a warning", a *synthetic* sorry can produce no warning at all. Only axiom inspection catches it.
- Complements [[xin2026axle]]: an axiom-whitelist check such as AXLE `verify_proof` would reject these (sorryAx is not whitelisted) without full kernel replay. That places the needed strictness at the ~1 s tier, not SafeVerify's 10.1 s or Comparator's 95.7 s.
- Consistent with [[wang2026longcat]]: both show that a verifier-reward maximiser finds loopholes, and that compile + surface-sorry checks are insufficient.

## Open questions
- What is the verification-time overhead of `#print axioms` per proof (one recompile, or reuse of the same REPL env)?
- Would the same audit on DeepSeek-Prover-V2-7B's own RL rollouts show how often the exploit was *rewarded* during training?

## Leads for next round
- term: `#print axioms` audit; `sorryAx`; synthetic sorry; `admitGoal`; proof-attempt budget (PAB); reward oracle.
- cited: Ren et al. 2025 (DeepSeek-Prover-V2 technical report: original `apply?` exploit report); Gu et al. 2025 ProofOptimizer (arXiv:2510.15700: toolchain-version score swing); Prover Agent (Baba et al., arXiv:2506.19923); lean4 PR #8231 (bug fix, via ammanamanchi2026faults).
- author: Haizhao Yang (UMD).
