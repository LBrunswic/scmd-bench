# chen2025seeda — Seed-Prover: Deep and Broad Reasoning for Automated Theorem Proving

Luoxin Chen, Jinming Gu, Liankai Huang, ... Thomas Hanwen Zhu (ByteDance Seed AI4Math)
arXiv 2025 · arXiv:2507.23726 (v2, 1 Aug 2025) · `pdf/chen2025seeda.pdf`

**Tier: T3**: an industry preprint from a strong group, with a public project page of proofs. The methods are described in prose, but there is no compute accounting. None of the Seed-Prover results report sample or verifier-call budgets, apart from the light-setting definition. There are no ablations and no matched-budget comparison with prior systems. The refinement-vs-pass@k efficiency claim rests on a single problem.
**Relevance: 3**: RQ1 (binary Lean reward RL with compiler feedback in the prompt; error-conditioned iterative refinement at test time), RQ2 (the LooKeng REPL interface design), and plan row #6.
**Read:** full text, including App. B (LooKeng)

## Summary
Seed-Prover is a whole-proof Lean 4 model trained with multi-stage VAPO RL on a binary proved/not-proved reward. It is "lemma-style": the model first emits `lemma`s and then the main `theorem`, so partial progress becomes visible and lemmas can be stored in a pool and reused across attempts. During RL, prompts are randomly augmented with failed attempts, summaries and Lean compiler feedback, so the model is *trained* to consume feedback. Test-time scaling has three tiers. **Light** runs Pass@8–16 with up to 8–16 feedback-conditioned refinements each. **Medium** adds an inner light-8×8 loop on failed lemmas. **Heavy** starts from about 5000 proposed conjectures, proves them with light, and feeds the top lemmas to medium, running for days. Results: 78.1% of 155 past IMO problems, 99.6% on miniF2F, 331/657 on PutnamBench, and 5/6 at IMO 2025 (one of them after the deadline). Seed-Geometry, a separate C++ forward-chaining engine, solves 43 of IMO-AG-50.

