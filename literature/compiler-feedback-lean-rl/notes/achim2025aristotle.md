# achim2025aristotle — Aristotle: IMO-level Automated Theorem Proving

Tudor Achim, Alex J. Best, Alberto Bietti, ... Vlad Tenev, ... Lingfeng Wu (The Harmonic Team)
arXiv 2025 · arXiv:2510.01346 · `pdf/achim2025aristotle.pdf`

**Tier: T4**: an industry preprint from a company that sells access to the system. The only quantitative evaluation is 5 of the 6 IMO 2025 problems (the formal proofs are public, so the result itself is checkable). The abstract claims "state-of-the-art performance with favorable scaling properties", but the paper contains no benchmark table, scaling curve, budget, or ablation. The method is described qualitatively, and no infrastructure numbers are given. Useful for mechanism leads only.
**Relevance: 2**: RQ2/RQ3 (a stateless, horizontally scaled REPL service with request-carried state; stricter-than-kernel checks), RQ1 (expert iteration on search traces; test-time training; lemma iteration from Lean error messages). Gives no numbers for plan rows #2/#3.
**Read:** full text including appendices B–D

## Summary
Aristotle has three parts. The first is a Monte Carlo Graph Search over Lean tactic states, with one >200B-parameter model serving as both policy and value, conditioned on proof state, action history and optional informal proof. The second is a lemma pipeline: an informal proof is split into lemmas and each lemma statement is formalized. Lean REPL error messages are fed back for correction, and failed attempts are revised using proved/unproved annotations. The third is Yuclid, a C++ geometry DD/AR engine. Training is expert iteration: the policy learns from search-found proofs filtered for nontriviality, and the value function learns from proven, disproven and unproven states. During deployment, test-time training retrains the model on its own search traces. The Lean backend is a REPL fleet on CPU-only GKE machines. It is stateless, because each request carries everything needed to reconstruct the state. Final proofs are re-checked as standalone files for kernel errors and axioms. The result is formal solutions to IMO 2025 P1–P5.

## Key points
- [V] Infrastructure mechanism: the REPL runs on "many CPU-only machines, which operate in a stateless manner". Any process can apply a tactic at any state because "all the information required to reconstruct the state is contained within the request". The fleet runs on GKE with autoscaling and per-request routing (App. B). How the state is encoded (replayed code, pickled environment, or something else) is not described. [P]
- [P] **Plan #2/#3: nothing found.** There is no import time, memory per REPL, core count, timeout, latency or throughput. Details are deferred to a blog post, "[16] Harmonic. Running Lean at Scale" (11 Sep 2025).
- [V] Soundness checks: a found proof is rendered as a self-contained Lean file and run "to check for kernel errors, check which axioms are used". The REPL also applies "more stringent checks to ensure that the proof terms produced by tactics are well typed", which catches errors eagerly before the kernel does (App. B). `sorryAx` and unsound axioms are excluded from "solved" (§1).
- [V] Search state equivalence: states count as equal if goals, local context and variable names are equal. Aesop is a known counterexample because it "uses global state internally". Equivalence turns the tree into a graph, and "we do not observe any CPU bottleneck" (§2.1.2).
- [V] Each single-goal state gets a negation transition, so search can disprove as well as prove (§2.1.3).
- [P] RL is expert iteration: the policy is trained on search-found proofs filtered for nontriviality, and the value function on proven and hard-unproven states. There is also hindsight relabelling of subgoals as root theorems (§2.1.6). No reward curve or ablation is given.
- [V] Lean-feedback repair is used for *statements*, not proofs: lemma formalizations are sent to the REPL and error messages are returned "and ask for corrections". The loop is iterated "multiple times ... to maximize the potential for error correction" at IMO (§2.2.1, §3.1). No budget or gain is reported.
- [V] Test-time training "allowed Aristotle to solve ... problems that were unsolved by our base model at the same search budget" (§2.1.7). This is anecdotal: no count and no budget.
- [V] Scale: a model "having over 200B parameters" (§3.1). Yuclid solves 17/30 of AG-30 and saturates the rest in "about 0.4s while running on a single 3.1GHz core" (§2.3.1).
- [V] Result: a formally verified solution "for all but the final problem" at IMO 2025 (§3.1). Aristotle also found four false exercises in Tao's Lean analysis textbook (§3.2).
- [P] The abstract's "state-of-the-art performance with favorable scaling properties" has no supporting table or figure anywhere in the paper (miniF2F and PutnamBench are cited but never evaluated) → `claims_exceed_evidence`.

## Verified quotes
> "The REPL is hosted on many CPU-only machines, which operate in a stateless manner."

> "Any REPL process can be asked to apply a tactic at some state at any time, as all the information required to reconstruct the state is contained within the request."

