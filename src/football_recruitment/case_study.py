"""Recruitment case-study payload generation."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import numpy as np
import pandas as pd

from football_recruitment.profiles import filter_role_cohort
from football_recruitment.reliability import (
    bootstrap_similarity_rank_intervals,
    split_half_metric_reliability,
    weight_sensitivity_summary,
)
from football_recruitment.similarity import (
    CENTRE_FORWARD_FEATURE_COLUMNS,
    CENTRE_FORWARD_FEATURE_GROUPS,
    CENTRE_FORWARD_GROUP_WEIGHTS,
    build_feature_weights,
    calculate_similarity,
    default_centre_forward_feature_weights,
)

TARGET_PLAYER_ID = 10955
TARGET_PLAYER_NAME = "Harry Kane"
TARGET_ROLE = "Centre Forward"

RAW_METRICS = [
    "non_penalty_xg_p90",
    "non_penalty_shots_p90",
    "average_non_penalty_xg_per_shot",
    "successful_box_receipts_p90",
    "xg_assisted_p90",
    "completed_open_play_passes_p90",
    "final_third_pressures_p90",
    "counterpressures_p90",
    "ball_security_errors_p90",
]

METRIC_LABELS = {
    "non_penalty_xg_p90": "NP xG/90",
    "non_penalty_shots_p90": "NP shots/90",
    "average_non_penalty_xg_per_shot": "Avg NP xG/shot",
    "successful_box_receipts_p90": "Box receipts/90",
    "xg_assisted_p90": "xG assisted/90",
    "completed_open_play_passes_p90": "Open-play passes/90",
    "final_third_pressures_p90": "Final-third pressures/90",
    "counterpressures_p90": "Counterpressures/90",
    "ball_security_errors_p90": "Ball-security errors/90",
}

METRIC_GROUPS = {
    "non_penalty_xg_p90": "threat",
    "non_penalty_shots_p90": "threat",
    "average_non_penalty_xg_per_shot": "threat",
    "successful_box_receipts_p90": "progression",
    "xg_assisted_p90": "link_play",
    "completed_open_play_passes_p90": "link_play",
    "final_third_pressures_p90": "pressing",
    "counterpressures_p90": "pressing",
    "ball_security_errors_p90": "ball_security",
}

WEIGHT_SCENARIOS = {
    "balanced": CENTRE_FORWARD_GROUP_WEIGHTS,
    "threat heavy": {
        "threat": 0.45,
        "link_play": 0.20,
        "progression": 0.15,
        "pressing": 0.10,
        "ball_security": 0.10,
    },
    "link-play heavy": {
        "threat": 0.25,
        "link_play": 0.40,
        "progression": 0.15,
        "pressing": 0.10,
        "ball_security": 0.10,
    },
    "pressing heavy": {
        "threat": 0.25,
        "link_play": 0.20,
        "progression": 0.15,
        "pressing": 0.30,
        "ball_security": 0.10,
    },
}


def clean_value(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, (np.floating, float)):
        if not np.isfinite(value):
            return None
        return round(float(value), 6)
    if isinstance(value, (np.integer, int)):
        return int(value)
    if pd.isna(value):
        return None
    return value


def _player_record(row: pd.Series) -> dict[str, Any]:
    return {
        "playerId": clean_value(row["player_id"]),
        "playerName": row["player_name"],
        "teamName": row["team_name"],
        "competitionName": row["competition_name"],
        "seasonName": row["season_name"],
        "minutes": clean_value(row["minutes"]),
        "matches": clean_value(row["matches"]),
        "positionGroup": row["position_group"],
        "positionShare": clean_value(row["position_group_minutes_share"]),
    }


def _metric_delta_rows(target: pd.Series, candidate: pd.Series) -> list[dict[str, Any]]:
    rows = []
    for metric in RAW_METRICS:
        target_value = clean_value(target.get(metric))
        candidate_value = clean_value(candidate.get(metric))
        delta = None
        if target_value is not None and candidate_value is not None:
            delta = round(float(candidate_value) - float(target_value), 6)
        rows.append(
            {
                "metric": metric,
                "label": METRIC_LABELS[metric],
                "group": METRIC_GROUPS[metric],
                "targetValue": target_value,
                "candidateValue": candidate_value,
                "delta": delta,
            }
        )
    return rows


def _candidate_note(candidate: pd.Series, target: pd.Series) -> str:
    deltas = []
    for metric in RAW_METRICS:
        target_value = target.get(metric)
        candidate_value = candidate.get(metric)
        if pd.notna(target_value) and pd.notna(candidate_value):
            deltas.append((metric, abs(float(candidate_value) - float(target_value))))
    closest = [METRIC_LABELS[metric] for metric, _ in sorted(deltas, key=lambda item: item[1])[:2]]
    if len(closest) < 2:
        return "Similar across the weighted centre-forward event profile."
    return f"Closest to Kane on {closest[0]} and {closest[1]}."


def _enrich_rankings(rankings: pd.DataFrame, bootstrap: pd.DataFrame, sensitivity: pd.DataFrame) -> pd.DataFrame:
    result = rankings.merge(
        bootstrap,
        on=["competition_name", "season_name", "player_id"],
        how="left",
    )
    result = result.merge(
        sensitivity[
            [
                "competition_name",
                "season_name",
                "player_id",
                "scenarios_in_top_n",
                "best_rank",
                "worst_rank",
                "median_rank",
            ]
        ],
        on=["competition_name", "season_name", "player_id"],
        how="left",
    )
    return result


def build_recruitment_case_study(
    profiles: pd.DataFrame,
    player_match: pd.DataFrame,
    *,
    target_player_id: int = TARGET_PLAYER_ID,
    position_group: str = TARGET_ROLE,
    min_minutes: float = 900,
    min_position_share: float = 0.60,
    top_n: int = 10,
    bootstrap_iterations: int = 100,
    random_state: int = 42,
) -> tuple[dict[str, Any], dict[str, pd.DataFrame]]:
    """Build a portfolio-ready case-study payload and supporting tables."""

    cohort = filter_role_cohort(
        profiles,
        position_group=position_group,
        min_minutes=min_minutes,
        min_position_share=min_position_share,
    )
    feature_weights = default_centre_forward_feature_weights()
    rankings = calculate_similarity(
        cohort,
        target_player_id=target_player_id,
        feature_columns=CENTRE_FORWARD_FEATURE_COLUMNS,
        feature_weights=feature_weights,
    )
    target = rankings.loc[rankings["is_target"]].iloc[0]

    reliability = split_half_metric_reliability(
        player_match,
        metric_columns=RAW_METRICS,
        min_minutes=450,
        random_state=random_state,
    )
    bootstrap = bootstrap_similarity_rank_intervals(
        player_match,
        target_player_id=target_player_id,
        position_group=position_group,
        feature_columns=CENTRE_FORWARD_FEATURE_COLUMNS,
        feature_weights=feature_weights,
        min_minutes=min_minutes,
        min_position_share=min_position_share,
        iterations=bootstrap_iterations,
        random_state=random_state,
    )
    sensitivity = weight_sensitivity_summary(
        cohort,
        target_player_id=target_player_id,
        feature_groups=CENTRE_FORWARD_FEATURE_GROUPS,
        group_weight_scenarios=WEIGHT_SCENARIOS,
        build_feature_weights=build_feature_weights,
        top_n=top_n,
    )
    enriched = _enrich_rankings(rankings, bootstrap, sensitivity)
    candidates = enriched.loc[~enriched["is_target"]].head(top_n).copy()

    candidate_records = []
    for row in candidates.itertuples(index=False):
        series = pd.Series(row._asdict())
        candidate_records.append(
            {
                **_player_record(series),
                "similarityRank": clean_value(series["similarity_rank"]),
                "similarityPercentile": clean_value(series["similarity_percentile"]),
                "profileDistance": clean_value(series["profile_distance"]),
                "rankInterval": {
                    "lower": clean_value(series.get("rank_lower")),
                    "median": clean_value(series.get("rank_median")),
                    "upper": clean_value(series.get("rank_upper")),
                    "iterations": clean_value(series.get("bootstrap_iterations")),
                },
                "sensitivity": {
                    "scenariosInTopN": clean_value(series.get("scenarios_in_top_n")),
                    "bestRank": clean_value(series.get("best_rank")),
                    "worstRank": clean_value(series.get("worst_rank")),
                    "medianRank": clean_value(series.get("median_rank")),
                },
                "metricDeltas": _metric_delta_rows(target, series),
                "note": _candidate_note(series, target),
            }
        )

    payload = {
        "title": "Harry Kane 2015/16 Centre-Forward Shortlist",
        "source": "StatsBomb Open Data",
        "question": "Which centre-forwards in the 2015/16 open-data sample had event profiles closest to Harry Kane?",
        "scope": {
            "positionGroup": position_group,
            "minMinutes": min_minutes,
            "minPositionShare": min_position_share,
            "cohortPlayers": int(len(cohort)),
            "competitions": sorted(cohort["competition_name"].dropna().unique().tolist()),
            "season": "2015/2016",
        },
        "benchmark": _player_record(target),
        "metrics": [
            {"id": metric, "label": METRIC_LABELS[metric], "group": METRIC_GROUPS[metric]}
            for metric in RAW_METRICS
        ],
        "featureWeights": [
            {"feature": feature, "weight": clean_value(weight)}
            for feature, weight in feature_weights.items()
        ],
        "candidates": candidate_records,
        "validation": {
            "splitHalfReliability": [
                {
                    "metric": row.metric,
                    "label": METRIC_LABELS.get(row.metric, row.metric),
                    "playersCompared": clean_value(row.players_compared),
                    "correlation": clean_value(row.correlation),
                }
                for row in reliability.itertuples(index=False)
            ],
            "weightScenarios": sorted(WEIGHT_SCENARIOS),
            "bootstrapIterations": bootstrap_iterations,
        },
        "limitations": [
            "Historical event-profile similarity only; not a transfer recommendation.",
            "No contract, wage, age, injury, physical, or scouting-video context.",
            "League-normalised metrics are relative to the observed open-data cohort.",
        ],
    }

    return payload, {
        "rankings": enriched,
        "reliability": reliability,
        "bootstrap": bootstrap,
        "sensitivity": sensitivity,
    }


def case_study_to_markdown(payload: Mapping[str, Any]) -> str:
    """Render the case-study payload as a concise markdown report."""

    benchmark = payload["benchmark"]
    lines = [
        f"# {payload['title']}",
        "",
        payload["question"],
        "",
        "## Benchmark",
        "",
        (
            f"{benchmark['playerName']}, {benchmark['teamName']}, "
            f"{benchmark['competitionName']} {benchmark['seasonName']}; "
            f"{benchmark['minutes']:.0f} minutes."
        ),
        "",
        "## Method",
        "",
        (
            "Players are filtered to centre-forwards with at least "
            f"{payload['scope']['minMinutes']:.0f} minutes and "
            f"{payload['scope']['minPositionShare']:.0%} of minutes in role. "
            "Similarity uses robust-scaled, league-position-normalised event metrics."
        ),
        "",
        "## Shortlist",
        "",
        "| Rank | Player | Team | Competition | Distance | Rank interval | Note |",
        "| --- | --- | --- | --- | ---: | --- | --- |",
    ]

    for candidate in payload["candidates"]:
        interval = candidate["rankInterval"]
        interval_text = (
            f"{interval['lower']:.0f}-{interval['upper']:.0f}"
            if interval["lower"] is not None and interval["upper"] is not None
            else "-"
        )
        lines.append(
            "| "
            f"{candidate['similarityRank']} | "
            f"{candidate['playerName']} | "
            f"{candidate['teamName']} | "
            f"{candidate['competitionName']} | "
            f"{candidate['profileDistance']:.3f} | "
            f"{interval_text} | "
            f"{candidate['note']} |"
        )

    lines.extend(
        [
            "",
            "## Validation",
            "",
            (
                f"Bootstrap rank intervals use {payload['validation']['bootstrapIterations']} "
                "match-resampling iterations. Weight sensitivity checks whether players remain "
                "near the top when threat, link play, or pressing receives extra emphasis."
            ),
            "",
            "## Limitations",
            "",
        ]
    )
    lines.extend(f"- {item}" for item in payload["limitations"])
    lines.append("")
    return "\n".join(lines)
