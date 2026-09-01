"""Player-profile similarity calculations."""

from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.preprocessing import RobustScaler

CENTRE_FORWARD_FEATURE_GROUPS: dict[str, list[str]] = {
    "threat": [
        "non_penalty_xg_p90_league_pos_z",
        "non_penalty_shots_p90_league_pos_z",
        "average_non_penalty_xg_per_shot_league_pos_z",
    ],
    "link_play": [
        "xg_assisted_p90_league_pos_z",
        "completed_open_play_passes_p90_league_pos_z",
        "pressured_pass_completion_pct",
    ],
    "progression": [
        "successful_box_receipts_p90_league_pos_z",
        "carries_into_box_p90_league_pos_z",
        "progressive_carry_distance_p90_league_pos_z",
        "successful_dribbles_p90_league_pos_z",
    ],
    "pressing": [
        "final_third_pressures_p90_league_pos_z",
        "counterpressures_p90_league_pos_z",
    ],
    "ball_security": ["ball_security_errors_p90_league_pos_z"],
}

CENTRE_FORWARD_GROUP_WEIGHTS: dict[str, float] = {
    "threat": 0.30,
    "link_play": 0.25,
    "progression": 0.20,
    "pressing": 0.15,
    "ball_security": 0.10,
}

CENTRE_FORWARD_FEATURE_COLUMNS = [
    feature
    for features in CENTRE_FORWARD_FEATURE_GROUPS.values()
    for feature in features
]


def build_feature_weights(
    feature_groups: dict[str, list[str]],
    group_weights: dict[str, float],
) -> dict[str, float]:
    """Distribute group-level weights equally across features in each group."""

    missing_groups = set(feature_groups) - set(group_weights)
    extra_groups = set(group_weights) - set(feature_groups)
    if missing_groups or extra_groups:
        raise ValueError(
            "feature_groups and group_weights must contain the same groups; "
            f"missing={sorted(missing_groups)}, extra={sorted(extra_groups)}"
        )

    feature_weights: dict[str, float] = {}
    for group, features in feature_groups.items():
        if not features:
            raise ValueError(f"Feature group {group!r} is empty")
        per_feature_weight = group_weights[group] / len(features)
        for feature in features:
            if feature in feature_weights:
                raise ValueError(f"Feature appears in multiple groups: {feature}")
            feature_weights[feature] = per_feature_weight

    return feature_weights


def default_centre_forward_feature_weights() -> dict[str, float]:
    """Return the default weighted centre-forward similarity feature set."""

    return build_feature_weights(
        CENTRE_FORWARD_FEATURE_GROUPS,
        CENTRE_FORWARD_GROUP_WEIGHTS,
    )


def calculate_similarity(
    profiles: pd.DataFrame,
    *,
    target_player_id: int,
    feature_columns: list[str],
    feature_weights: dict[str, float],
) -> pd.DataFrame:
    """Rank players by weighted distance from a target profile."""

    missing = set(feature_columns) - set(profiles.columns)
    if missing:
        raise KeyError(f"Missing feature columns: {sorted(missing)}")

    if set(feature_columns) != set(feature_weights):
        raise ValueError("feature_weights must contain exactly the feature columns")

    cohort = profiles.dropna(subset=feature_columns).copy()
    target_matches = np.flatnonzero(
        cohort["player_id"].to_numpy() == target_player_id
    )
    if len(target_matches) != 1:
        raise ValueError(f"Expected one target row; found {len(target_matches)}")

    lower = cohort[feature_columns].quantile(0.02)
    upper = cohort[feature_columns].quantile(0.98)
    X = cohort[feature_columns].clip(lower=lower, upper=upper, axis="columns")

    scaler = RobustScaler()
    Z = scaler.fit_transform(X)

    weights = np.asarray([feature_weights[col] for col in feature_columns], dtype=float)
    weights = weights / weights.sum()

    target_index = int(target_matches[0])
    difference = Z - Z[target_index]

    cohort["profile_distance"] = np.sqrt(np.sum(weights * difference**2, axis=1))

    ranks = cohort["profile_distance"].rank(method="min", ascending=True)
    denominator = max(len(cohort) - 1, 1)
    cohort["similarity_percentile"] = 100 * (1 - (ranks - 1) / denominator)
    cohort["similarity_rank"] = ranks.astype(int)
    cohort["is_target"] = cohort["player_id"].eq(target_player_id)

    return cohort.sort_values(
        ["profile_distance", "minutes"], ascending=[True, False]
    )
