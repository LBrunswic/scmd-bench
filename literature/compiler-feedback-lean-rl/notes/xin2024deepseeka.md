# xin2024deepseeka — DeepSeek-Prover-V1.5: Harnessing Proof Assistant Feedback for Reinforcement Learning and Monte-Carlo Tree Search

Huajian Xin, Z. Z. Ren, Junxiao Song, Zhihong Shao, Wanjia Zhao, Haocheng Wang, Bo Liu, Liyue Zhang, Xuan Lu, Qiushi Du, Wenjun Gao, Qihao Zhu, Dejian Yang, Zhibin Gou, Z. F. Wu, Fuli Luo, Chong Ruan (DeepSeek-AI)
ICLR 2025 (read: arXiv v1, 15 Aug 2024) · arXiv:2408.08152 · `pdf/xin2024deepseeka.pdf`

**Tier: T1** — peer-reviewed at ICLR 2025 (confirmed via proceedings.iclr.cc / OpenReview I4YAIwrsXa; the archived text is arXiv v1 and does not say so itself). Base, SFT and RL weights and the RMaxTS code are released. It is the de-facto baseline for later Lean RL work, including [[kim2026process]], which re-runs it. The headline numbers match the tables, but the RL-over-SFT gain is modest, and the miniF2F/ProofNet validation sets were used in SFT expert iteration.
**Relevance: 3** — RQ1: binary whole-proof Lean reward with GRPO, and error-truncation used for search. RQ3: verifier deployment, with 300 s timeout, a fresh REPL process per verification, and thousands of CPU cores.
**Read:** full text (§1–5, Tables 1–3, Fig. 3–5); appendices skimmed.

## Summary
DeepSeek-Prover-V1.5 is a 7B Lean 4 whole-proof generator. Training runs in three stages: math/formal pre-training; SFT on 9.6M sequences built by expert iteration, with NL chain-of-thought comments and inserted tactic-state comments as an auxiliary target; and GRPO online RL ("RLPAF"), where the Lean verdict is a 0/1 reward on about 4.5k prompts filtered to medium difficulty. At inference, Lean feedback enters a second way. Generated proofs are truncated at the first Lean error, the valid prefix is split into tactic nodes of an MCTS tree, and generation resumes from a node with the Lean tactic state appended as a comment ("truncate-and-resume"). RMaxTS adds a curiosity reward, equal to 1 when an expansion adds a new tactic-state node, and uses discounted UCB. Together these reach 63.5% on miniF2F-test and 25.3% on ProofNet-test at very large budgets (up to 32×6400 samples).

## Key points
- [V] The RL reward is binary whole-proof verification: 1 if Lean accepts the proof, 0 otherwise. The authors concede it is sparse (§2.3 "Rewards").
- [V] Sparsity is handled by prompt curation rather than by reward shaping: they keep theorems on which the SFT model has a moderate success rate, "approximately 4.5k unique theorem statements" (§2.3 "Prompts").
- [V] GRPO settings: lr 5e-6, KL 0.02, group of 32 proofs per theorem, max length 2,048 (§2.3 "Training Setting").
- [V] What RL adds is small. At pass@128, CoT RL scores 51.6% on miniF2F against 50.4% for SFT, and 18.2% vs 15.9% on ProofNet (Fig. 3). With CoT and RMaxTS at 16×6400, RL reaches 62.7%, which the authors call a "3.7%" gain over SFT (§4.2, Table 3).
- [V][C: vs yue2025does, lin2025goedela] The authors claim RL gives "a genuine enhancement of fundamental capabilities" that stays stable as the sample budget grows, unlike DeepSeekMath's reranking effect (§2.4). The evidence is +0.7 to +2.3 pp at pass@128 on miniF2F (derived from Fig. 3's table). That supports "not only TopK reweighting" only weakly.
- [V] Lean feedback at inference: "the code is truncated at the first error message, and any subsequent code is discarded". The latest tactic state is appended as a comment to the resume prompt (§1, §3.1).
- [V] Ablation of the tactic-state signal: without the tactic-state comment, "the performance gain from applying tree search becomes moderate" (§4.3, Fig. 5). The gap at the largest budget is about 1.6 pp (Fig. 5 table), and there is no variance estimate at that budget.
- [V] Without the intrinsic reward, UCT "degenerates into a level comparable to that of non-search methods" (§4.3). With binary extrinsic reward alone, search gets no signal.
- [V] Single-pass headline: 60.2% on miniF2F-test, "10.2 percentage points" over V1's 50.0%. This is at the 16×6400 sample budget (Table 1).
- [V] Sample-efficiency comparison: 54.9% with 3,200 whole-proof samples against InternLM2-StepProver's 54.5% at 64×3200 tree searches (§4.1).
- [V] The 63.5% headline uses a mixture strategy: half the budget CoT and half non-CoT, at the largest budget (§4.2, Table 3, † in Table 1).
- [V] Verifier deployment: the Lean REPL runs "on a cluster with thousands of CPU cores". Each verification is an individual process "created and terminated in a sandbox". Generation and verification are asynchronous, with 256 MCTS runners per node and 32 thread workers per tree (§3.4).
- [V] Evaluation verification uses a 300 s time limit per proof (§2.4). No RL-time timeout or verifier throughput is reported.
- [V] The Lean REPL was extended with LeanDojo extraction tools to produce (position, state-before, state-after) triples per tactic (§2.2).
- [V] The authors frame the compiler as "the world model to provide environmental supervision". Future work they name is a partial-proof critic for step-wise credit assignment (§5).
- [P] No discussion of reward hacking (`sorry`, `axiom`, statement tampering). The paper never states how the verifier rejects `sorry`/new axioms, and the word "sorry" does not appear in the text.

