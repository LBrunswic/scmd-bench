# scmd-bench rules — version 1.0

These rules define what a scmd-bench number means. Any change to them bumps the version, and a
result is only comparable to results produced under the same version. Each rule names the
benchmark it was borrowed from, or the measured failure that made it necessary.

## 1. The task

A system is given:

- a **target**: a Lean 4 theorem signature taken from mathlib;
- **BASE**: K premise statements (K = 64 for the headline, or 16), each a true mathlib
  declaration.

It returns a **proof**: the Lean text that goes after `:=`.

BASE is *sufficient*. It contains every dependency the target's own mathlib proof names
(`gold_deps`), and the remaining slots are distractors.

Distractors come in three tiers, mixed 0.65 / 0.25 / 0.10:

- **retrieval-hard**: BM25 top-scoring non-dependencies;
- **sibling**: from the same module or namespace;
- **random**.

Slots are uniformly shuffled.

This is SCMD's own task. The draw is LeanDLLM's `scmd.data.assemble`, transcribed in
`scmd_bench/assemble.py` and parity-tested against the original 2,000 draws out of 2,000.

## 2. Data and splits

| file | rows | what |
|---|---|---|
| `train.jsonl.gz` (release asset) | 168,807 | corpus_v2 rows on the TRAIN side of all three splits |
| `data/v1/dev.jsonl` | 500 | frozen evaluation items; tune on these |
| `data/v1/test.jsonl` | 2,000 | frozen evaluation items; report on these |

**2.1 Held-out definition.** A row is held out if it is on the test side of *any* of three
splits:

- `file`: whole files held out;
- `temporal`: the newest ≈5% of files by creation date;
- `novel_premises`: targets citing a premise that is cited exactly once in the corpus. This is
  LeanDLLM's version of the LeanDojo Benchmark `novel_premises` split.

Evaluation items come only from held-out rows. Training rows come only from rows that are held
out by *none* of the three splits.

**2.2 Train only on the training side.** A system may be trained or tuned on:

- `train.jsonl.gz` and the other release assets;
- any mathlib source text **except the proofs of the 24,029 held-out declarations** listed in
  `heldout_decls.txt`;
- any data unrelated to mathlib.

Other declarations in the same files are fair game: the training release itself contains them,
because `temporal` and `novel_premises` hold out declarations, not whole files. Hyper-parameters
and prompts are selected on **dev**. Test is scored once per submitted system.

**2.3 Contamination is declared, not assumed away.**

- The pinned mathlib commit, `fabf563a` (2026-06-15), is public. The temporal split's cut is
  2026-03-24.
- Every submission declares its training-data cutoff. The leaderboard marks a system
  **exposed** if its pretraining corpus could contain mathlib after the cut, and **clean**
  otherwise.
- Exposed and clean results are shown in separate columns.
- A post-pin temporal test set is planned for v1.1. This follows miniCTX-v2 and SorryDB's
  dated snapshots.

**2.4 Near-duplicates.** An evaluation target whose statement has Jaccard ≥ 0.9 with any
training target was removed. That removed 66 of 17,763 eligible held-out rows.

**2.5 Evaluation BASE is drawn in-closure.** Distractors for evaluation items come only from
premises the target's module can actually name: its imports, followed through Lean's
module-system re-exports, plus premises declared above the target in its own file. A slot that
does not exist in the grading environment is a premise no proof could cite. The dataset card
reports how this shifts the tier mixture relative to SCMD's training draw.
`scmd_bench.assemble(..., allowed=...)` lets a system train on the same distribution.

## 3. Verification contract

Every attempt is graded by `scmd_bench.verify.Grader`, with no other judge involved. An attempt
is **SOLVED** only if all six of the following hold.

**3.1 Static rules.**

- Outside comments and strings, the proof must not contain:
  - `sorry`, `admit`, `native_decide`;
  - `unsafe`, `implemented_by`, `extern`;
  - `run_tac`, `run_cmd`, `run_elab`, `run_meta`, `#eval`, `#exit`, `#print`, `#check`;
  - `import`, `axiom`, `macro`, `syntax`, `elab`, `notation`, `attribute`, `initialize`.
- It must not use `set_option` for any budget, trust, kernel, debug, compiler, or
  implicit-argument option.
- Reason: `#print axioms` catches `sorryAx` and `Lean.ofReduceBool`. It does *not* catch
  `implemented_by` or a disabled kernel check. SafeVerify documents the same blind spot.

**3.2 Leak-free environment.**

- The declaration is `theorem <ns>.sb_target <signature> := <proof>`.
- It is elaborated after the target file's own text up to the target: imports, `variable`s,
  `open`s, and earlier declarations.
- mathlib's lakefile options apply: `autoImplicit false`, `maxSynthPendingDepth 3`.
- The target itself and everything after it in its file do not exist in that environment.
- Borrowed from miniCTX and VeriSoftBench.

**3.3 Clean elaboration.** No error, no `sorry`. The budget is mathlib's deterministic
`maxHeartbeats` (200,000), or whatever the declaration's own `set_option … in` wrapper sets.

**3.4 One declaration.** The command declares `…sb_target` and nothing follows it. This is
SorryDB's "no edits outside the proof".

**3.5 Standard axioms.** `#print axioms` lists only `propext`, `Classical.choice` and
`Quot.sound`.

**3.6 Admissibility.**

