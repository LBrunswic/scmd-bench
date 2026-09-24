# lin2025goedela — Goedel-Prover-V2: Scaling Formal Theorem Proving with Scaffolded Data Synthesis and Self-Correction

Yong Lin, Shange Tang, Bohan Lyu, Ziran Yang, Jui-Hui Chung, Haoyu Zhao, Lai Jiang, Yihan Geng, Jiawei Ge, Jingruo Sun, Jiayun Wu, Jiri Gesi, Ximing Lu, David Acuna, Kaiyu Yang, Hongzhou Lin, Yejin Choi, Danqi Chen, Sanjeev Arora, Chi Jin (Princeton, NVIDIA, Tsinghua, Stanford, Meta FAIR, Amazon, SJTU, PKU)
ICLR 2026 poster (per the iclr.cc/virtual/2026 listing, found by web search on 2026-09-23; the archived text is the arXiv v1 "Technical Report" of 5 Aug 2025 and does not state a venue) · arXiv:2508.03613 · `pdf/lin2025goedela.pdf`

**Tier: T2** — Peer-reviewed (ICLR 2026, per the conference listing; the archived v1 does not say so). Models, code and data are released. The headline numbers in the abstract match Tables 2–4. It is held back from T1 because the self-correction gain is reported at matched *sample count*, not at matched verifier calls or tokens. At matched verifier calls, Table 4 shows the gain almost vanishes. The key ablation (w/o error messages) appears only as a figure with no numbers in the text. There is one training run, and the unique-input count for the 32B model is inconsistent (67K in §2.3, 64K in App. E.1).
**Relevance: 3** — RQ1: Lean compiler errors as model input for self-correction, trained jointly with whole-proof RL, and model averaging against RL diversity collapse. RQ3 (weak): rollout and Lean-call counts per RL step. There is no verifier timeout or throughput.
**Read:** full text (§1–5, Tables 1–4, Fig. 7–8 captions and prose, App. A–E).

## Summary
Goedel-Prover-V2 (8B and 32B, from Qwen3) is a long-CoT whole-proof Lean 4 prover. It is trained in three stages: expert-iteration SFT on DeepSeek-Prover-V2 outputs; SFT on self-correction data, where the input is a failed proof plus the Lean error and the target is a revision; and scaffolded data synthesis (sub-goals via `extract_goal`, LLM-generated easier or harder variants, and negations). RL then runs as a *multi-task* single-turn setup. Half of the prompts ask for whole proofs, and half are first-round self-correction prompts that include a stored error message. This avoids true multi-turn RL, which the authors tried and call immature. Model averaging with the base model is applied after SFT and after RL to recover pass@N lost to diversity collapse. At inference, "self-correction mode" means 1 attempt plus 2 revision rounds, each conditioned on Lean feedback. The 32B model scores 88.1% pass@32 on miniF2F in standard mode and 90.4% in self-correction mode. On PutnamBench it solves 43, or 57 with self-correction, at pass@32, and 86 at pass@184.

