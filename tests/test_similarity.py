import pandas as pd
import pytest

from football_recruitment.similarity import (
    build_feature_weights,
    calculate_similarity,
)


def test_calculate_similarity_ranks_target_first() -> None:
    profiles = pd.DataFrame(
        {
            "player_id": [1, 2, 3],
            "player_name": ["Target", "Near", "Far"],
            "minutes": [1800, 1700, 1600],
            "shots_p90": [3.0, 3.1, 1.0],
            "pressures_p90": [12.0, 11.5, 4.0],
        }
    )

    result = calculate_similarity(
        profiles,
        target_player_id=1,
        feature_columns=["shots_p90", "pressures_p90"],
        feature_weights={"shots_p90": 0.6, "pressures_p90": 0.4},
    )

    assert result.iloc[0]["player_id"] == 1
    assert result.iloc[0]["similarity_percentile"] == 100
    assert result.iloc[0]["similarity_rank"] == 1
    assert result.iloc[0]["is_target"]


def test_calculate_similarity_requires_complete_weights() -> None:
    profiles = pd.DataFrame(
        {
            "player_id": [1],
            "minutes": [900],
            "shots_p90": [2.0],
        }
    )

    with pytest.raises(ValueError):
        calculate_similarity(
            profiles,
            target_player_id=1,
            feature_columns=["shots_p90"],
            feature_weights={},
        )


def test_build_feature_weights_distributes_group_weight_across_features() -> None:
    weights = build_feature_weights(
        {"threat": ["xg", "shots"], "pressing": ["pressures"]},
        {"threat": 0.6, "pressing": 0.4},
    )

    assert weights == {"xg": 0.3, "shots": 0.3, "pressures": 0.4}


def test_build_feature_weights_requires_matching_groups() -> None:
    with pytest.raises(ValueError):
        build_feature_weights({"threat": ["xg"]}, {"pressing": 1.0})
