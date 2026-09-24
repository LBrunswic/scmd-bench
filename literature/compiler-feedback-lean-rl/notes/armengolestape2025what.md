# armengolestape2025what — What I cannot execute, I do not understand: Training and Evaluating LLMs on Program Execution Traces

Jordi Armengol-Estapé, Quentin Carbonneaux, Tianjun Zhang, Aram H. Markosyan, Volker Seeker, Chris Cummins, Melanie Kambadur, Michael F. P. O'Boyle, Sida Wang, Gabriel Synnaeve, Hugh Leather (Edinburgh; Meta AI)
arXiv 2025 · arXiv:2503.05703 (v1, dated 10 Feb 2025; header "Preprint") · `pdf/armengolestape2025what.pdf`

**Tier: T3**: an unreviewed preprint (web search found no venue). The methods are concrete and the controlled comparisons use one base model (Llama 3.1 8B). Weaknesses: single runs with no variance, a very small long-execution eval (9 inputs per task), an MBPP subset of fewer than 100 functions, and no released code or data.
**Relevance: 2**: RQ2 (can a learned model of execution substitute for execution, and how accurate is it: per-step vs compounded). It is the direct precursor of CWM's tracing data. It is not about Lean.
**Read:** full text

## Summary
Execution Tuning (E.T.) fine-tunes Llama 3.1 8B on Python execution traces. The corpus is about 300k real-world functions made executable with Llama-3-8B-generated unit tests and fuzzing, giving more than 1.5M executions, captured with a custom `sys.settrace` tracer that records locals, globals, stack and opcodes. The paper compares granularities (direct output, line-level, bytecode-instruction level) and scratchpad styles. Full-history scratchpad follows Nye et al.; compact diff scratchpad follows NExT; the new "dynamic scratchpad" is a single self-contained state updated each step, which can also skip N steps ahead. Per-step accuracy is very high (up to 98.8% full-state accuracy). Compounded output prediction reaches about 80% on CruxEval and on an MBPP nested-loop subset. Dynamic scratchpads can chain up to 14,055 correct steps on toy long-running programs. Adding traces to an SFT mix produces no conclusive downstream coding gain.

## Key points
- [V] Data scale: about 300k executable functions, about 6 inputs per function, more than 1.5M executions. No manual tests are needed (§2.1).
- [P] The tracer uses `sys.settrace` and captures call, line, opcode and return events. It steps into same-file auxiliary functions and deliberately ignores C events. Iterator states are recovered from the stack and encoded explicitly for dynamic scratchpads (§2.1–2.2).
- [V] Per-step (single state) accuracy on CruxEval after fine-tuning: Line-1 dynamic scratchpad 96.3% full state, Instruction-1 98.8%, and the Nye-style scratchpad 86.4%. Prompted, untrained Llama 3.1 8B reaches 10.6% (Table 1, §3.1).
- [V] Compounding error: per-step accuracy is far above whole-execution output accuracy, because "a single step error (out of, e.g., 20 steps) can lead to a wrong result" (§3.2).
- [V] CruxEval-O output accuracy: direct fine-tuning 49.3%, scratchpad 78.7%, compact scratchpad 79.7%, Line-1 73.3%, Instruction-1 73.5%. Prompted Llama 8B scores 37.8%, and GPT-4 on the leaderboard 82% (Table 2).
- [P] "+search" rows use Dijkstra over model predictions with access to ground truth, so they are an oracle upper bound and not comparable (Table 2 caption).
- [V] MBPP nested-loop subset (<100 functions): compact scratchpad with step-in 80.6%, Instruction-1 78.5%, direct output fine-tuning 47.3% (Table 3, §3.3).
- [V] Long executions: Line-1 chains 14,055 correct predictions for the binary counter at n=3038, and 619 for Collatz(3038). Each task has only 9 inputs (5 for Fibonacci) (§3.4, Table 4).
- [V] Line-n on Collatz reaches the same accuracy as Line-1 with 39% of the steps. Step-skipping by NLL fails on the binary counter (1/9) (§3.4, Table 4).
- [V] Downstream: E.T. in an SFT mix (Llama 3.1 8B base, 7.5k steps) gives "little coding improvement"; the best variant adds +1.2 on GSM8K. Forward-execution fine-tuning *worsens* Crux-I (§4, Table 5).
- [V] Conclusion: "no conclusive improvements on downstream coding benchmarks" (§6).
- [P] Failure modes are string indexing (tokenisation) and C-implemented string built-ins (e.g. `istitle`), which finer granularity cannot decompose (§3.2).

## Verified quotes
> "we gather about ∼300k executable functions, with an average of 6 inputs per function. Using automatically generated inputs allows us to scale the training dataset to > 1.5M executions, without requiring manually written unit tests."

> "We build a custom tracer leveraging Python's built-in"

> "We deliberately ignore C events because with"

> "Interestingly, we observe that the line-based dynamic scratchpad outperforms (96.3% full accuracy) its scratchpad counterpart (86.4% full state accuracy), and that the instruction-level obtains the highest full state accuracy, 98.8%."