> "The machines are hosted in GKE which can be scaled up and down depending on demand and can be routed to on a per-request basis."

> "When a proof is found via the search process, it is verified by rendering the proof out as a self contained Lean file and running it through Lean as a command in order to check for kernel errors, check which axioms are used, and check which lemmas from the file were necessary in order to complete the proof."

> "The REPL also allows us to apply more stringent checks to ensure that the proof terms produced by tactics are well typed."

> "[16] Harmonic. Running Lean at Scale. Blog post, September 11, 2025."

> "we only consider a problem to be solved if our system produces a complete proof using the Lean 4 proof language and its mathematical library Mathlib, without gaps or unsound axioms like sorryAx."

> "We consider Lean states to be equivalent if they are equal in goal expressions, local context expressions, and local variable names."

> "a common counterexample is the aesop tactic, which uses global state internally"

> "we do not observe any CPU bottleneck in our implementation for graphs that arise in practice."

> "we augment each single-goal state with a state transition corresponding to the logical negation of that goal"

> "We train the generative policy on proofs found by search, filtered by measures of nontriviality."

> "Prior to the IMO, we found that using TTT allowed Aristotle to solve ... problems that were unsolved by our base model at the same search budget."

> "Finally, after sending the formalizations from (3) to the Lean REPL, we communicate any error messages back and ask for corrections."

> "Iterating the formal feedback loop of this pipeline multiple times on individual instances to maximize the potential for error correction."

> "Running our search algorithm with a model having over 200B parameters."

> "in about 0.4s while running on a single 3.1GHz core."

> "Aristotle produced a formally verified solution for all but the final problem"

> "demonstrates state-of-the-art performance with favorable scaling properties for automated theorem proving."

> "Upon processing a few chapters from the book, Aristotle discovered four exercises which were false as written"

## Methods and evidence
- Data / setting: "open-source collections and in-house data", with a statement autoformalization system judged "using signals from the Lean REPL". IMO 2025 statements were formalized by hand.
- Baselines: none. The comparison with Seed-Prover and others is qualitative (§4).
- Evaluation: IMO 2025, 5/6, plus anecdotes (Mathlib contributions, the Tao textbook). No benchmark, seeds, budget or compute figures.
- Artifacts: the IMO 2025 Lean proofs (GitHub harmonic-ai/IMO2025) and Yuclid (Apache 2.0). The prover, the REPL service code and the weights are not released; access is a commercial early-access product.

## Limitations and caveats
- Conceded: lemma formalization is "a noisy process" with gaps and misformalizations even after error correction. State equivalence is unsound for tactics that use global state (aesop).
- Not conceded: no quantitative evidence for SOTA or scaling claims; the authors have a commercial interest (early-access product); no infrastructure numbers despite a stateless-service design that is directly relevant.

## Contradictions and tensions
- [[xin2026axle]] and [[chen2025seeda]] (LooKeng): all three industrial Lean backends are stateless, with state carried in or reconstructed from the request. This goes against the stateful, white-box REPL sessions of [[aniva2024pantograph]] and [[kripner2025leantree]], and the in-process snapshot forking proposed by [[shen2026keep]]. No paper in the KB yet measures the reconstruction cost that statelessness pays per request.
- [[kripner2025leantree]] documented the REPL tactic mode accepting wrong proofs. Aristotle's extra well-typedness checks plus a final whole-file re-check are the same defence (re-verify the final artifact), stated without numbers.
- [[chen2025seeda]]: the authors themselves contrast Seed-Prover's whole-proof refinement with their own step-wise search. Neither reports a matched-budget comparison.
- [[xin2024deepseeka]]: both use search plus expert iteration. Aristotle uses a single policy/value model (DeepSeek uses no value model; RMaxTS uses an intrinsic reward).

## Open questions
- How is Lean state encoded in a request (replayed prefix? `pickleTo` bytes?), and what does reconstruction cost per tactic call?
- How many REPL machines and cores, and what per-call latency, support MCGS with a >200B policy?
- How much does test-time training gain at matched budget?

## Leads for next round
- term: Monte Carlo Graph Search (MCGS); stateless REPL; request-carried state; progressive widening; hypertree AND/OR; test-time training (TTT); hindsight experience replay for subgoals; negation transitions.
- cited: [16] Harmonic, "Running Lean at Scale" blog (11 Sep 2025), **the primary lead for plan #2/#3**; [44] leanprover-community/repl (base of their REPL); [20] HyperTree Proof Search; [8, 50] MCGS literature; [1] test-time training; [11] ABEL.
- author: Alex J. Best, Yury Kudryashov, Aidan Swope (also a LeanDojo author), Harmonic.
