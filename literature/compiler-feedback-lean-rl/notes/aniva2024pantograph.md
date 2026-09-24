# aniva2024pantograph — Pantograph: A Machine-to-Machine Interaction Interface for Advanced Theorem Proving, High Level Reasoning, and Data Extraction in Lean 4

Leni Aniva, Chuyue Sun, Brando Miranda, Clark Barrett, Sanmi Koyejo (Stanford)
TACAS 2025 (LNCS 15696, Springer, doi 10.1007/978-3-031-90643-5_6) 2025 · arXiv:2410.16429 (v2, 31 Jan 2025) · *no archived PDF: read `text/aniva2024pantograph.txt` (arXiv v2)*

**Tier: T3**: a peer-reviewed tool paper (TACAS 2025). The venue is **not** stated in the archived arXiv v2 text; it was confirmed by web search (Springer and ACM DL listings, chapter 10.1007/978-3-031-90643-5_6). The notable methodological weakness is that the abstract's "efficient proof search via … MCTS" and the related-work claim of better "speed of interaction" over LeanDojo carry no measurement at all. The only evaluation is a small untrained DSP demo on MiniF2F. The code is released (PyPantograph).
**Relevance: 3**: RQ2 (Lean interaction-tool design: goal-level state handling, metavariable coupling, sorry-extraction, frontend data extraction). For RQ3 it gives only per-benchmark DSP runtimes and states that pickling-based distribution is hard.
**Read:** full text (arXiv v2, about 15 pages including appendix; not 6)

## Summary
Pantograph is an API and REPL for Lean 4, written entirely in Lean with no external dependencies. It exposes three interfaces: Python (PyPantograph), a REPL executable, and a C FFI. It runs tactics by calling `Lean.Elab.Tactic.evalTactic` on stored goal states, and it lets the caller choose which goal to work on. That enables user-defined policies for MCTS or and-or tree search. It reports metavariable coupling explicitly, lets the user switch "automatic mode" off (sibling goals then become "dormant" and are brought back with `goal.continue`), and can partially execute `conv`/`calc`. It also supports `have`/`let`. `frontend.process` compiles a file and returns (before, after, tactic) triples, or turns every `sorry` into a goal. The evaluation is a Draft-Sketch-Prove pipeline: GPT-4o or o1-preview drafts and sketches, and aesop/simp/linarith close the holes. The best configuration proves 28.4% of MiniF2F test.

## Key points
- [V] Architecture: implemented entirely in Lean 4, with Python, REPL and C-FFI interfaces. Tactics run through `Elab.Tactic.evalTactic` (§4).
- [P] Positioned against LeanDojo: no Docker dependency and "improves the speed of interaction". **No timing measurement supports the speed claim** anywhere in the paper (§3).
- [P] Proof-state handling is goal-granular. When automatic mode is off, siblings become dormant and are resumed with `goal.continue`; coupled metavariables are reported to the user rather than resolved (§4.2–4.3).
- [P] Data extraction: `frontend.process` runs the Lean 4 compiler on a file and returns (goalBefore, goalAfter, tactic) triples with source positions. `env.inspect` and `goal.print` expose proof terms, optionally as S-expressions (§4.4–4.5).
- [P] Sorry-extraction turns every `sorry` in a draft into a goal with its local context, and type errors in a sketch are forwarded from the kernel (§4.6).
- [V] Limitation relevant to RQ3: distributing search via pickling is non-trivial, and merging two branches concluded on different machines is not handled (§4.7).
- [V] Maintenance cost: tight coupling to Lean internals means major Lean version changes need non-trivial engineering (§4.7).
- [V] DSP on MiniF2F with GPT-4o and 3 sketches reaches 28.4% on test and 23.6% on validation. With 1 sketch the figures are 14.7%/12.7% for 4o and 16.0%/10.9% for o1-preview (Table 2).
- [V] Mean runtime per benchmark ranges from 17.25 s (val, 1 sketch, 4o) to 88.38 s (test, o1). The authors attribute the bottleneck to LLM inference, not Lean (Table 2, §5).
- [V] Mean hammer invocations per problem are 4.17–7.93 (Table 2).

## Verified quotes
> "arXiv:2410.16429v2 [cs.LO] 31 Jan 2025"

> "First of all, it is written entirely in Lean 4. This removes the need for external dependencies (such as Docker) and also improves the speed of interaction."

> "Pantograph provides three interfaces: (i) a Python interface called PyPantograph; (ii) a REPL via the pantograph-repl executable; and (iii) a library via the C Foreign Function Interface (FFI)."

> "When the user executes a tactic, Pantograph calls the Lean 4 kernel's Elab.Tactic.evalTactic function."

