# olausson2023self — Is Self-Repair a Silver Bullet for Code Generation?

Theo X. Olausson, Jeevana Priya Inala, Chenglong Wang, Jianfeng Gao, Armando Solar-Lezama (MIT CSAIL, Microsoft Research)
ICLR 2024 (the arXiv v5 header reads "Published as a conference paper at ICLR 2024"; refs.jsonl lists it as an arXiv preprint) · arXiv:2306.09896v5 · `pdf/olausson2023self.pdf`

**Tier: T1** (was T2; raised in round 2 after [[lin2025goedela]] confirmed the matched-budget result in Lean) — peer-reviewed at ICLR 2024, with code and data released. It evaluates carefully against a matched-budget i.i.d. baseline, including token-based variants (App. A), and it is cited and accepted as the reference dissent by [[gehring2024rlef]]. It is not T1 because variance comes from bootstrapping a single frozen repair tree per task, the APPS subset is small (300 tasks), the human study is tiny (40 programs, 16 people), and the headline models are frozen API endpoints.
**Relevance: 3** — RQ1, where feedback does *not* help: the matched-budget test for any verifier-in-the-loop repair claim.
**Read:** full text incl. appendices A and C, skimmed D–H

## Summary
Self-repair is decomposed into four stages: generate np programs, execute them on unit tests, generate nf textual feedback strings per failing program, and generate nr repairs. It is evaluated on HumanEval and 300 APPS tasks with CodeLlama-13b-instruct, GPT-3.5 and GPT-4. The budget is matched: a repair tree with np + np·nfr programs is compared with pass@k of i.i.d. samples at the same k. Gains are modest (at most about 8% relative for GPT-4 on APPS, about 10% for Code Llama on HumanEval), absent or negative at small budgets, and inconsistent across subsets. Spending budget on diverse initial samples beats spending it on more repairs. When the *feedback* comes from a stronger model or a human, repair improves markedly (human feedback 1.58× GPT-4's own on repair success). The authors conclude that the bottleneck is the model's ability to diagnose its own code, not the repair step.

## Key points
- [V] The execution signal is the error message: a compile/runtime error, or a counterexample input with expected vs actual output. A model-written feedback step is inserted because raw messages give "little signal for repair" (§3.1).
- [V] Matched-budget definition: a repair tree counts |programs(T)| = np + np·nfr samples and is compared against i.i.d. pass@k at k = |programs(T)|. Feedback tokens are **not** counted in the main body. App. A redoes everything with token-counted pass@t, both batched and sequential, and "the overall trends which we observe remain the same" (§3.2, App. A).
- [V] Main finding: gains are "often modest, vary a lot between subsets of the data, and are sometimes not present at all", especially at small budgets (Abstract, §4.1).
- [V] GPT-4 on APPS: 10 initial + 1 repair each is 1.05× pass@20, while 2 initial + 10 repairs each is 0.97× pass@22 (§1).
- [V] Heat-map extremes (normalized to the i.i.d. baseline): GPT-3.5 on APPS ranges from 0.83 (np=1, nfr=10) to 1.04. GPT-4 on APPS peaks at 1.08. The prose says "up to 8%" for GPT-4 on APPS, up to 10% for Code Llama on HumanEval, and up to 3% for GPT-3.5 on HumanEval (Fig. 3, §4.1).
- [V] Increasing np at fixed nfr consistently helps. Increasing nfr at fixed np "does not appear to be worth the additional cost". Diversity of initial samples matters more than the depth of repair (§4.1).
- [V] Gains are larger on harder problems. GPT-3.5 gains up to 34% relative on APPS competition-level problems (§4.1, App. C).
- [V] Stronger feedback model: every boosted configuration beats both the i.i.d. baseline and plain self-repair at every budget (§1, §4.2).
- [V] Human feedback raises GPT-4's repair success from 33.3% to 52.6% (1.58×). GPT-4's feedback is inaccurate in 32/80 cases vs 7/80 for humans, and GPT-4 never expresses uncertainty (0/80) (§4.3, Table 1).
- [V] Repair success rates are low in absolute terms. On APPS competition problems they are 0.1% (Code Llama), 1.5% (GPT-3.5) and 8.6% (GPT-4) (App. C, Table 2).
- [V] Sequential (depth-first) pass@t makes self-repair look *less* beneficial, especially when the baseline pass rate is already high (App. A.2).
- [P] The setup assumes access to the full test suite for both feedback and correctness (no public/private split), so the i.i.d. baseline effectively gets an oracle filter over k samples (§2). This is exactly the Lean situation, where the checker is the oracle.

## Verified quotes
> "We find that when the cost of carrying out repair is taken into account, performance gains are often modest, vary a lot between subsets of the data, and are sometimes not present at all."

> "whether self-repair is a winning strategy or not ultimately boils down to whether you would—at an equivalent compute budget—have had a greater chance of success if you had simply drawn more code samples i.i.d. from the model and checked them against the suite of unit tests"

> "drawing 10 samples up front and then 1 repair candidate each (up to 20 samples total) leads to a pass rate 1.05× higher than pass@20 from the same model without repair; drawing 2 samples up front and then drawing 10 repair candidates each (up to 22 samples total) leads to a pass rate which is lower than the baseline pass@22 (0.97×)."

> "in every case, the boosted configuration beats both the corresponding i.i.d. baseline and the corresponding self-repair configuration at all budgets."

> "increasing the fraction of repaired programs which pass the tests by a factor of 1.58× (from 33.3% to 52.6%)."

> "Error messages from the execution environment are usually very high-level, providing little signal for repair."

> "define the number of programs in the tree as |programs(T )| ≜ np + np nf r"

> "we then compare against a baseline with k = |programs(T )| i.i.d. samples."

> "Importantly, although the details differ, the overall trends which we observe remain the same."

> "this evaluation strategy does not account for the feedback tokens produced by the same model, which also come at a cost, and so risks overemphasizing the benefits of self-repair."

> "GPT-4, on the other hand, shows more significant improvements, beating out the baseline by up to 8%."

> "GPT-3.5 sees up to a 34% performance gain relative to the baseline on competition-level problems"

> "similar to those of GPT-4 on APPS for Code Llama (up to 10% improvement relative to the baseline), while gains for GPT-3.5 are limited as it approaches the ceiling (up to 3%)."

> "10 0.83 0.89 O.O.B. O.O.B. O.O.B. 5 0.85 0.90 0.96 O.O.B. O.O.B. 3 0.87 0.92 0.96 1.01 O.O.B. 1 0.91 0.95 0.98 1.00 1.04"

> "fixing np and increasing nf r (i.e., moving up along the y-axis on the heat maps) does not appear to be worth the additional cost incurred, giving marginal gains at higher budgets and oftentimes even decreasing performance at lower budgets."

> "In all cases, performance gains at smaller budgets are very marginal or non-existant, but grow somewhat as the budget increases."

> "GPT-4's feedback is much more likely to be inaccurate (32/80 vs. 7/80 for the human feedback)."

> "Our human participants sometimes express uncertainty (7/80); GPT-4 never does (0/80)."

> "We recruit 16 participants and collect a total of 2 human-written pieces of feedback for each of 40 failing programs sampled from GPT-4."

> "However, in this setting, self-repair appears to be somewhat less beneficial; especially when the baseline pass rate is already high."

> "0.1% 0.4% 1.5% 3.3% 8.6%"

> "unlike some prior work (Li et al., 2022; Shi et al., 2022), we do not make a distinction between public tests used for filtering and private tests used to determine correctness"

> "On APPS, in order to keep our experiments tractable, we evaluate on a randomly chosen set of 300 tasks."

## Methods and evidence
- Data / setting: HumanEval (164) and 300 APPS test tasks (180 interview, 60 competition, 60 introductory). Python. Temperature 0.8, one-shot templated prompts.
- Baselines: i.i.d. sampling from the same model at matched k (and, in App. A, matched tokens).
- Evaluation: for each task, one frozen large repair tree (Np=50, Nf=25, Nr=1), sub-sampled with replacement Nt=1000 times. The error bars are bootstrap std over sub-samples of that single tree, not independent draws, a risk the authors acknowledge in §5.
- Artifacts: code and data at github.com/theoxo/self-repair.

## Limitations and caveats
- Authors concede: the bootstrapped single tree may introduce statistical artefacts (mitigated by keeping np far below Np), the setting is self-contained Python with full tests, and the human study did not time participants.
- **Matched-budget argument, checked:** the main-body budget counts programs but not feedback tokens, which favours self-repair; the authors say so and redo the analysis with tokens in App. A. Neither accounting charges for *execution* calls, which are cheap for Python unit tests. For Lean, where a verifier call can dominate cost, i.i.d. sampling and repair both pay one check per program, so the program-count accounting is roughly fair per verifier call. It is not fair per token, because repair prompts carry the failed program plus the error.
- The i.i.d. baseline gets oracle filtering with the full test suite. That is the correct comparison for verifier-backed domains like Lean, but it does not transfer to settings with weak or partial tests.
- The models are frozen, inference-only prompting. The paper says nothing about models *trained* to use feedback, which is exactly the gap [[gehring2024rlef]] targets.
- The abstract's claims are hedged and match the figures, so `claims_exceed_evidence=false`.

## Contradictions and tensions
- [[gehring2024rlef]]: confirms Olausson's finding for untrained models at matched sample budget (Table 2: base Llama and gpt-4o do not gain from multi-turn) but shows RL training makes feedback use net-positive. The two are compatible. Olausson's dissent limits *prompted* self-repair and does not rule out *trained* repair. Gehring's random-feedback result also echoes Olausson's point that much of the gain is resampling diversity.
- [[wang2022compilable]]: compares a best-of-5 reranked system against top-1 baselines, which is exactly the unmatched-budget comparison this paper warns against.
- [[lin2025goedela]] (round 2): the Lean analogue confirms the matched-budget caution. Goedel-Prover-V2's self-correction "+2 pp at pass@32" is at matched sample count, but each sample has up to 3 Lean calls. At matched calls, Table 4 gives ≈0–0.5 pp (32B: 90.4 vs 90.5 at standard pass@128). Only a 5-round/128k-context extension shows a clear matched-call win (92.7 at pass@32 vs 92.2 at pass@8192), and that comes without token accounting or variance. [[ji2025leanabell]] also finds returns concentrated in the first repair round.
- [[le2022coderl]] (round 2): CodeRL's critic-sampling repair/refine regenerates N programs per extra round, yet it is reported at the same nominal pass@k as single-round baselines (17.78 → 20.98 pass@1000). That is the unmatched-budget comparison this paper warns against.

## Open questions
- Does the "feedback quality is the bottleneck" result carry over to Lean, where error messages (unsolved goals, type mismatch at a location) are much more informative than a Python counterexample?
- With RL-trained repair (as in RLEF), does the "more initial samples beat more repairs" allocation rule still hold?

## Leads for next round
- term: pass@t (token-matched pass rate); repair tree; batched vs sequential self-repair; feedback-model vs repair-model decomposition; matched-budget / compute-matched evaluation
- cited: Chen et al. 2023b Self-Debug (arXiv:2304.05128); Zhang et al. 2023 Self-Edit (arXiv:2305.04087); Le et al. 2022 CodeRL; Gupta et al. 2020 SED (Synthesize, Execute and Debug); Madaan et al. 2023 Self-Refine; Pan et al. 2023 self-correction survey (arXiv:2308.03188); Inala et al. 2022 fault-aware neural code rankers; Shi et al. 2022 MBR-exec; Mesbah et al. 2019 DeepDelta (learning to repair compilation errors)
- follow-ups to check: Kapoor et al. 2024 "AI Agents That Matter"; Huang et al. 2024 "LLMs cannot self-correct reasoning yet"; Lean-side analogues: whether proof repair with Lean error messages beats resampling at matched verifier calls (e.g. DeepSeek-Prover-V1.5, Baldur `first2023baldur` in the SCMD refs)
- author: Theo X. Olausson; Armando Solar-Lezama (MIT)
