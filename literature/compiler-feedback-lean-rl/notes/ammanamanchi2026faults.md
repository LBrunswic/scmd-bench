# ammanamanchi2026faults — Faults in Our Formal Benchmarking: Dataset Defects and Evaluation Failures in Lean Theorem Proving

Pawan Sasanka Ammanamanchi, Siddharth Bhat, Stella Biderman (EleutherAI; Cambridge)
ICML 2026 (PMLR 306, per the PDF header) · arXiv:2606.29493 · `pdf/ammanamanchi2026faults.pdf`

**Tier: T2**: peer-reviewed at ICML 2026 according to the PDF's proceedings header; the KB metadata still lists it as a preprint. The checkers (Lean metaprograms), prompts and corrected snapshots are released, and the authors include a Lean expert (Bhat). Two things hold it at T2. The score-impact evidence is small: 20 corrected problems, and a ProofNet# effect with no numbers. There are also internal count inconsistencies: 398 vs 399 proven issues, and 370 vs 427 ProverBench findings.
**Relevance: 3**: plan row #4 (evaluation loopholes that corrupt a verifier reward: the `apply?` bug, `native_decide`, axiom injection, `sorry`-as-axiom); benchmark-defect rates that would corrupt RL reward (RQ1).
**Read:** full text, including Appendices C–F and H.

## Summary
The paper argues that Lean benchmarks are not self-verifying. The kernel certifies only that a proof establishes the *formal* statement. It does not certify that the statement matches the informal problem, or that the harness resists trivial or adversarial proofs. The authors audit miniF2F, ProofNet, FormalMath, CombiBench and ProverBench across 13 variants (~10,000 problems), using static checkers written as Lean 4 metaprograms: counterexample, vacuity, unsound axiom, and totalization hazards such as division by zero and Nat subtraction. The checkers produce 4,833 findings, 398 of them with a machine-checkable certificate. They propose a taxonomy with three categories: fidelity, evaluation loopholes, and maintenance decay. They show that defects can deflate scores (unprovable items: 0/20 → 3/20 after correction) as well as inflate them (weakened statements). They recommend Comparator, patched Lean, `#print axioms`, a ban on `native_decide`, `proof_wanted` instead of `sorry`, and `autoImplicit false`.

## Key points
- [V] Corpus scale: 4,833 static-checker findings, of which 398 are mechanically certified (counterexamples, vacuous theorems, unsound axioms), across ~10,000 problems in 13 non-deduplicated variants (Abstract, Table 4).
- [V] The counts are not benchmark error rates: "should not be read as deduplicated benchmark-level error rates" (§4.1).
- [P] Internal inconsistencies. The Table 4 total and the abstract say 398 proven, but §4.1 text says 399. Table 4 lists 370 ProverBench findings, but §4.1 says LLM filtering reduces ProverBench findings "from 427 to 277" (§4.1, Table 4).
- [V] ProverBench (325 problems) has 208 proven issues, 199 of them in the Axiom column (Table 4). [P] The Unsound Axiom checker flags both `axiom` declarations and `sorry` in proofs (App. F), so this column may mostly count `sorry`-admitted helper statements shipped in the files. That is exactly the "sorry-as-axiom" loophole the paper warns about, but it is not necessarily 199 false statements.
- [V] Score effect on 20 problems with proven defects: both provers scored 0/20 on the originals. After correction, DeepSeek-Prover-V2-7B scored 3/20 and Kimina-Prover-8B 2/20 (§4.3). Repairing ProofNet's weakened statements (ProofNet#) "lowers measured pass rates", but no numbers are given (§4.3).
- [V] The `apply?` frontend bug in Lean < 4.20.0 let `apply?` "report success without producing a theorem declaration that had passed ordinary kernel verification". It appeared in at least three DeepSeek-Prover-V2 claimed proofs: 1 miniF2F and 2 PutnamBench, from the 7B model (§3.2, App. D). It was fixed by lean4 PR #8231.
- [V] Mechanism: `apply?` calls `admitGoal` without logging, which creates a synthetic sorry. A universe error then stops elaboration "before addDecl is reached", so no "declaration uses sorry" warning appears (App. D).
- [V] `native_decide` expands the trusted base to the compiler via `Lean.ofReduceBool`. Known codegen bugs "have produced proofs of False" (§3.2).
- [V] `sorry` in dataset files adds the statement as an axiom that any proof can cite. The recommended fix is `proof_wanted` (§5).
- [V] Recommendation: "incorporate maximally strict verification in RL reward signals". Comparator does not catch the `apply?` bug class, "which operated below the tactic layer" (§3.2).
- [P] The claim that "RL-trained provers will find and exploit any verification loophole" is asserted, not measured. The paper documents no RL run (§3.2).
- [V] LLM semantic audit on a labeled 92-problem set: high recall, low precision. Sonnet 4.5 + thinking reaches P 0.30 / R 0.82; GPT-5.2 + thinking P 0.24 / R 0.91 (Table 6).
- [P] The paper does not measure verification cost for any of the recommended checks.

## Verified quotes
> "using corpus-scale static checkers to surface 4,833 findings, including 398 mechanically certified issues such as counterexamples, vacuous theorems, and unsound axioms"