## Key points
- [V] Self-correction is presented as a consistent gain of "approximately 2 percentage points in pass@32" on miniF2F, plus 14 more PutnamBench solves at pass@32 (§3.3, Tables 2–3).
- [V] Budget accounting: a self-correction-mode sample runs 2 extra revision rounds with a 40,000-token total, against 30,000 tokens for a standard sample (§3.2). So pass@32 in self-correction mode means up to 96 Lean calls and 32×40k tokens, while standard pass@32 means 32 calls and 32×30k tokens.
- [P] **At matched verifier calls, the gain almost disappears** (derived from Table 4). 32B self-correction pass@32 (≤96 calls) is 90.4. Standard pass@64 is 89.8 and standard pass@128 is 90.5. For 8B: self-correction 86.7 vs standard 86.1 at 64 and 86.5 at 128. At the large end, self-correction pass@1024 (≤3072 calls) is 92.6 vs standard 92.2 at pass@4096. At matched *tokens* (32×40k ≈ 43 standard samples), the gain is about 1–2 pp. Revision therefore beats resampling only slightly per verifier call. This is consistent with [[olausson2023self]].
- [V] With context extended to 128k (YaRN) and up to 5 revision rounds, self-correction pass@32 averages 92.7%, above the 92.2% of standard mode at pass@8192 (§3.5, Fig. 7). [P] That is up to 192 Lean calls against 8192, so this is the one Lean result in the KB where error-conditioned revision clearly beats resampling at matched verifier calls. It is ~+2 pp over standard pass@256 (91.0). Token cost is not matched (up to 128k context per sample), and the number is read from a figure average with no variance.
- [P] Ablation (Fig. 7, §3.5): removing the compiler error messages "significantly lowers" self-correction performance, and removing prior CoTs "slightly" lowers it. No numbers are given in the text. This is the Lean analogue of [[gehring2024rlef]]'s random-feedback ablation: the error *content* matters, not just the extra attempt.
- [V] RL is multi-task, not multi-turn: "50% of the inputs are used for whole proof generation, and the remaining 50% for first-round self-correction". Self-correction inputs carry a stored SFT-model output and its error message (§2.3, App. E.1).
- [V] Multi-turn RL was explored and abandoned: "multi-turn approaches introduce various engineering challenges, especially on the rollout engine side, such as asynchronous generation" (App. E.2).
- [V] The RL recipe is GRPO with Dr.GRPO (no group normalisation) plus DAPO (clip-higher, overlong penalty, dynamic sampling), no KL, and only prompts with pass rate in (0, 0.75]. This is difficulty filtering, as in [[xin2024deepseeka]] (§2.3).
- [V] RL scale: batch 128, n=8 rollouts, each reward a Lean compile. Over-sampling is 3× the train batch. There is one epoch of about 46K (8B) / 64K (32B, App. E.1; §2.3 says 67K) unique inputs (App. E.1). [P] That is roughly 1,024 Lean calls per optimiser step, up to ~3,072 with over-sampling (derived). No verifier timeout, CPU count or throughput is reported.
- [V] RL raises pass@1 but diversity collapses. In late SFT/RL, pass@1 rises while pass@N (N=32) declines. Averaging (1−α)θ0+αθ recovers pass@N, and there is an interior optimum for α (§2.3, §3.6).
- [P] Correction benefits more from RL than whole-proof generation does. Vanilla pass@N plateaus with RL steps, while correction pass@N keeps improving. The authors attribute this to scarce self-correction SFT data (§3.6, Fig. 8).
- [V] Evaluation uses Lean 4.9.0-rc1 with 30,000 max tokens in the first round (§3.2). Self-correction SFT data was generated with DeepSeek-Prover-V2-671B on 144 H100s (§2.4).
- [P] At test time, a sub-goal repair variant uses `extract_goal` to isolate the failing sub-goal, solves it separately and splices the result back in. It improves the "amortized budget scaling curve by 1–2 percentage points" (§5). No table is given.
- [V] The flagship benchmark claim is 86 PutnamBench problems at pass@184 in self-correction mode. The abstract compares this with DeepSeek-Prover-V2's 47 at pass@1024 (Table 3).

## Verified quotes
> "Our flagship model, Goedel-Prover-V2-32B, achieves 88.1% on MiniF2F at pass@32 in standard mode and 90.4% in selfcorrection mode"

> "Adding self-correction provides a consistent gain of approximately 2 percentage points in pass@32 for both models on MiniF2F. On PutnamBench, error correction leads to 14 more solves under pass@32."

> "For the verifier-guided error-correction, we sequentially conduct 2 additional rounds of self-correction, given the verifier's feedback on the previous attempt. The total number of tokens in the self-correction mode is set to be 40,000."

> "For the first round of whole-proof generation, the max token length of the model is set to be 30,000."

> "32B (self-correction mode) 32B 8B (self-correction mode) 8B 90.4 88.1 86.7 84.6 91.4 89.8 86.9 86.1 91.9 90.5 87.4 86.5"

> "92.3 91.0 88.0 87.0 92.4 91.6 88.5 87.4 92.6 91.8 89.3 87.9 – 92.0 – 88.5 – 92.2 – 89.3 – 92.2 – 90.2"

> "we used YaRN (Peng et al., 2024) to extend the context length to 128k tokens and allowed up to 5 revision iterations"

> "the full self-correction model's pass@32 accuracy on MiniF2F reaches an average of 92.7%, which surpasses the 92.2% performance of the model without self-correction at pass@8192"

> "The results show that removing compiler feedback significantly lowers performance, confirming that specific error messages are crucial for effective revision. Similarly, removing the reasoning from previous attempts also slightly degrades performance"

> "50% of the inputs are used for whole proof generation, and the remaining 50% for first-round self-correction"

> "We train for a single epoch, using approximately 46K and 67K unique inputs for the 8B and 32B models, respectively."

> "During RL training, we consumed approximately 46K and 64K unique inputs for the 8B and 32B models on 1 epoch, respectively."

> "We adopt a batch size of 128 and n of 8 for parallel rollouts and reward function calls (via the Lean compiler)"

> "we set the over-sample batch size equal to three times of train batch size and filter out inputs with a pass rate equal to 0 or higher than 0.75"

> "we modify the dynamic sampling strategy to only include problems with pass rates in the range (0, 0.75] during optimization"

> "multi-turn approaches introduce various engineering challenges, especially on the rollout engine side, such as asynchronous generation"

> "This is reflected by an increase in pass@1 but a decline in pass@N for larger values of N, such as N=32."

