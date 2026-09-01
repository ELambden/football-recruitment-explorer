import pandas as pd
import pytest

from football_recruitment.profiles import (
    add_rate_metrics,
    build_player_profiles,
    filter_role_cohort,
)


def test_add_rate_metrics_calculates_per_90_and_ratios() -> None:
    profiles = pd.DataFrame(
        {
            "minutes": [900.0],
            "non_penalty_xg": [5.0],
            "non_penalty_shots": [25.0],
            "successful_box_receipts": [30.0],
            "carries_into_box": [10.0],
            "xg_assisted": [2.0],
            "completed_open_play_passes": [150.0],
            "progressive_carry_distance": [300.0],
            "successful_dribbles": [12.0],
            "final_third_pressures": [80.0],
            "counterpressures": [20.0],
            "completed_pressured_passes": [15.0],
            "pressured_passes_attempted": [30.0],
            "open_play_passes_attempted": [200.0],
            "miscontrols": [8.0],
            "dispossessed": [12.0],
        }
    )

    result = add_rate_metrics(profiles)

    assert result.loc[0, "non_penalty_xg_p90"] == pytest.approx(0.5)
    assert result.loc[0, "average_non_penalty_xg_per_shot"] == pytest.approx(0.2)
    assert result.loc[0, "pressured_pass_completion_pct"] == pytest.approx(50.0)
    assert result.loc[0, "ball_security_errors_p90"] == pytest.approx(2.0)


def test_build_player_profiles_aggregates_player_season() -> None:
    player_match = pd.DataFrame(
        {
            "competition_name": ["Premier League", "Premier League"],
            "season_name": ["2015/2016", "2015/2016"],
            "match_id": [1, 2],
            "team_name": ["Tottenham Hotspur", "Tottenham Hotspur"],
            "player_id": [10, 10],
            "player_name": ["Example Forward", "Example Forward"],
            "minutes": [90.0, 45.0],
            "position_group": ["Centre Forward", "Centre Forward"],
            "position_group_minutes_share": [1.0, 1.0],
            "event_count": [20, 10],
            "shots": [4, 1],
            "non_penalty_shots": [4, 1],
            "passes_attempted": [15, 5],
            "completed_passes": [10, 4],
            "open_play_passes_attempted": [14, 5],
            "completed_open_play_passes": [9, 4],
            "pressured_passes_attempted": [3, 1],
            "completed_pressured_passes": [2, 1],
            "ball_receipts": [8, 4],
            "successful_ball_receipts": [7, 3],
            "successful_box_receipts": [3, 1],
            "carries": [4, 2],
            "carries_into_box": [1, 1],
            "successful_dribbles": [1, 0],
            "pressures": [12, 4],
            "final_third_pressures": [10, 2],
            "counterpressures": [3, 1],
            "miscontrols": [1, 1],
            "dispossessed": [2, 0],
            "non_penalty_xg": [0.8, 0.2],
            "xg_assisted": [0.1, 0.2],
            "progressive_carry_distance": [30.0, 10.0],
        }
    )

    result = build_player_profiles(player_match)

    assert len(result) == 1
    assert result.loc[0, "minutes"] == 135.0
    assert result.loc[0, "matches"] == 2
    assert result.loc[0, "non_penalty_shots"] == 5
    assert result.loc[0, "position_group"] == "Centre Forward"
    assert result.loc[0, "non_penalty_xg_p90"] == pytest.approx(1.0 / 1.5)


def test_filter_role_cohort_requires_minutes_and_position_share() -> None:
    profiles = pd.DataFrame(
        {
            "player_id": [1, 2, 3],
            "position_group": ["Centre Forward", "Centre Forward", "Centre Back"],
            "minutes": [1000, 800, 1200],
            "position_group_minutes_share": [0.7, 0.9, 1.0],
        }
    )

    result = filter_role_cohort(
        profiles,
        position_group="Centre Forward",
        min_minutes=900,
        min_position_share=0.60,
    )

    assert result["player_id"].tolist() == [1]