## Verified quotes
> "each generated proof receives a reward of 1 if verified as correct, and 0 otherwise"

> "While this binary reward signal is accurate, it is also sparse, especially for theorems that are challenging for the supervised fine-tuned model."

> "After filtering, we retain approximately 4.5k unique theorem statements."

> "We use a constant learning rate of 5e-6, and the KL penalty coefficient is set to 0.02. For each theorem, we sample a group of 32 candidate proofs, with maximum length set to 2,048."

> "with an average accuracy of 51.6% on miniF2F and 18.2% on ProofNet"

> "50.4% ± 0.4%"

> "15.9% ± 0.6%"

> "DeepSeek-Prover-V1.5-RL achieves a pass rate of 62.7% on miniF2F-test. This performance shows a notable 3.7% improvement over the SFT model"

> "we observe a genuine enhancement of fundamental capabilities in formal theorem proving"

> "If an error is detected, the code is truncated at the first error message, and any subsequent code is discarded."

> "we append the latest state from the Lean 4 prover as a comment at the end of the prompt"

> "the performance gain from applying tree search becomes moderate in the absence of tactic state information"

> "degenerates into a level comparable to that of non-search methods"

> "achieved the highest pass rate at 60.2%, marking a significant improvement of 10.2 percentage points over DeepSeek-Prover-V1’s 50.0%"

> "requires only 3200 whole-proof generation samplings to achieve a pass rate of 54.9%, surpassing the previous state-of-the-art result of InternLM2-StepProver, which performs 64 × 3200 tree searches to achieve 54.5%"

> "allocates half of sample budget to the CoT mode and the remains to the non-CoT mode"

> "achieving a pass rate of 63.5% on miniF2F-test"

> "The Lean prover is invoked through REPL and executed on a cluster with thousands of CPU cores, where each proof verification task is handled by an individual process, created and terminated in a sandbox."

> "We deploy 256 MCTS runners per node, with one language model per GPU and a batch size of 512 for proof generation."

> "We manage each search tree with 32 thread workers to parallelize the tree iteration steps."

> "The verification process is subject to a time limit of 300 seconds."

> "We enhanced the Lean REPL (Read-Eval-Print Loop; Leanprover Community, 2023) with data extraction tools from the LeanDojo (Yang et al., 2023) project."

> "with the compiler oracle serving as the world model to provide environmental supervision"

> "A promising future direction is training a critic model to assess incomplete proofs and prune search branches."

> "Note that the validation set of ProofNet is used to perform expert iteration in supervised fine-tuning."

> "and validation sets from the miniF2F (Zheng et al., 2022) and ProofNet (Azerbayev et al., 2023) benchmarks"

> "The resulting proof dataset consists of 9,645k sequences."

## Methods and evidence
- Data / setting: Lean 4.9.0, with Mathlib4 and Aesop imported. SFT uses 9,645k sequences from expert iteration over Mathlib4, V1 synthetic theorems, Lean Workbook and the miniF2F/ProofNet validation sets. RL uses about 4.5k filtered prompts, each run in both CoT and non-CoT mode.
- Baselines: DeepSeek-Prover-V1, InternLM2-StepProver, HTPS, ReProver, Lean-STaR, COPRA, Llemma, GPT-f. Tree-search baseline numbers are copied from the original papers.
- Evaluation: pass@K on miniF2F-test (244) and ProofNet valid/test (185/186). Mean ± std is reported for the smaller budgets; the number of runs behind the std is not stated in the main text. Temperature 1, top-p 0.95. The Base model's ProofNet few-shot demonstrations come from the RL model's own proofs.
- Artifacts: Base/SFT/RL weights and RMaxTS code on GitHub (deepseek-ai/DeepSeek-Prover-V1.5).

