# yang2023leandojo — LeanDojo: Theorem Proving with Retrieval-Augmented Language Models

Kaiyu Yang, Aidan M. Swope, Alex Gu, Rahul Chalamala, Peiyang Song, Shixing Yu, Saad Godil, Ryan Prenger, Anima Anandkumar (Caltech, NVIDIA, MIT, UCSB, UT Austin)
NeurIPS 2023 (Datasets and Benchmarks Track) 2023 · arXiv:2306.15626 (v2, 27 Oct 2023) · `pdf/yang2023leandojo.pdf`

**Tier: T1**: peer-reviewed at NeurIPS 2023 in the Datasets & Benchmarks track (stated on p.1 of the archived text). The code, both datasets (on Zenodo, with DOIs) and the models are released. LeanDojo/ReProver has since become the standard open baseline and interaction toolkit in the field. Two weaknesses: the evaluation is single-run with no variance, and the headline pass@1 uses the easy `random` split.
**Relevance: 3**: RQ2 (data extraction, the gym interface, environment-construction correctness). It gives only indirect RQ3 timings: a 10-min wall limit per theorem and days of GPU evaluation. It does not report tactic latency or throughput.
**Read:** full text (main body plus Appendices A, C, D and F; skimmed B and E)

## Summary
LeanDojo is an open toolkit with two jobs. It extracts training data from Lean repos (file dependency DAG, ASTs, before/after tactic states, and premise definition/use locations with fully-qualified names), and it exposes Lean as a gym-like environment through `initialize(theorem)` and `run_tac(state, tactic)`. To get premise information, the authors patch Lean 3's elaborator to log name resolution. That patched Lean is used only for extraction, never for checking. For interaction, LeanDojo wraps its code as a tactic inserted at the proof's original location, so the proof environment (namespaces, opens) is exactly the human one. This cuts misjudged-correct proofs from 21.1% (lean-gym) to 1.4%. On top of this they build LeanDojo Benchmark (98,734 mathlib theorems, with a `novel_premises` split) and ReProver, a ByT5-small tactic generator with DPR premise retrieval over the accessible premises only. ReProver reaches 51.2% pass@1 on the random split and 26.3% on `novel_premises`.

## Key points
- [V] Environment correctness matters for RL. lean-gym misjudged 21.1% of correct human proofs as incorrect, and LeanDojo 1.4%; LeanDojo's failures are a subset of lean-gym's (§4, App. A.2).
- [V] The cause was namespace handling: lean-gym "opens" the namespace instead of being "inside" it, so short-name resolution picks the wrong constant. LeanDojo fixes this by injecting the interaction code as a tactic in place (App. A.2, A.3).
- [V] The authors state that noisy checker errors make the signal "too noisy as feedback signals for reinforcement learning" (App. A.2).
- [P] Gym interface: `initialize(theorem)` returns the initial state string, with multiple goals concatenated. `run_tac(state, tactic)` returns the next state or an error state (on timeout or an inapplicable tactic), and error states are absorbing. Only tactic-style proofs are supported (§4).
- [P] Data extraction relies on Lean's built-in exports (`lean --ast --tsast --tspp`) plus a git patch to the elaborator that records premise full names and definition locations. The patch applies to Lean 3 versions after 24 Mar 2022 (App. A.1, A.3).
- [V] Benchmark: 98,734 theorems from 3,384 files, 130,262 premises, 217,776 tactics (129,243 of them with ≥1 premise). The split is 94,734/2,000/2,000 (§4).
- [V] Program analysis restricts retrieval to accessible premises, cutting the candidate pool to 33,160 on average out of 130,262 (§5).
- [V] Pass@1 with a 10-minute wall limit: ReProver 51.2% vs no-retrieval 47.6% vs GPT-4 29.0% on `random`. On `novel_premises` the figures are 26.3% vs 23.2% (GPT-4 7.4%, tidy 5.3%) (Table 2, §1).
- [V] Compute: training takes 5 days on one A100-80GB. Evaluating the benchmark takes 2 days on 8 V100s, and one MiniF2F pass@1 evaluation takes a day (§6, App. C.4).
- [V] Lean 4: LeanDojo Benchmark 4 has 102,514 theorems, 213,067 tactics and 152,695 premises. ReProver scores 48.6/19.9 (random/novel) against 44.5/16.2 without retrieval (App. D, Table C).
- [V] MiniF2F test pass@1 is 26.5% and ProofNet 13.8% (§1, §6).
- [P] The authors concede that the model is trained only on human-written proofs, with no expert iteration or RL. Human proofs record only the final trajectory, not the trial and error (App. F).
- [P] With a 2,300-token input limit, only 10–15 retrieved premises fit into the generator (App. F). This bears on premise-conditioned provers such as SCMD's BASE.

## Verified quotes
> "37th Conference on Neural Information Processing Systems (NeurIPS 2023) Track on Datasets and Benchmarks."

> "LeanDojo is the first tool capable of interacting with Lean reliably, reducing proof-checking errors in existing tools [19] (correct proofs misjudged as incorrect) from 21.1% to 1.4%."

> "About 21.1% of the correct, human-written proofs are misjudged as incorrect, leading to two problems: First, it underestimates the prover's evaluation performance. Second, the results are too noisy as feedback signals for reinforcement learning."

> "These proofs are all correct, but lean-gym failed on 21.1% of them. In contrast, LeanDojo only failed on 1.4%, and its failures are a subset of lean-gym's."

> "Specifically, it wraps the interaction code as a Lean tactic, which is inserted into the proof. Therefore, the environment is guaranteed to be correct."