- Every **theorem** the proof *names* must be in BASE, or be ambient.
- A theorem is *named* when the proof's own source contains an identifier that elaborates to
  that constant and spells it.
- A theorem is *ambient* if it is:
  - defined outside `Mathlib.*` (Lean core, Batteries, Aesop, …);
  - private;
  - already named in the target's own signature.
- A theorem here means a constant whose type is a proposition. Definitions, structures,
  instances, and projections of structure or class fields (including Prop fields such as
  `Category.assoc`) are vocabulary, not premises.
- A named theorem outside BASE makes the attempt **ILLEGAL**.

**3.7 Anonymised track only.** A BASE premise must be cited by its placeholder `⟪pI⟫`. The
grader substitutes `_root_.<name>`. Naming a BASE theorem by a real name that no prompt text
showed is **ILLEGAL**.

**What the contract does not bind.** If every gold dependency a proof names is a *definition*,
removing those dependencies from BASE leaves the proof admissible. Definitions are vocabulary, so
BASE membership is not what that item tests. The grader runs the gold-removed control on every
released item and records `meta.base_binding`. On dev, 469 of 500 items are base-binding, and the
scorer reports the `premise_necessary & base_binding` subset beside the headline.

**What is reported but not forbidden.** A tactic may still *reach* lemmas without naming them:

- the default simp set (97,393 lemmas);
- instance search;
- `exact?`.

These are listed per attempt as `reach_outside_base`. Section 6's `premise_necessary` subset is
what keeps this reach from being scored as the task.

**Harness vs. system faults.** A wall-clock timeout (300 s) or a crashed Lean process is charged
to the **harness** and must be re-graded (`--regrade-harness`). It is never counted as a system
failure.

## 4. Tracks

| track | BASE names shown | the proof cites BASE by |
|---|---|---|
| `named` | real mathlib names | name |
| `anon` | `⟪p0⟫ … ⟪p63⟫` | placeholder |

- Each track is scored at K = 64 (headline) and K = 16.
- Targets with more than 16 gold dependencies have no K = 16 variant.
- `anon` is the default reading of the task. Names are not memorisable; only tactic names are.
  It removes the shortcut of recognising a mathlib lemma by name.
- `named` measures what a system that knows mathlib does with that knowledge.

A system may see BASE in any order it likes. The released order is the uniform shuffle. Premise
order is known to move LLM provers by more than 30% (`chen2024premiseorder`), so
order-sensitive systems should report a shuffled re-draw beside the released one.

## 5. Sampling budget

- **n = 64 samples per item** for leaderboard rows. Report pass@1, pass@8 and pass@32 with
  Codex's unbiased estimator (`n > k` is required).
- **Every proof checked by Lean during inference counts as a sample.** This includes repair
  rounds and self-verification loops.
  - A system that checks 4 repair rounds per draw and stops at the first success has used up to
    5 samples per draw.
  - It reports those 5 as samples. The released grader's verdict on the final submitted proof is
    what is scored.
- Declare in `system.json`:
  - parameters;
  - inference hardware and GPU-hours;
  - wall-clock time;
  - temperature;
  - seeds;
  - whether an external model API was used;
  - training-data cutoff.

Leaderboard columns are split by budget class: `n=64`, and `n=64 + verifier-in-the-loop`. This
answers PutnamBench's stated lack of budget standardisation.

## 6. Scoring and statistics

**6.1 Headline subset.** The headline is the `premise_necessary` subset: items that none of 16
zero-parameter proofs solves under the full contract. Those 16 are `rfl` and `by` followed by
`simp`, `aesop`, `decide`, `omega`, `norm_num`, `ring`, `positivity`, `linarith`, `simp_all`,
`simpa`, `tauto`, `field_simp`, `trivial`, `assumption`, or `exact?`.

This rule exists because of a measurement. On SCMD's own held-out targets that battery solved
26.5%, more than either model arm, and a margin read against an unmeasured floor is not the
number it looks like (LeanDLLM GAP-M7-007). The full-set score is always reported beside the
headline.

**6.2 Subsets reported.** All of the following are always reported:

- held-out split (`file`, `temporal`, `novel_premises`);
- |gold| bucket (1, 2–3, 4–8, 9+).

**6.3 Intervals.** 95% bootstrap intervals over items, 2,000 resamples, seed 0.

**6.4 Paired comparisons.** Compare systems with exact two-sided McNemar on per-item "solved in
any of n" over the same items (`scmd-bench compare`).

**6.5 Missing and void.** A missing sample is a failed sample. VOID items (the grader could not
build the environment) are excluded and counted.

## 7. Controls a result should report

The grader runs these for the baselines. Submissions are encouraged to report them too.

| control | what it shows |
|---|---|
| gold proof | harness validity: must be 1.0 on released items (it is, by construction) |
| ambient battery | the zero-parameter floor on the full set |
| BASE with gold premises removed | whether a system uses BASE or ignores it |
| BASE shuffled | order sensitivity |
| no BASE (target only) | what the system does without the premise set |

## 8. Submitting

A leaderboard entry provides:

- the submission JSONL;
- the grader's own `graded.jsonl` and `score.json`, produced by the released container;
- `system.json` (§5);
- a link to code or a preprint;
- open-weights / closed flag.

Self-computed scores are not accepted. See `docs/SUBMITTING.md`.
