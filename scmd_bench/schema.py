"""Items, submissions and verdicts. Frozen per benchmark version; a field change is a version bump.

THE OUTCOME ENUM IS CLOSED, AND FAULT IS ORTHOGONAL TO IT
--------------------------------------------------------
`Outcome` says what happened to the mathematics; `Fault` says whose it was. An infrastructure
failure that can be published as a model failure eventually is, so a `TIMEOUT` with
`fault=harness` is a row the grader owes a re-run, never a row the system lost. Only `SOLVED`
counts toward pass@k; every other verdict is a failure of the attempt, and `VOID`/harness faults
are reported separately so a leaderboard row can be audited.
"""

from __future__ import annotations

import dataclasses
import hashlib
import json
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Final, Iterable, Iterator

BENCHMARK: Final[str] = "scmd-bench"
VERSION: Final[str] = "1.0"
ITEM_SCHEMA: Final[str] = f"{BENCHMARK}/item/v1"

TRACKS: Final[tuple[str, ...]] = ("named", "anon")
KS: Final[tuple[int, ...]] = (64, 16)


class Outcome(str, Enum):
    #: elaborated in the item's prefix environment; no sorry; standard axioms; one declaration;
    #: every constant the proof NAMES is in BASE or the ambient theory.
    SOLVED = "solved"
    #: well-formed Lean that the elaborator rejected, or that left `sorry`.
    REJECTED = "rejected"
    #: does not parse.
    MALFORMED = "malformed"
    #: empty submission.
    ABSTAINED = "abstained"
    #: broke a rule of the frame: a named constant outside BASE, a forbidden token or option, a
    #: second declaration, a non-standard axiom, a real premise name on the anonymised track that
    #: no prompt text showed.
    ILLEGAL = "illegal"
    #: the deterministic heartbeat budget ran out (fault=model), or the harness's wall-clock guard
    #: fired (fault=harness -- re-run).
    TIMEOUT = "timeout"
    ERROR = "error"
    #: the ITEM could not be graded (its prefix environment failed). Never charged to a system.
    VOID = "void"

    @property
    def is_success(self) -> bool:
        return self is Outcome.SOLVED


class Fault(str, Enum):
    NONE = "none"
    MODEL = "model"
    HARNESS = "harness"
    ITEM = "item"


def item_id_of(prompt: dict[str, Any], grading: dict[str, Any]) -> str:
    """Content hash of what defines the QUESTION. A changed question cannot reuse an old id."""
    payload = json.dumps({"schema": ITEM_SCHEMA, "prompt": prompt, "grading": grading},
                         sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]


_LEFTOVER_HEAD = __import__("re").compile(
    r"^\s*(?:(?:private|protected|noncomputable|nonrec)\s+)*(?:theorem|lemma|def|abbrev|instance)\s+\S+")


def clean_rest(rest: str) -> str:
    """A premise's text after its name, with a leftover declaration head removed.

    About 1% of the corpus's SOURCE renderings (1,153 of 109,587 premises) still begin with the
    keyword and the short name -- ` lemma empty : Absorbs M s ∅` -- where the upstream renderer's
    cut missed. The name is already shown in front, so the head is dropped at DISPLAY time. The
    stored text, and therefore every `item_id`, is the corpus's own; `Item.view` and a system
    training on the release should both apply this function.
    """
    m = _LEFTOVER_HEAD.match(rest)
    return (" " + rest[m.end():].lstrip()) if m else rest


def placeholder(slot: int) -> str:
    """The anonymised track's name for slot `slot`. See `scmd_bench.placeholders`."""
    return f"⟪p{slot}⟫"            # ⟪p17⟫


@dataclass(frozen=True)
class Item:
    """One benchmark question.

    `prompt` is everything a system may read. `grading` is what the verifier needs (the target's
    file, offset and source signature); `answer` is the gold solution. Both are in the released
    file -- the gold proofs are public mathlib anyway -- and RULES.md forbids a system reading them.
    `Item.view(track, k)` is the only accessor a baseline adapter is handed.
    """

    item_id: str
    split: str
    prompt: dict[str, Any]
    grading: dict[str, Any]
    answer: dict[str, Any]
    meta: dict[str, Any] = field(default_factory=dict)
    schema: str = ITEM_SCHEMA

    @classmethod
    def from_json(cls, d: dict[str, Any]) -> Item:
        return cls(**{f.name: d[f.name] for f in dataclasses.fields(cls) if f.name in d})

    def to_json(self) -> dict[str, Any]:
        return dataclasses.asdict(self)

    def base(self, k: int) -> list[dict[str, str]]:
        return self.prompt["base"][str(k)]

    def view(self, track: str, k: int) -> dict[str, Any]:
        """What a system sees on `(track, k)`: the target and K premises. Nothing else.

        named: `{"slot": i, "name": "Finset.sum_comm", "statement": "Finset.sum_comm {β ...} : ..."}`
        anon:  `{"slot": i, "name": "⟪p7⟫",           "statement": "⟪p7⟫ {β ...} : ..."}`
        """
        if track not in TRACKS:
            raise ValueError(f"track must be one of {TRACKS}, got {track!r}")
        base = []
        for i, s in enumerate(self.base(k)):
            nm = s["name"] if track == "named" else placeholder(i)
            base.append({"slot": i, "name": nm, "statement": nm + clean_rest(s["rest"])})
        return {"item_id": self.item_id, "track": track, "k": k,
                "target": "theorem target " + self.prompt["target"].lstrip(), "base": base}


@dataclass
class Attempt:
    """One graded `(item, sample)`."""

    item_id: str
    sample_idx: int
    outcome: Outcome
    fault: Fault = Fault.NONE
    detail: str = ""
    #: `cited`: constants the proof named; `outside_base_named` (illegal), `reach_outside_base`
    #: (constants in the proof term outside BASE, reported and not enforced), axioms, timings.
    evidence: dict[str, Any] = field(default_factory=dict)
    verify_s: float = 0.0

    def to_json(self) -> dict[str, Any]:
        d = dataclasses.asdict(self)
        d["outcome"] = self.outcome.value
        d["fault"] = self.fault.value
        return d

    @classmethod
    def from_json(cls, d: dict[str, Any]) -> Attempt:
        d = dict(d)
        d["outcome"] = Outcome(d["outcome"])
        d["fault"] = Fault(d.get("fault", "none"))
        return cls(**d)


def read_jsonl(path: str | Path) -> Iterator[dict[str, Any]]:
    with Path(path).open(encoding="utf-8") as fh:
        for line in fh:
            if line.strip():
                yield json.loads(line)


def write_jsonl(path: str | Path, rows: Iterable[Any]) -> int:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    n = 0
    with p.open("w", encoding="utf-8") as fh:
        for r in rows:
            fh.write(json.dumps(r.to_json() if hasattr(r, "to_json") else r,
                                ensure_ascii=False, sort_keys=True) + "\n")
            n += 1
    return n


def load_items(path: str | Path) -> list[Item]:
    return [Item.from_json(d) for d in read_jsonl(path)]
