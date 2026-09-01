"""Player-profile similarity calculations."""

from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.preprocessing import RobustScaler


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

    return cohort.sort_values(
        ["profile_distance", "minutes"], ascending=[True, False]
    )