> "However, LeanDojo's data extraction and proof execution units are essentially separate, which makes it impossible to extract an incomplete proof and resume from it, whereas Pantograph supports this use case."

> "The frontend.process command runs the Lean 4 compiler on a Lean 4 file, collects all tactics in the file, and returns them as a list of (before, after, tactic) triplets."

> "Moreover, due to the user-defined nature of tactics, distributing computation via pickling of objects in Pantograph is not trivial. For example, if two branches of a proof executing on two different machines are concluded, Pantograph does not handle the algorithmically difficult problem of uniting the two branches."

> "Due to the tight coupling of Pantograph with Lean's internals, nontrivial engineering effort is required to update Pantograph when Lean undergoes a major version change."

> "Dormant goals must either be tracked by the user or"

> "Pantograph provides explicit information about which goals are coupled."

> "12.7 10.9 23.6 14.7 16.0 28.4"

> "4.17 5.38 7.93 4.46 5.72 7.34"

> "17.25 73.23 23.98 28.39 88.38 36.41"

> "For this configuration, the DSP system out of the box successfully proved 28% of the theorems from MiniF2F [24]."

> "indicating that the main performance bottleneck is the inference of the GPT-4o model."

## Methods and evidence
- Data / setting: MiniF2F (Lean 4) validation and test splits. GPT-4o (1 or 3 sketches) and o1-preview (1 sketch), with max tokens 2048, top-p 0.95 and T=0.8. The hammers are aesop, simp and linarith.
- Baselines: none. No comparison with LeanDojo or the Lean REPL on speed or success, and no comparison with Isabelle DSP (the authors say the type systems differ).
- Evaluation: success rate, mean hammer invocations and mean runtime. Single run, no variance. MCTS and tree search are described but **never evaluated**.
- Artifacts: github.com/stanford-centaur/PyPantograph.

## Limitations and caveats
- Conceded: Lean-version coupling, difficulty with pickling and distribution, bugs in tactics that discard metavariables surface only at the end of the proof, and results are "not state of the art".
- Not conceded: the abstract says Pantograph "enables efficient proof search via powerful search algorithms such as Monte Carlo Tree Search", but no search experiment and no latency or throughput measurement is reported. §3's claim that it "improves the speed of interaction" over LeanDojo is likewise unmeasured. → `claims_exceed_evidence=true`.
- The "28%" headline in §5 is the test split with 3 sketches (28.4). Validation with the same configuration gives 23.6.
- The per-benchmark runtime folds together LLM API latency and hammer time, so no Lean-only verification cost can be read from it.

## Contradictions and tensions
- vs [[yang2023leandojo]]: Pantograph says LeanDojo requires Docker, is slower, cannot resume incomplete proofs, and cannot run `have`/`conv`/`calc` incrementally. LeanDojo's own paper neither claims nor measures speed, and it presents its interaction as tactic-level and reliable (1.4% false negatives). Neither side quantifies interaction latency, so the speed comparison is unresolved.
- vs [[shen2026keep]]: Pantograph's goal-state reuse is effectively in-process proof-state forking, but it reports no cost numbers. Shen's snapshot approach measures forking inside the LSP and does not run Pantograph as a baseline. Pantograph's own "pickling is not trivial" limitation is the distribution gap that REPL-pickle approaches (see [[santos2025kimina]]) target.

## Open questions
- What is Pantograph's per-tactic latency and memory per live goal state compared with Lean REPL `proofState` reuse or `pickleTo`?
- Can dormant-goal and coupled-metavariable handling survive across processes (for distributed MCTS workers)?
- How does sorry-extraction cost scale with file length, given that it runs the full frontend each time?

## Leads for next round
- term: "metavariable coupling"; "dormant goals"; "automatic mode"; "sorry-extraction"; "frontend.process"; "and-or tree"; machine-to-machine interface; "goal.continue".
- cited: Aesop (Limperg & From, CPP 2023) [13], a white-box best-first search that handles coupling by "copying"; HyperTree Proof Search (Lample et al.) [11]; Draft, Sketch, and Prove (Jiang et al., arXiv 2210.12283) [8]; Thor [9]; CoqGym [22]; lean-training-data (Kim Morrison, acknowledged).
- follow-ups found while verifying venue: ProofWala (arXiv 2502.04671); Nazrin (arXiv 2602.18767, a neural proof-automation tactic in Lean 4); Keep the Proof State Live (arXiv 2605.25556, already in KB as [[shen2026keep]]); an ICLR 2025 submission's supplementary material cites Pantograph (openreview P7NUVF6wo4, unidentified).
- author: Leni Aniva; Brando Miranda; Clark Barrett (Stanford Centaur).
