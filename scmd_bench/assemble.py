"""The reference BASE assembler: how a training (or evaluation) instance's premise set is drawn.

A TRANSCRIPTION of LeanDLLM `scmd/data/{assemble,distractors}.py` and `scmd/common/rng.py` at
`3616c91`, stdlib-only, so a competing system can train on exactly the distribution SCMD trains on
without SCMD's tokenizer or code. `tests/fixtures/assemble_parity.json` records, for 2,000 corpus
rows, the BASE name list the upstream implementation drew; `test_assemble_parity` requires this
module to reproduce every one of them name-for-name and slot-for-slot.

WHAT A DRAW IS
--------------
For target `t` with gold dependencies `G` (|G| <= K):

  1. `K ~ U{8, 16, 32, 64}` from its own derived stream, raised to the smallest choice >= |G|
     (sufficiency is never truncated), unless `k` is given.
  2. `K - |G|` distractors mixed over three tiers at curriculum point `progress`:
     `random` (uniform over the premise universe), `sibling` (same module, else same namespace),
     `retrieval_hard` (the target's precomputed BM25 top-64 non-dependencies, k1=20, b=1).
     The integer remainder is allocated stochastically; a tier that runs short is redistributed
     hardest-first. No distractor is ever a gold dependency or the target.
  3. A uniform permutation of the K slots, from a third stream.

Everything is a pure function of `(seed, epoch, example_id)`. `example_id` is the row's POSITION in
the corpus (`decls.txt` has 9 duplicate names, so a name is not a key).

THE ONE ADDITION: `allowed`
---------------------------
Passing `allowed` restricts every tier to premises nameable in the target's environment -- its
module's import closure plus same-module premises declared above it. Evaluation items are drawn
this way (RULES.md section 2) because a slot that does not exist in the grading environment is a
premise no proof could cite. Training with `allowed` gives the matched distribution; without it,
SCMD's own. The two differ, and the dataset card reports by how much.
"""

from __future__ import annotations

import hashlib
import random
from dataclasses import dataclass, field
from typing import Final, Iterable, Mapping, Sequence

K_CHOICES: Final[tuple[int, ...]] = (8, 16, 32, 64)
DISTRACTOR_TIERS: Final[tuple[str, ...]] = ("random", "sibling", "retrieval_hard")
CURRICULUM_START: Final[tuple[float, ...]] = (0.70, 0.25, 0.05)
CURRICULUM_END: Final[tuple[float, ...]] = (0.10, 0.25, 0.65)
RANDOM, SIBLING, RETRIEVAL_HARD = DISTRACTOR_TIERS
MIN_SIBLING_POOL: Final[int] = 4

_DOMAIN: Final[bytes] = b"scmd/rng/v1"
_K_STREAM: Final[int] = 0x4b
_PERM_STREAM: Final[int] = 0x50


def derive(*parts: object) -> int:
    h = hashlib.blake2b(_DOMAIN, digest_size=8)
    for p in parts:
        h.update(b"\0")
        h.update(str(p).encode("utf-8"))
    return int.from_bytes(h.digest(), "big")


def example_seed(run_seed: int | str, epoch: int, example_id: int) -> int:
    return derive("example", run_seed, int(epoch), int(example_id))


def _check(weights: Sequence[float]) -> None:
    if len(weights) != 3 or any(w < 0 for w in weights) or abs(sum(weights) - 1.0) > 1e-9:
        raise ValueError(f"bad tier weights {tuple(weights)}")


def curriculum_weights(progress: float) -> tuple[float, ...]:
    if not 0.0 <= progress <= 1.0:
        raise ValueError(f"progress must be in [0, 1], got {progress!r}")
    if progress == 0.0:
        return CURRICULUM_START
    if progress == 1.0:
        return CURRICULUM_END
    raw = [a + (b - a) * progress for a, b in zip(CURRICULUM_START, CURRICULUM_END)]
    total = sum(raw)
    out = tuple(w / total for w in raw)
    _check(out)
    return out


def choose_k(seed: int, epoch: int, example_id: int) -> int:
    rng = random.Random(example_seed(seed, epoch, example_id * 2 + _K_STREAM))
    return int(rng.choice(list(K_CHOICES)))


def tier_counts(n: int, weights: Sequence[float], rng: random.Random) -> dict[str, int]:
    _check(weights)
    if n <= 0:
        return {t: 0 for t in DISTRACTOR_TIERS}
    exact = [n * float(w) for w in weights]
    base = [int(x) for x in exact]
    frac = [e - b for e, b in zip(exact, base)]
    for _ in range(n - sum(base)):
        total = sum(frac)
        if total <= 0.0:
            base[max(range(len(base)), key=lambda i: exact[i])] += 1
            continue
        x = rng.random() * total
        acc = 0.0
        for i in range(len(frac)):
            acc += frac[i]
            if x <= acc:
                base[i] += 1
                frac[i] = 0.0
                break
        else:
            i = max(range(len(frac)), key=lambda j: frac[j])
            base[i] += 1
            frac[i] = 0.0
    return dict(zip(DISTRACTOR_TIERS, base))


