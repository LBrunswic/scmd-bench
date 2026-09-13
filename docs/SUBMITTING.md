# Submitting a result

## 1. Get the prompts

```bash
scmd-bench view --items data/v1/test.jsonl --track anon --k 64 > prompts.jsonl
```

Each line looks like this:

```json
{"item_id": "…", "track": "anon", "k": 64,
 "target": "theorem target (h : SemiconjBy x a b) (z : ℂ) : …",
 "base": [{"slot": 0, "name": "⟪p0⟫", "statement": "⟪p0⟫ {F : …} : …"}, …]}
```

These are the only fields a system may read. The item files also carry `grading`, `answer` and
`meta`. Those exist for the grader and the scorer, and reading them is a rules violation (RULES §2.2).

## 2. Write a submission

One JSON line per attempt, n = 64 attempts per item:

```json
{"item_id": "…", "sample_idx": 0, "proof": "by\n  rw [⟪p12⟫]\n  simp"}
```

`proof` is the text that follows `:=`. Nothing else is accepted: no `theorem` header, no imports,
no extra declarations. On the `anon` track, cite slot `i` as `⟪pI⟫`.

## 3. Grade and score with the released container

```bash
docker run --rm --network none -v $PWD:/work scmd-bench:1.0 \
  grade --items /work/data/v1/test.jsonl --submission /work/sub.jsonl \
        --track anon --k 64 --out /work/graded.jsonl --workers 8
docker run --rm --network none -v $PWD:/work scmd-bench:1.0 \
  score --items /work/data/v1/test.jsonl --graded /work/graded.jsonl --n 64 --k 64 \
        --out /work/score.json
```

Grading can be resumed: re-running `grade` only checks attempts that `--out` does not already
hold. If any attempt carries `fault: harness` (a wall-clock timeout or a crashed Lean process),
`score` refuses to produce a number. Re-run `grade` with `--regrade-harness` first.

Grading 2,000 items × 64 samples on 8 workers takes hours, not minutes. Most of the time goes to
building each item's file-prefix environment, and that cost is paid once per item, not once per
sample.

## 4. Open a pull request

Put these files in `results/<system-name>/`:

- `sub.jsonl.gz`
- `graded.jsonl.gz`
- `score.json`
- `system.json`

`system.json` looks like this:

```json
{"name": "…", "track": "anon", "k": 64, "n_samples": 64,
 "verifier_in_the_loop": false, "lean_checks_per_sample": 1,
 "parameters": "7B", "open_weights": true, "api": null,
 "training_data_cutoff": "2025-12", "trained_on_release": true,
 "hardware": "1x RTX 4090", "gpu_hours": 3.2, "temperature": 0.7, "seed": 0,
 "code": "https://…", "paper": null}
```