## Key points
- [V] Budget accounting for refinement. Light is Pass@8–16 with up to 8–16 refinements each. The paper writes a budget of Pass@n with up to m refinements as n × m and says light is "equivalent to" Pass@64–256. Light runs in 1–2 hours (§2.2.4).
- [V] **Plan #6, the exact claim.** The only direct refinement-vs-resampling comparison in the paper is one anecdote: IMO 2022 P2 is proved under light, "whereas without refinement, the same problem can only be proved in Pass@8192" (§2.2.4). **No table compares refinement with independent pass@k at matched verifier calls.** The "32–128×" figure quoted by [[wang2026learning]] does not appear in this text (v2). It can only be derived as 8192/256 = 32 and 8192/64 = 128 from this single problem. [P]
- [V] The nearest thing to an ablation: on PutnamBench, light gives 201/657 and medium gives 331/657 (§3.2). The medium budget is not reported, so this is not compute-matched.
- [V] The RL reward is binary (1 if proven, 0 otherwise), plus a formatting penalty that pushes the model to emit lemmas. Problems with proof rate above 1/4 are excluded from RL (§2.2.3).
- [V] RL prompts randomly include failed attempts, summaries and "Lean compiler feedback" (§2.2.3). The model is trained to use feedback, which is the RLEF-style regime ([[gehring2024rlef]]), not prompted repair ([[olausson2023self]]).
- [V] Observed refinement behaviours: the model "fixes Lean syntax errors in response to Lean compiler feedback" and it rewrites sketches, sometimes changing the whole trajectory (§2.2.4). [P]
- [V] Heavy setting: about 5000 conjectures by default, "days of thinking", and a lemma pool of "several thousand" facts (§2.2.4).
- [V] Headline results: 121/155 past IMO problems (78.1%), 99.6% miniF2F-test, 331/657 PutnamBench, 30% CombiBench, 81.8% MiniCTX-v2 (light, Lean v4.16.0). The default version is Lean v4.14.0 (§3.2, Table 3).
- [V] Infrastructure (App. B, LooKeng). The REPL-based Python interface has a "Stateless Design", in which any instance can process a Lean state. It offers "Memory Control" with user thresholds that kill processes, and it handles "thousands of concurrent requests" as a service. It supports infotree integration "to prevent false positive proofs". **No number is given for memory, latency, throughput, timeout, or CPU count.** [P]
- [P] Nothing in the paper measures Mathlib import cost, per-REPL memory, or verifier CPU-hours per RL step (plan #2 and #3: nothing found).
- [V] The IMO 2025 "5 out of 6" in the abstract includes Problem 1, which "was finished after the deadline". Table 3 reports 4/6 under competition conditions.

## Verified quotes
> "In the light setting, each proof attempt is refined up to 8–16 times and evaluated under Pass@8–16."

> "We denote the sample budget of Pass@n and up to m refinements as n × m, so the sample budget of the light setting is equivalent to generating the whole proof at Pass@64–256."

> "This setting completes in 1–2 hours."

> "whereas without refinement, the same problem can only be proved in Pass@8192"

> "Under the light inference setting only, Seed-Prover proved 201/657 problems from PutnamBench. Using the medium inference setting improved this performance to 331/657 problems."

> "using a light setting with an 8 × 8 budget to handle finer details"

> "The RL reward is 1 if the formal statement is successfully proven, and 0 otherwise."

> "We also exclude problems which are too easy (i.e. proof rate above 1/4) from RL training."

> "randomly incorporates natural language hints, natural language proofs, similar lemmas, proved lemmas, failed lemmas, failed attempts, summaries of previous attempts, and Lean compiler feedback into the prompt"

> "First, it fixes Lean syntax errors in response to Lean compiler feedback."

> "Initially, the proposer generates thousands of conjectures (by default 5000) to populate the conjecture pool."

> "After days of thinking, the lemma pool accumulates several thousand nontrivial math facts."

> "Seed-Prover successfully proves 121/155 problems, achieving an overall success rate of 78.1%."

> "Under the medium setting, we prove 99.6% problems on both MiniF2F-valid and MiniF2F-test."

> "Our system successfully achieved 81.8% of MiniCTX-v2"

> "Unless otherwise specified, we use Lean v4.14.0 with its corresponding Mathlib version."

> "Notably, the proof for Problem 1 was finished after the deadline."

> "Stateless Design: A Lean state can be simultaneously processed using different LooKeng instances, enabling effortless scaling and sharing."

> "Memory Control: Users can easily track the memory consumption of the Lean backend, set custom thresholds, and automatically terminate processes when memory usage exceeds the limit."

> "Multi-Concurrency Support: LooKeng can run as a service, handling thousands of concurrent requests via async architecture and resource isolation."

> "Complex tactics such as apply? and all_goals are fully supported, with enhanced infotree integration to prevent false positive proofs."

## Methods and evidence
- Data / setting: open-source RL sets (Big-Math, NuminaMath, Lean Workbook, DAPO, CriticLean) plus in-house formalizations. Past-IMO is a curated set of 155 problems (Compfiles and miniF2F, with human corrections). Lean v4.14.0 (v4.16.0 for MiniCTX-v2).
- Baselines: Table 3 compares with "Previous SOTA" numbers copied from other papers at unreported and unmatched budgets: DeepSeek-Prover-V2, Kimina-Prover, Goedel-Prover-V2, and o4-mini@8.
- Evaluation: success counts only. There are no seeds, no variance, and no compute or verifier-call totals for medium or heavy. The evaluation is adaptive: light first, then medium or heavy on the unsolved problems.
- Artifacts: a project page (GitHub ByteDance-Seed/Seed-Prover) with proofs. The model weights and LooKeng code are not evidenced in the paper.

## Limitations and caveats
- The authors concede that combinatorics remains weak (CombiBench 30%, IMO combinatorics 7/14).
- Not conceded: no experiment isolates refinement from budget. The "refinement beats pass@k" claim rests on a single problem (IMO 2022 P2). Light-vs-medium on PutnamBench confounds structure with budget.
- The abstract matches Table 3 on 78.1%, "saturates", and >50% PutnamBench (331/657 = 50.4%). The "5 out of 6" includes a post-deadline proof; Table 3 discloses this. `claims_exceed_evidence` is not set for the headline numbers. It *would* apply to any reuse of "32–128× more efficient", which the paper itself does not state.
- The comparisons with prior SOTA are not compute-matched ("up to 3×" in §1).

## Contradictions and tensions
- [[wang2026learning]] cites this paper as showing refinement is "32-128x more efficient than pass@k". That phrase is not in the v2 text. The numbers can only be derived from one problem (IMO 2022 P2: light Pass@64–256 vs Pass@8192), so the citation generalises an anecdote into a rate. This should be treated as a citation overstatement.
- [[olausson2023self]]: Seed-Prover does *not* contradict it at matched budget, because no matched-budget test is run. Seed-Prover's model is trained on compiler feedback in the prompt, so it belongs to the [[gehring2024rlef]] "trained repair" regime. It is consistent with that pair's joint conclusion, but it is not evidence for it.
- [[xin2024deepseeka]] filters RL prompts to medium difficulty. Seed-Prover similarly drops problems with proof rate > 1/4, which is convergent evidence that sparse binary Lean reward is managed by prompt filtering.
- [[achim2025aristotle]] and [[xin2026axle]]: LooKeng is also "stateless", like Aristotle's REPL service and AXLE's per-request sandbox. Three industrial Lean backends converge on stateless, request-carried state, against the stateful white-box designs ([[aniva2024pantograph]], [[kripner2025leantree]]).

## Open questions
- What is the success rate of light (n × m) against Pass@(n·m) on a whole benchmark, at the same number of Lean calls and tokens? Refinement prompts are longer, so the token budget is not matched by n × m either.
- How many Lean verifier calls and CPU-hours does a heavy run consume (5000 conjectures × light 8–16 × 8–16)?
- What memory thresholds does LooKeng use in practice, and what is its per-REPL RSS?

## Leads for next round
- term: lemma-style proving; conjecture pool / lemma pool; n × m refinement budget; self-summarization; inner/outer refinement; LooKeng; infotree-based false-positive prevention.
- cited: [32] Zhou et al. 2025, "Solving formal math problems by decomposition and iterative reflection" (Delta-Prover, arXiv:2507.15225), the cited source for refinement with Lean feedback. [29] VAPO (arXiv:2504.05118). [9] Goedel-Prover (and V2, with self-correction). [15] DeepSeek-Prover-V2. Seed-Prover 1.5 / later versions may carry the missing ablation.
- author: Huajian Xin, Yichi Zhou, Jianqiu Zhao (infra), Thomas Hanwen Zhu.