@dataclass(frozen=True)
class PremisePools:
    """The drawable universe, indexed by module and namespace. Build once; share read-only."""

    universe: tuple[str, ...]
    module_of: Mapping[str, str]
    by_module: Mapping[str, tuple[str, ...]]
    by_namespace: Mapping[str, tuple[str, ...]]

    @staticmethod
    def build(module_of: Mapping[str, str], *, drawable: Iterable[str] | None = None) -> PremisePools:
        """`module_of` may cover more names (targets) than are drawable (the premise universe)."""
        draw = set(module_of) if drawable is None else set(drawable)
        by_mod: dict[str, list[str]] = {}
        by_ns: dict[str, list[str]] = {}
        for name in sorted(draw):
            by_mod.setdefault(module_of.get(name, ""), []).append(name)
            ns = name.rpartition(".")[0]
            if ns:
                by_ns.setdefault(ns, []).append(name)
        return PremisePools(universe=tuple(sorted(draw)), module_of=dict(module_of),
                            by_module={k: tuple(v) for k, v in by_mod.items()},
                            by_namespace={k: tuple(v) for k, v in by_ns.items()})

    def restricted(self, allowed: set[str]) -> PremisePools:
        """The same pools with every name outside `allowed` removed, order preserved."""
        return PremisePools(
            universe=tuple(n for n in self.universe if n in allowed), module_of=self.module_of,
            by_module={m: t for m, v in self.by_module.items()
                       if (t := tuple(n for n in v if n in allowed))},
            by_namespace={m: t for m, v in self.by_namespace.items()
                          if (t := tuple(n for n in v if n in allowed))})

    def siblings_of(self, name: str) -> tuple[str, ...]:
        pool = self.by_module.get(self.module_of.get(name, ""), ())
        if len(pool) >= MIN_SIBLING_POOL:
            return pool
        ns = name.rpartition(".")[0]
        return self.by_namespace.get(ns, ()) or pool


def _take(pool: Sequence[str], k: int, *, banned: set[str],
          rng: random.Random) -> list[str]:
    # `random.sample` over the eligible list. Upstream uses an O(|banned|) view for the random tier
    # that is proven to consume the RNG identically; the list is the definition it is checked
    # against, so it is what is transcribed.
    eligible = [p for p in pool if p not in banned]
    if not eligible:
        return []
    if k >= len(eligible):
        return list(eligible)
    return rng.sample(eligible, k)


@dataclass
class Draw:
    names: list[str] = field(default_factory=list)
    tiers: list[str] = field(default_factory=list)


def draw_distractors(target: str, gold: Sequence[str], *, n: int, weights: Sequence[float],
                     pools: PremisePools, hard: Sequence[str], seed: int, epoch: int,
                     example_id: int) -> Draw:
    rng = random.Random(example_seed(seed, epoch, example_id))
    banned = {target, *gold}
    counts = tier_counts(n, weights, rng)
    got = Draw()

    def add(tier: str, names: Sequence[str]) -> None:
        for nm in names:
            if nm in banned:
                continue
            banned.add(nm)
            got.names.append(nm)
            got.tiers.append(tier)

    if counts[RETRIEVAL_HARD]:
        add(RETRIEVAL_HARD, _take(list(hard), counts[RETRIEVAL_HARD], banned=banned, rng=rng))
    if counts[SIBLING]:
        add(SIBLING, _take(pools.siblings_of(target), counts[SIBLING], banned=banned, rng=rng))
    if counts[RANDOM]:
        add(RANDOM, _take(pools.universe, counts[RANDOM], banned=banned, rng=rng))
    missing = n - len(got.names)
    for tier in (RETRIEVAL_HARD, SIBLING, RANDOM):          # redistribute hardest-first
        if missing <= 0:
            break
        pool = (list(hard) if tier == RETRIEVAL_HARD else
                pools.siblings_of(target) if tier == SIBLING else pools.universe)
        for nm in _take(pool, missing, banned=banned, rng=rng):
            if nm in banned:
                continue
            banned.add(nm)
            got.names.append(nm)
            got.tiers.append(tier)
            missing -= 1
    if set(got.names) & {target, *gold} or len(set(got.names)) != len(got.names):
        raise AssertionError(f"{target}: invalid distractor draw")
    return got


@dataclass
class Base:
    """One drawn BASE. `names[i]` is the premise in slot `i`; `tiers[i]` is `"gold"` or a tier."""

    k: int
    names: list[str]
    tiers: list[str]
    k_drawn: int

    @property
    def gold_slots(self) -> list[int]:
        return [i for i, t in enumerate(self.tiers) if t == "gold"]


def assemble_base(target: str, gold: Sequence[str], *, pools: PremisePools, hard: Sequence[str] = (),
                  progress: float = 0.0, seed: int = 0, epoch: int = 0, example_id: int = 0,
                  k: int | None = None, allowed: set[str] | None = None) -> Base:
    """The BASE for one corpus row. Identical to upstream `assemble(...)`'s `names`/`tiers`."""
    gold = list(gold)
    if k is None:
        k = choose_k(seed, epoch, example_id)
    drawn = k
    if len(gold) > k:
        bigger = [c for c in K_CHOICES if c >= len(gold)]
        if not bigger:
            raise ValueError(f"{target}: {len(gold)} gold dependencies exceed K_MAX=64")
        k = min(bigger)
    if allowed is not None:
        pools = pools.restricted(allowed)
        hard = [h for h in hard if h in allowed]
    d = draw_distractors(target, gold, n=k - len(gold), weights=curriculum_weights(progress),
                         pools=pools, hard=hard, seed=seed, epoch=epoch, example_id=example_id)
    real = gold + d.names
    tiers = ["gold"] * len(gold) + d.tiers
    perm = list(range(k))
    random.Random(example_seed(seed, epoch, example_id * 2 + _PERM_STREAM)).shuffle(perm)
    # A restricted pool can run dry: then fewer than K names exist and the slots past them are
    # simply absent. Never happens unrestricted (the universe is 100,853 names).
    slotted = [""] * k
    slotted_t = [""] * k
    for src, dst in enumerate(perm):
        if src < len(real):
            slotted[dst] = real[src]
            slotted_t[dst] = tiers[src]
    keep = [i for i in range(k) if slotted[i]]
    return Base(k=len(keep), names=[slotted[i] for i in keep],
                tiers=[slotted_t[i] for i in keep], k_drawn=drawn)