> "For vanilla pass@N, performance stabilizes at higher RL steps, whereas in the correction setting, pass@N continues to improve."

> "the evaluations are done under Lean 4.9.0-rc1"

> "The selfcorrection data from Deepseek-Prover-V2-671B is inferenced using NeMo-Skills2 with 144 H100s."

> "On the MiniF2F benchmark, this approach improves the amortized budget scaling curve by 1–2 percentage points"

> "Under pass@184 and error correction, Goedel-Prover-V2-32B solves 86 on PutnamBench"

> "surpassing DeepSeekProver-V2-671B's record of solving 47 problems by pass@1024"

## Methods and evidence
- Data / setting: Lean 4.9.0-rc1. miniF2F-test (the Kimina-fixed version), PutnamBench (644), and the new MathOlympiadBench (360). Training statements come from Goedel-Pset plus a trained formalizer plus scaffolded synthesis. Base models are Qwen3-8B/32B.
- Baselines: DeepSeek-Prover-V2 7B/671B, Kimina-Prover 8B/72B, STP, Goedel-Prover-SFT (numbers mostly quoted from the respective papers).
- Evaluation: pass@N; ±std only at pass@32 in Table 2. There is no matched-verifier-call baseline for self-correction, and there are no seeds for RL. The self-correction ablation (Fig. 7) is given as a figure only.
- Artifacts: models, code and data released (github.com/Goedel-LM/Goedel-Prover-V2), plus the MathOlympiadBench benchmark.

## Limitations and caveats
- The self-correction gain is claimed at equal pass@k, where one "sample" holds up to 3 Lean calls and 4/3 of the tokens. At equal Lean calls, Table 4 shows ≈0–0.5 pp. The paper never makes this comparison. Only the 5-round/128k extension (Fig. 7) shows a clear matched-call win, and it comes without variance or token accounting.
- The ablation that matters most ("w/o Error Messages") has no reported numbers.
- There is no verifier infrastructure detail: no timeout, CPU budget, REPL reuse, or `sorry`/axiom checking.
- The unique-input count is inconsistent (67K vs 64K for 32B).
- The Fig. 10 training reward includes rollouts later filtered out by dynamic sampling (the authors state this).
- PutnamBench comparisons mix budgets (pass@184 vs pass@1024), which the paper states openly.

## Contradictions and tensions
- [[olausson2023self]]: agrees. Error-conditioned revision of a *trained* model buys little over i.i.d. resampling at matched verifier calls (Table 4, derived). The 5-round extension is the only matched-call win, and it is modest.
- [[gehring2024rlef]]: agrees in mechanism. Training on feedback (SFT on correction data plus RL on first-round correction prompts) makes the feedback useful, and removing the error text hurts (Fig. 7). But Goedel uses single-turn multi-task RL rather than RLEF's multi-turn PPO, and says multi-turn RL was too immature to use.
- [[xin2024deepseeka]]: same difficulty-filtering answer to sparse binary reward (pass rate in (0, 0.75]). Goedel adds an explicit report that RL lowers pass@N (diversity collapse) and needs weight averaging. This tempers DeepSeek's claim that RL gives a "genuine enhancement" stable across budgets.
- [[ji2025leanabell]]: this paper's related work groups Leanabell-V2 as a verifier-feedback refinement loop. Both find the main gain comes from the first revision round.

## Open questions
- What is the pass@k curve for self-correction when the x-axis is Lean calls or total tokens?
- What are the Fig. 7 numbers for "w/o Error Messages" at each iteration count?
- What verifier timeout and hardware were used during RL, and how are `sorry`/axioms rejected?
- Does the model-averaging trick transfer to diffusion or non-AR provers, or is it specific to RL-sharpened AR policies?

## Leads for next round
- term: "multi-task RL for self-correction" (single-turn, stored-error prompts); "model averaging / WiSE-FT for pass@N"; "scaffolded data synthesis"; `extract_goal` sub-goal repair; "Dr.GRPO"; "DAPO dynamic sampling".
- cited: Seed-Prover (Chen et al. 2025, arXiv:2507.23726); Kimina-Prover Preview (Wang et al. 2025, arXiv:2504.11354); DeepSeek-Prover-V2 (Ren et al. 2025, arXiv:2504.21801); Yue et al. 2025 "Does RL really incentivize reasoning capacity..." (arXiv:2504.13837), for plan row #5; Dang et al. 2025 "Assessing diversity collapse in reasoning"; Delta-Prover (Zhou et al. 2025, arXiv:2507.15225); Prover Agent (Baba et al. 2025, arXiv:2506.19923); ABEL (Gloeckle et al. 2024, online RL for neural theorem proving); VeRL/HybridFlow (Sheng et al. 2024).
- author: Chi Jin, Sanjeev Arora, Danqi Chen (Princeton PLI); Kaiyu Yang (LeanDojo).