## Limitations and caveats
- Test hygiene: the miniF2F and ProofNet **validation** sets are part of the SFT/expert-iteration data (§2.2, Table 2 ‡). Validation numbers are not held-out, and ProofNet "valid" appears in the "all" column.
- The headline 63.5% / 25.3% needs 32×6400 or 4×6400 budgets plus a CoT/non-CoT mixture. Single-pass pass@32 is ~50%. The abstract numbers match the tables, but the budget is not in the abstract.
- The isolated RL contribution is small (about +1 to +3.7 pp). The paper's language ("genuine enhancement of fundamental capabilities") is stronger than the Fig. 3 differences. Flagged, not treated as abstract-vs-table disagreement: `claims_exceed_evidence=false`.
- The binary reward gives no credit inside a failed proof. The authors themselves name a partial-proof critic as the missing piece. [[kim2026process]] attacks exactly this gap.
- There is no reporting of RL-time verifier cost, RL timeout, or throughput. At evaluation, "thousands of CPU cores" and one process per verification (no REPL reuse) is the only infrastructure detail.
- Failure modes such as `sorry`, `axiom` or `native_decide` exploitation are not discussed.

## Contradictions and tensions
- [[kim2026process]] re-runs outcome-only GRPO on DeepSeek-Prover-V1.5 (after extra STP SFT). It finds GRPO "fails to yield any gains on ProofNet" and sometimes underperforms the SFT baseline. That tempers this paper's claim that RLPAF gives a stable general enhancement. The settings differ: LoRA, G=4, 15 s timeout and non-CoT, against full RL with G=32.
- [[santos2025kimina]]: DeepSeek spawns a fresh sandboxed REPL process per verification, with no import/header caching (Level 0 in the [[shen2026keep]] taxonomy) and brute-force parallelism over thousands of cores. Kimina's server shows about 2× from header caching. DeepSeek's reported setup therefore leaves that factor unused.
- [[wang2026learning]] uses the error message and goal state as a **supervised input** for repair. DeepSeek uses the first error only to truncate, and keeps the tactic state (not the error text) as the resume prompt. The two design choices, discarding the erroneous suffix vs editing it, have not been compared head-to-head.
- [[polu2022formal]] / [[lin2025goedela]] (round 2): the small RL-over-SFT gain here (+1.2 pp pass@128) has the same order as classic expert iteration's out-of-distribution gain (+3.7 pp miniF2F-test pass@1 over 8 iterations, ≈2000 A100-days, Polu Table 2). Goedel-V2 reports that RL raises pass@1 but lowers pass@32 (diversity collapse) and needs weight averaging to recover it, which tempers the claim here that RL gives a budget-stable "genuine enhancement".
- [[yue2025does]] (round 2): across math and code, RLVR raises pass@1 but base or SFT models overtake at k in the tens to hundreds, and the boundary narrows with longer training. This is in *tension* with this paper's "genuine enhancement" claim, which rests on +0.7 to +2.3 pp at pass@128. There is no Lean test in Yue, and no RL-vs-SFT comparison here at k ≫ 128 without tree search.

## Open questions
- What was the Lean timeout during RL, and how many verifier CPU-hours did RLPAF use?
- Does RLPAF's gain survive once evaluation is decontaminated from the miniF2F-valid-derived SFT data?
- How is `sorry` or axiom use rejected in the reward? Is the REPL's `sorries`/messages field checked?

## Leads for next round
- term: RLPAF (reinforcement learning from proof assistant feedback); truncate-and-resume; RMaxTS; discounted UCB (DUCB); virtual loss; tactic-state comment augmentation; intrinsic reward / ZeroRMax.
- cited: [24] Lean REPL (leanprover-community/repl); [55] LeanDojo; [52] InternLM2-StepProver (Wu et al., 2024); [23] Hypertree Proof Search; [26] Lean-STaR; [40] DeepSeekMath/GRPO; [16] miniCTX (Hu, Zhu, Welleck 2024); Arjona-Medina 2019 RUDDER (return decomposition for proof-level credit).
- follow-ups: DeepSeek-Prover-V2 (ren2025deepseekproverv2, subgoal RL); STP (Dong & Ma 2025) as a self-play extension on this base; Leanabell-Prover-V2 (verifier-integrated RL).
- author: Huajian Xin, Z. Z. Ren, Zhihong Shao (DeepSeek).