> "run_tac(state, tactic): Run a tactic on a given state and return the next state. The returned state will be an error state if the tactic execution is not successful, e.g., due to timeout or inapplicable tactic. If the input state is an error, the result can only be an error."

> "The modified Lean is used only for data extraction but not for evaluation, so we do not risk accidentally breaking Lean's logical soundness."

> "consisting of 98,734 theorems from 3,384 Lean files"

> "Furthermore, the dataset has 217,776 tactics, 129,243 of them with at least one premise."

> "LeanDojo Benchmark has 94,734/2,000/2,000 theorems for training/validation/testing."

> "LeanDojo Benchmark contains 130,262 premises in total, but the average number of accessible premises is only 33,160."

> "In evaluation, ReProver can prove 51.2% theorems, outperforming a baseline that generates tactics directly without retrieval (47.6%) and another baseline using GPT-4 [27] to generate tactics in a zero-shot manner (29.0%)."

> "5.3 7.4 26.3 23.2"

> "The prover is given only one attempt and must find the proof within a wall time limit of 10 minutes."

> "Training takes five days on a single NVIDIA A100 GPU with 80GB memory, and evaluation takes two days on eight V100 GPUs."

> "We use Pass@1, and it already takes one day for a single evaluation on MiniF2F's test set."

> "LeanDojo Benchmark 4 consists of 102,514 theorems/proofs, 213,067 tactics, and 152,695 premises."

> "48.6 44.5 19.9 16.2"

> "It can prove 26.5% theorems in MiniF2F and 13.8% in ProofNet"

> "With a length limit of 2,300 tokens, we can fit only 10–15 premises into the input of the tactic generator."

> "Second, theorem proving in proof assistants is an interactive process, but the proof only captures the final successful trajectory."

## Methods and evidence
- Data / setting: mathlib (Lean 3) at commit 19c869ef…; mathlib4 at commit 3ce43c18… for Benchmark 4. Two splits, `random` and `novel_premises`. Search is best-first over 64 beam-search tactic candidates per step.
- Baselines: tidy, zero-shot GPT-4 tactic generation (possibly contaminated), ReProver without retrieval, and BM25 for premise selection. The authors argue that no comparison with prior closed Lean provers (PACT, HTPS, lean-gym expert iteration) is feasible (App. C.3).
- Evaluation: pass@1 with a 10-min wall limit. Single run, no seeds or confidence intervals. The test sets hold 2,000 theorems each.
- Artifacts: code (github.com/lean-dojo/LeanDojo, ReProver), datasets on Zenodo (10.5281/zenodo.8016385 and 8040109), and models. MIT license.

## Limitations and caveats
- Conceded: supervised imitation only (no RL or expert iteration), a small ByT5 backbone, concatenation-based fusion limited to 10–15 premises, and generalisation out of mathlib is weak (App. F).
- Not conceded: the introduction headlines 51.2% on the `random` split even though the authors themselves argue that `novel_premises` (26.3%) "is more indicative". Retrieval's gain is +3.6 / +3.1 points from a single run with no variance, so its size is uncertain. The abstract has no numbers, so it does not overclaim, and `claims_exceed_evidence=false`.
- No interaction latency, tactics/s or memory figures are reported, so the paper is silent on RQ3 throughput. It never mentions Docker, which [[aniva2024pantograph]] cites as a LeanDojo dependency.
- The 1.4% residual error rate was measured on Lean v3.42.1 with an older mathlib. No equivalent check is reported for Lean 4.

## Contradictions and tensions
- [[aniva2024pantograph]] says LeanDojo needs external dependencies "such as Docker" and is slower, that LeanDojo cannot handle `have`, `conv` or `calc` incrementally, and that its separate extraction and execution units make it "impossible to extract an incomplete proof and resume from it". LeanDojo's own text makes no claim about speed or Docker either way, and Pantograph gives no measurement.
- [[shen2026keep]] and [[santos2025kimina]] treat per-proof Lean start-up and import cost as the RQ3 bottleneck. LeanDojo reports only coarse wall-clock figures (10 min/theorem, 2 days on 8 GPUs), so no per-tactic latency can be extracted from it for comparison.
- [[polu2022formal]] (round 2): LeanDojo's lead "25.9% → 29.6% MiniF2F with RL" matches Polu's Table 2 (θ1 → θ9full, miniF2F-test pass@1), but the method is verifier-filtered *expert iteration*, not RL. lean-gym's 21.1% false-negative rate means Polu's training loop discarded correct proofs and its reported rates are lower bounds.

## Open questions
- What is LeanDojo's per-`run_tac` latency and per-theorem start-up cost in Lean 4, and how does it compare with the REPL-based (Kimina, LeanInteract) or Pantograph back-ends?
- Is the 1.4% false-negative rate also reached in Lean 4, where environment construction differs?
- How much of ReProver's `novel_premises` gap is closed when the sufficient premise set is given (the SCMD BASE setting) rather than retrieved?

## Leads for next round
- term: "gym-like environment" for ITP; "accessible premises"; "in-file negatives"; "novel_premises split"; proof-checking false negatives / environment fidelity.
- cited: lean-gym (Polu et al. [19], "Formal mathematics statement curriculum learning", expert iteration, 25.9% → 29.6% MiniF2F with RL); HTPS (Lample et al. [17], HyperTree proof search, private tool, Pass@64); PACT (Han et al. [16]); CoqGym [9]; HOList [54]; PISA [15]; Magnushammer [49]; MiniF2F [28]; ProofNet [29].
- follow-ups: LeanDojo-v2 / LeanAgent (lifelong learning, Kaiyu Yang); Lean Copilot (Song, Yang, Anandkumar); ReProver used as a baseline in later work.
- author: Kaiyu Yang; Anima Anandkumar; Peiyang Song.