> "while the out-of-the-box, prompted Llama shows non-trivial trace modeling capabilities (10.6% full state accuracy with the Line-1 approach)"

> "The reason why this happens is that when aggregating individual trace predictions, a single step error (out of, e.g., 20 steps) can lead to a wrong result."

> "49.3% 78.7% 79.7% 73.3% 60.8% 70.3% 73.5% 74.1% 62.5% 73.5% 37.8% 82%"

> "Out of the box, Llama 3.1 8B obtains an output prediction accuracy of 37.8%. This accuracy can be improved to 49.3% by fine tuning on direct output prediction."

> "47.3% 64.5% 77.4% 80.6% 73.1% 43% 59.1% 78.5% 80.6% 65.6% 88.2%"

> "leaving us with slightly fewer than 100 functions"

> "For correctly predicting the output for n = 3038, Line-1 has to chain as many as 14,055 correct predictions in a row."

> "For the largest input, n = 3038, Line-1 needs to chain 619 correct predictions in a row. Notably, Line-n is able to achieve the same accuracy but with only 39% of the steps required by Line-1."

> "For selecting the inputs, we generate 4 random numbers (as the small inputs) between 1 and 20, and 5 between 20 and 4000"

> "These results indicate that merging E.T. with SFT data offers little coding improvement."

> "Curiously, forward execution fine-tuning worsens Crux-I, and vice versa, suggesting weaker-than-expected ties between forward and backward prediction."

> "We saw no conclusive improvements on downstream coding benchmarks (5), where program state understanding might not be critical."

## Methods and evidence
- Data / setting: an unrestricted Python corpus. Inputs come from Llama 3 8B unit tests plus fuzzing, filtered for coverage and diversity. Models are fine-tuned from Llama 3.1 8B Instruct with comparable hyperparameters and 8192-token context.
- Baselines: direct output fine-tuning, a re-implemented Nye scratchpad, NExT-style compact scratchpad, prompted Llama 3.1 8B, and the GPT-4 CruxEval leaderboard figure.
- Evaluation: per-step accuracy (control flow, vars, iterators, stack, full), CruxEval-O, the MBPP nested-loop subset, and 3 toy long-execution tasks. Downstream: HumanEval, MBPP, GSM8K, Crux-I/O. Single run, no seeds or confidence intervals.
- Artifacts: none mentioned (no code, data or weights links in the text).

## Limitations and caveats
- Conceded: no downstream coding gain, failure modes on string indexing, and an MBPP nested-`for` iterator-tracing bug worked around with an AST rewrite to `while`.
- Not conceded: the long-execution claim ("up to 14k steps") rests on one input of one toy function, with 9 inputs per task. MBPP uses a subset of fewer than 100 functions. No variance is reported anywhere, so the 1–3-point differences between scratchpad variants (for example 78.7 vs 79.7) are within plausible noise.
- The abstract's "∼80% accuracy on CruxEval and MBPP" matches the best non-oracle rows (79.7% and 80.6%), and the abstract does not claim downstream gains ("we discuss E.T.'s practical applications"). → `claims_exceed_evidence=false`.
- For RQ2 (world model as a substitute for execution): per-step accuracy of 96–99% still compounds into about 73–80% whole-program accuracy on short CruxEval programs. A learned executor is therefore not a drop-in verifier replacement.

## Contradictions and tensions
- vs [[team2025cwm]]: consistent. In both, trace training lifts CruxEval but not downstream code generation (CWM 8B ablation: SBV 18.6 → 18.4 with tracing). CWM's full-trace CruxEval-O of 87.7% at 32B (and 88.0% greedy) exceeds E.T.'s 8B best of 79.7%. CWM's conclusion is more optimistic about downstream benefit than this paper's own evidence.
- [[jain2025r2e]] (round 2): a learned execution-free outcome judge for SWE patches reaches 71.82% accuracy and is swayed by the agent's own narration. That is the same ~70–80% band as this paper's whole-program accuracy, and it supports "filter, not substitute" for learned execution models.

## Open questions
- Does trace modelling help when the traces are provided as *input* (NExT-style repair) or used for verifier-guided repair, rather than as an output-prediction target?
- Would a dynamic-scratchpad analogue for Lean (predicting the next goal state rather than the history) be accurate enough to rank proof candidates before real verification?
- How do these results scale with model size? E.T. at 8B vs CWM at 32B suggests the gap narrows, but there is no controlled study.

## Leads for next round
- term: "execution tuning"; "dynamic scratchpad"; "compact scratchpad"; "learning to execute"; "neural program evaluation"; "output prediction" as a code-reasoning proxy; step-skipping by NLL.
- cited: Nye et al. 2021 (Show Your Work: scratchpads); Ni et al. 2024 (NExT: Naturalized Execution Tuning, traces in input improve repair); Ding et al. 2024 (SemCoder); Gehring et al. 2024 (RLEF: RL from execution feedback); Dong et al. 2024 (self-play with execution feedback); Gu et al. 2024 (CruxEval); Bieber et al. 2022 (runtime-error prediction); Zaremba & Sutskever 2014.
- author: Jordi Armengol-Estapé; Hugh Leather; Chris Cummins; Gabriel Synnaeve.