> "Running the static checkers over all released variants surfaces 4,833 findings and 399 proven issues (Table 4)."

> "These counts should not be read as deduplicated benchmark-level error rates"

> "On ProverBench, LLM filtering reduces findings from 427 to 277 (35% reduction) while preserving all confirmed true positives."

> "325 370 208 81 7 6 19 199 5"

> "10,318 4,833 398"

> "The original flawed statements were unprovable, and both evaluated models solved 0/20; after correction, DeepSeek-Prover-V2-7B solved 3/20 and Kimina-Prover8B solved 2/20."

> "repairing the weakened statements that distinguish ProofNet from its humancorrected counterpart ProofNet# (Poiroux et al., 2025) lowers measured pass rates for the provers we tested"

> "A bug in Lean versions prior to 4.20.0 allowed the apply? tactic to report success without producing a theorem declaration that had passed ordinary kernel verification"

> "This failure mode appeared in at least three proofs claimed by DeepSeek-Prover-V2 (Ren et al., 2025): one miniF2F solution and two PutnamBench solutions from the 7B model"

> "it stops before addDecl is reached"

> "known bugs in native code generation and implemented by overrides have produced proofs of False"

> "sorry adds the statement to the environment as an axiom, meaning any downstream code can reference it as a proven fact"

> "We recommend that evaluation harnesses use patched Lean versions, verify #print axioms output, and incorporate maximally strict verification in RL reward signals."

> "While comparator does not address all end-to-end trustworthiness issues (e.g. the apply? bug, which operated below the tactic layer)"

> "provers will find and exploit any verification loophole that increases reward."

> "0.82 0.42 68.1% $13.71"

> "0.91 0.37 54.6% $6.86"

> "PMLR 306, 2026"

## Methods and evidence
- Data / setting: 5 benchmarks and 13 variants (miniF2F ×7 forks, ProofNet and ProofNet#, FormalMath all/lite, ProverBench, CombiBench), about 10,318 problem rows.
- Method: static checkers written as Lean 4 metaprograms that try to discharge guards with omega, assumption and simp, and report only when that fails; an LLM false-positive filter on a 55-example labelled set; an LLM semantic audit on a 92-problem labelled challenge set (552 classifications).
- Evaluation: the corpus counts are not deduplicated. The score-impact experiment is 20 problems with 2 provers. The ProofNet# effect is stated without numbers. There are no seeds or variance.
- Artifacts: github.com/Shashi456/atp-checkers (checkers, harness, prompts, corrected snapshots).

## Limitations and caveats
- The authors concede this is not a complete human-verified enumeration. Semantic judgments need human adjudication.
- Not conceded: the abstract claims defects "both inflate and deflate reported prover scores" but gives numbers only for deflation (20 items). Inflation is asserted from ProofNet# without figures. The claim is mildly ahead of the evidence.
- Count inconsistencies (398/399; 370/427) suggest the numbers were not re-derived after a revision.
- The evaluation-loophole section is a survey plus the `apply?` case study. There is no new exploit measurement and no cost of strict checking.

## Contradictions and tensions
- Mechanism tension with [[vamshi2026reward]]. Here the `apply?` bug stops elaboration before `addDecl`, so the theorem is "never actually verified by the kernel". Vamshi's `#print axioms` finds the declarations present and depending on `sorryAx` under Lean 4.15.0. Both agree the bug predates 4.20.0 and evades the "declaration uses sorry" warning.
- Supports [[xin2026axle]] and [[kripner2025leantree]]: the verifier surface (frontend, not kernel) is where exploits live. It also adds a gap that AXLE's analysis does not cover: Comparator, the strictest (95.7 s) tier in AXLE, would *not* catch the `apply?` class according to this paper, because that bug sits below the tactic layer. The fix is a patched Lean (≥ 4.20), not a stricter checker.
- Refines [[kim2026process]]: "sorry is a warning" is the benign case. A synthetic sorry from `apply?` produced *no* warning on Lean < 4.20.
- Consistent with [[wang2026longcat]]: axiom injection and `sorry`-as-axiom appear in both loophole lists. This paper's list is predictive; LongCat's is observed in RL.
- Relevant to [[yang2023leandojo]]: a different axis of environment infidelity. LeanDojo measured false *rejections* (21.1%); here it is false-*accept* and specification defects.

## Open questions
- What is the deduplicated per-benchmark rate of certified-defective statements? This is needed to bound reward noise if these benchmarks are mined as RL prompts.
- How much does the inflation from weakened statements move the score on ProofNet vs ProofNet#?

## Leads for next round
- term: `proof_wanted`; `autoImplicit false`; `Lean.ofReduceBool`; trusted computing base; fork proliferation; specification fidelity.
- cited: comparator (github.com/leanprover/comparator); lean4 PR #8231 (`apply?` fix); miniF2F-v2 (Ospanov et al., 2025); ProofNet# (Poiroux et al., 2025, "Reliable evaluation and benchmarks for statement autoformalization"); Alexeev 2025 (Erdős #124 misformalization exploited by Aristotle).
- artifact: github.com/Shashi456/atp-checkers.
- author: Siddharth Bhat; Stella Biderman (EleutherAI).
