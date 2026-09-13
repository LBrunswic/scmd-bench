"""pass@k -- Codex's unbiased estimator, with `n > k` required at the call.

PORTED FROM LeanDLLM `scmd/eval/passk.py`, whose transcription is checked against exhaustive
enumeration at 1.0 over all 638 `(n, c, k)` with n <= 12. scmd-bench imports nothing from `scmd`, so
the estimator is reproduced here; `tests/test_offline.py` re-derives it against its own independent
enumeration rather than trusting the port.

`chen2021codex` §2, the definition:

    pass@k := E_problems [ 1 - C(n-c, k) / C(n, k) ]

computed as Figure 3's term-by-term product, not the binomial ratio -- the paper's own reason is
that "calculating this estimator directly results in very large numbers and numerical instability".

WHY `n == k` RAISES, AND WHY CODEX IS NOT THE REASON
----------------------------------------------------
Codex requires `n >= k` and does NOT call the `n = k` value biased -- its Appendix A calls the
empirical "solved if any of k passes" estimate unbiased. The objection is VARIANCE: at `n = k` the
expression degenerates to an indicator, so the problem contributes 0 or 1 and nothing about the
sampling distribution. A mean of indicators is the highest-variance unbiased estimate available.
Refusing it here is this benchmark's decision on those grounds, not a claim about the paper. The value
stays reachable through `pass_at_k_naive`, which returns a labelled object rather than a float so it
cannot be spent as a pass@k by assigning it to the wrong variable.
"""

from __future__ import annotations

import itertools
from dataclasses import dataclass
from math import comb
from typing import Final, Sequence

#: `pass_at_k_bruteforce` refuses above this: C(12,6) = 924 subsets is instant, C(64,32) = 1.8e18 is
#: not, and the failure mode of allowing it is a test that never returns rather than one that fails.
BRUTEFORCE_N_MAX: Final[int] = 12


class PassAtKError(ValueError):
    """Raised when pass@k is asked for a number it cannot honestly produce."""


@dataclass(frozen=True)
class NaiveEstimate:
    """The `n == k` value, deliberately not a float. See the module docstring."""

    value: float
    n: int
    c: int
    k: int


def _validate(n: int, c: int, k: int) -> None:
    for name, v in (("n", n), ("c", c), ("k", k)):
        # Type first: `pass_at_k(64, 0.5, 1)` must not produce a plausible float by coercion.
        if isinstance(v, bool) or not isinstance(v, int):
            raise PassAtKError(f"{name} must be an int, got {v!r} ({type(v).__name__})")
    if n < 1:
        raise PassAtKError(f"n must be >= 1, got {n}: pass@k over zero samples is not a number")
    if k < 1:
        raise PassAtKError(f"k must be >= 1, got {k}")
    if not 0 <= c <= n:
        raise PassAtKError(f"c must satisfy 0 <= c <= n, got c={c}, n={n}")


def pass_at_k(n: int, c: int, k: int) -> float:
    """Codex Figure 3's product. Requires `n > k` -- see the module docstring for why."""
    _validate(n, c, k)
    if n <= k:
        raise PassAtKError(
            f"pass@{k} needs n > k; got n={n}. At n = k the estimate is an indicator carrying no "
            f"information about the sampling distribution, and a benchmark mean of indicators is "
            f"the highest-variance unbiased estimate available. Draw more samples, or call "
            f"pass_at_k_naive() for a labelled value that cannot be spent as a pass@k.")
    if n - c < k:
        return 1.0
    out = 1.0
    for i in range(n - c + 1, n + 1):
        out *= 1.0 - k / i
    return 1.0 - out


def pass_at_k_naive(n: int, c: int, k: int) -> NaiveEstimate:
    """The `n == k` degenerate value, labelled so it cannot be mistaken for `pass_at_k`."""
    _validate(n, c, k)
    return NaiveEstimate(1.0 if c >= 1 else 0.0, n, c, k)


def pass_at_k_bruteforce(n: int, c: int, k: int) -> float:
    """Enumerate every k-subset and count those containing a correct sample.

    Independent of `pass_at_k` ON PURPOSE: it touches no binomial coefficient and no product, so
    agreement is evidence rather than one expression compared to a rearrangement of itself.
    """
    _validate(n, c, k)
    if n > BRUTEFORCE_N_MAX:
        raise PassAtKError(f"refusing brute force at n={n} > {BRUTEFORCE_N_MAX}: "
                           f"C({n},{k}) subsets would not return")
    if k > n:
        raise PassAtKError(f"k={k} > n={n}")
    correct = set(range(c))
    subsets = list(itertools.combinations(range(n), k))
    hit = sum(1 for s in subsets if correct & set(s))
    return hit / len(subsets)


def pass_at_k_exact(n: int, c: int, k: int) -> float:
    """The binomial ratio in exact integer arithmetic. The reference the product is checked against.

    It CAN be computed directly here even though Figure 3 warns against it: the instability is a
    float64 property, and Python's ints are arbitrary precision.
    """
    _validate(n, c, k)
    if k > n:
        raise PassAtKError(f"k={k} > n={n}")
    return 1.0 - comb(n - c, k) / comb(n, k) if n - c >= k else 1.0


def mean_pass_at_k(per_problem: Sequence[tuple[int, int]], k: int) -> float:
    """`E_problems[pass@k]` over `(n, c)` pairs. The benchmark-level number."""
    if not per_problem:
        raise PassAtKError("no problems")
    return sum(pass_at_k(n, c, k) for n, c in per_problem) / len(per_problem)
