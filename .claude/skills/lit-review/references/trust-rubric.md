# Trust rubric

Trust is graded at **two levels**, and they are kept apart on purpose:

1. **Source tier (T1–T5)** — how much weight the *work as a whole* deserves. Stored in
   `refs.jsonl` as `trust.tier`, with a one-line `trust.rationale`. Shown in `INDEX.md`.
2. **Claim grade** — how well a *specific statement* you intend to reuse is supported. Written
   next to the claim in the note (`[V]`, `[P]`, `[S]`, `[C]`, below).

A T1 paper can contain a `[P]` claim that is weaker than its headline, and a T3 preprint can carry
a `[V]` number you are entitled to reuse verbatim. Downstream prose cites claims, not tiers.

## Source tiers

`kb.py prior` computes a **metadata-only prior** (venue type, citations/year, retraction flag,
whether the identifier resolved). It is a *starting point*. The tier recorded after reading is
yours, and it must be justified by the factors below — write the deciding ones in `rationale`.

| tier | label | meaning | typical profile |
|---|---|---|---|
| **T1** | established | Reliable enough to build on without re-deriving it | Peer-reviewed at a recognised venue **and** independently reproduced, extended, or used as a baseline by others; methods and data sufficient to reproduce; no unresolved published critique |
| **T2** | peer-reviewed | Sound, but its results rest on its own evidence | Peer-reviewed, methods adequately described, claims proportionate to evidence; not yet independently confirmed |
| **T3** | credible preprint | Plausible and informative; do not lean a load-bearing argument on it alone | Unreviewed (arXiv etc.) but with concrete methods, released code/data, or authors with a track record in the area; or peer-reviewed with a notable methodological weakness |
| **T4** | weak | Useful as a lead or for context only | No method detail, tiny/uncontrolled evaluation, claims outrun the evidence, blog/white-paper/marketing, heavy undisclosed conflict of interest, or single-source numbers nobody else reports |
| **T5** | flagged | Do not cite as support | Retracted; identifier does not resolve; content does not match the citation that led to it; predatory venue; results contradicted by a stronger source; fabricated-looking references |

### Factors (record the ones that moved the tier as `factor.<name>`)

Raise:
- `peer_review` — published at a recognised venue (not just "accepted" on a personal page).
- `replicated` — another group reproduces the result, or it is a standard baseline.
- `artifacts` — code / data / models released and they match the paper.
- `evaluation` — strong baselines, ablations, variance / multiple seeds, held-out test.
- `consensus` — agrees with other T1/T2 sources in this KB.

Lower:
- `preprint_only`, `small_eval`, `no_baselines`, `cherry_picked` (single seed, best-of-N unreported).
- `claims_exceed_evidence` — the abstract says more than the tables show. **Check this every time;
  it is the most common defect.** Compare the abstract's headline number with the table it comes from.
- `conflict_of_interest` — the authors sell the thing being evaluated, undisclosed.
- `contradicted_by:<key>` — a stronger source in the KB disagrees. Write the tension into both notes.
- `secondary_only` — you could not read the primary text (paywall, no PDF); you read an abstract
  or someone else's summary. **Cap at T3** regardless of venue, and say so.

Hard overrides (always T5): `retracted`, `unresolved_identifier`, `citation_mismatch`
(the paper does not say what the citing source claimed it says), `predatory_venue`.

Citation counts are weak evidence. Use them only relative to age and field, and never to lift
a paper above what its methods earn. A heavily cited preprint is a strong *lead*, not a T1.

## Claim grades (inline in notes)

| grade | meaning | requirement |
|---|---|---|
| `[V]` verified | Verbatim quote or number, checked against the archived full text | In `## Verified quotes`, passes `kb.py verify-quotes` (or `✋` hand-checked against a named copy) |
| `[P]` paraphrase | Your summary of what the primary text says, read in full | Section / table / page locator given |
| `[S]` secondary | Known only from an abstract, a citing paper, or a summary | Name the secondary source. Never promote to a number you reuse. |
| `[C]` contested | Another source in the KB disputes it | Link the other key: `[C: vs smith2024foo]` |

A **number** that will be reused downstream must be `[V]`. Web-search snippets and model
summaries misreport constants and exponents often enough that no number is reused from one.
