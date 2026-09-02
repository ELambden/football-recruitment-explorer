"""Reliability, uncertainty, and sensitivity helpers."""

from __future__ import annotations

from collections.abc import Mapping, Sequence

import numpy as np
import pandas as pd

from football_recruitment.profiles import build_player_profiles, filter_role_cohort
from football_recruitment.similarity import calculate_similarity

PROFILE_KEYS = ["competition_name", "season_name", "player_id", "player_name"]


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


def split_half_metric_reliability(
    player_match: pd.DataFrame,
    *,
    metric_columns: Sequence[str],
    min_minutes: float = 450,
    random_state: int = 42,
) -> pd.DataFrame:
    """Estimate metric stability by correlating two random match halves."""

    required = {"match_id", *PROFILE_KEYS, "minutes"}
    missing = required - set(player_match.columns)
    if missing:
        raise KeyError(f"Missing columns: {sorted(missing)}")

    match_ids = np.asarray(sorted(player_match["match_id"].dropna().unique()))
    if len(match_ids) < 2:
        raise ValueError("At least two matches are required for split-half reliability")

    rng = np.random.default_rng(random_state)
    shuffled = match_ids.copy()
    rng.shuffle(shuffled)
    split_at = len(shuffled) // 2
    first_ids = set(shuffled[:split_at])
    second_ids = set(shuffled[split_at:])
    if not first_ids or not second_ids:
        raise ValueError("Both split halves must contain at least one match")

    first = build_player_profiles(player_match.loc[player_match["match_id"].isin(first_ids)])
    second = build_player_profiles(player_match.loc[player_match["match_id"].isin(second_ids)])

    first = first.loc[first["minutes"].ge(min_minutes), PROFILE_KEYS + list(metric_columns)]
    second = second.loc[second["minutes"].ge(min_minutes), PROFILE_KEYS + list(metric_columns)]
    merged = first.merge(second, on=PROFILE_KEYS, suffixes=("_first", "_second"))

    rows = []
    for metric in metric_columns:
        valid = pd.DataFrame(
            {
                "first": pd.to_numeric(merged[f"{metric}_first"], errors="coerce"),
                "second": pd.to_numeric(merged[f"{metric}_second"], errors="coerce"),
            }
        ).dropna()
        rows.append(
            {
                "metric": metric,
                "players_compared": int(len(valid)),
                "correlation": valid["first"].corr(valid["second"]) if len(valid) >= 3 else np.nan,
                "first_half_mean": valid["first"].mean() if not valid.empty else np.nan,
                "second_half_mean": valid["second"].mean() if not valid.empty else np.nan,
            }
        )

    return pd.DataFrame(rows)


def bootstrap_similarity_rank_intervals(
    player_match: pd.DataFrame,
    *,
    target_player_id: int,
    position_group: str,
    feature_columns: Sequence[str],
    feature_weights: Mapping[str, float],
    min_minutes: float = 900,
    min_position_share: float = 0.60,
    iterations: int = 100,
    random_state: int = 42,
) -> pd.DataFrame:
    """Bootstrap matches and summarise similarity-rank uncertainty."""

    if iterations <= 0:
        raise ValueError("iterations must be positive")

    match_ids = np.asarray(sorted(player_match["match_id"].dropna().unique()))
    if len(match_ids) < 2:
        raise ValueError("At least two matches are required for bootstrap intervals")

    rng = np.random.default_rng(random_state)
    rank_samples: dict[tuple[str, str, int], list[float]] = {}

    for _ in range(iterations):
        sampled_ids = rng.choice(match_ids, size=len(match_ids), replace=True)
        sampled = pd.concat(
            [player_match.loc[player_match["match_id"].eq(match_id)] for match_id in sampled_ids],
            ignore_index=True,
        )
        profiles = build_player_profiles(sampled)
        cohort = filter_role_cohort(
            profiles,
            position_group=position_group,
            min_minutes=min_minutes,
            min_position_share=min_position_share,
        )
        if target_player_id not in set(cohort["player_id"]):
            continue

        try:
            rankings = calculate_similarity(
                cohort,
                target_player_id=target_player_id,
                feature_columns=list(feature_columns),
                feature_weights=dict(feature_weights),
            )
        except ValueError:
            continue

        for row in rankings.itertuples(index=False):
            key = (str(row.competition_name), str(row.season_name), int(row.player_id))
            rank_samples.setdefault(key, []).append(float(row.similarity_rank))

    rows = []
    for (competition, season, player_id), ranks in rank_samples.items():
        values = np.asarray(ranks, dtype=float)
        rows.append(
            {
                "competition_name": competition,
                "season_name": season,
                "player_id": player_id,
                "bootstrap_iterations": int(len(values)),
                "rank_median": float(np.median(values)),
                "rank_lower": float(np.percentile(values, 5)),
                "rank_upper": float(np.percentile(values, 95)),
            }
        )

    return pd.DataFrame(rows).sort_values(["rank_median", "rank_upper", "player_id"]).reset_index(drop=True)


def weight_sensitivity_summary(
    profiles: pd.DataFrame,
    *,
    target_player_id: int,
    feature_groups: Mapping[str, Sequence[str]],
    group_weight_scenarios: Mapping[str, Mapping[str, float]],
    build_feature_weights,
    top_n: int = 10,
) -> pd.DataFrame:
    """Summarise how candidate ranks move under alternative feature weights."""

    if top_n <= 0:
        raise ValueError("top_n must be positive")

    rows = []
    for scenario_name, group_weights in group_weight_scenarios.items():
        feature_weights = build_feature_weights(
            {name: list(features) for name, features in feature_groups.items()},
            dict(group_weights),
        )
        rankings = calculate_similarity(
            profiles,
            target_player_id=target_player_id,
            feature_columns=list(feature_weights),
            feature_weights=feature_weights,
        )
        for row in rankings.loc[~rankings["is_target"]].head(top_n).itertuples(index=False):
            rows.append(
                {
                    "scenario": scenario_name,
                    "competition_name": row.competition_name,
                    "season_name": row.season_name,
                    "player_id": int(row.player_id),
                    "player_name": row.player_name,
                    "similarity_rank": int(row.similarity_rank),
                    "profile_distance": float(row.profile_distance),
                }
            )

    scenario_ranks = pd.DataFrame(rows)
    if scenario_ranks.empty:
        return pd.DataFrame(
            columns=[
                "competition_name",
                "season_name",
                "player_id",
                "player_name",
                "scenarios_in_top_n",
                "best_rank",
                "worst_rank",
                "median_rank",
            ]
        )

    return (
        scenario_ranks.groupby(
            ["competition_name", "season_name", "player_id", "player_name"],
            as_index=False,
        )
        .agg(
            scenarios_in_top_n=("scenario", "nunique"),
            best_rank=("similarity_rank", "min"),
            worst_rank=("similarity_rank", "max"),
            median_rank=("similarity_rank", "median"),
        )
        .sort_values(["scenarios_in_top_n", "median_rank"], ascending=[False, True])
        .reset_index(drop=True)
    )
