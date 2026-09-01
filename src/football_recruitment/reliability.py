"""Reliability and shrinkage helpers."""

from __future__ import annotations


def shrink_rate(
    count: float,
    nineties: float,
    prior_mean: float,
    prior_nineties: float = 8.0,
) -> float:
    """Shrink an observed event rate towards a positional prior mean."""

    if nineties < 0:
        raise ValueError("nineties must be non-negative")
    if prior_nineties < 0:
        raise ValueError("prior_nineties must be non-negative")

    denominator = nineties + prior_nineties
    if denominator == 0:
        return prior_mean

    return (count + prior_mean * prior_nineties) / denominator

