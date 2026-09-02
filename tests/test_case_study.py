import pandas as pd
import pytest

from football_recruitment.case_study import case_study_to_markdown
from football_recruitment.reliability import (
    split_half_metric_reliability,
    weight_sensitivity_summary,
)
from football_recruitment.similarity import build_feature_weights


def test_split_half_metric_reliability_returns_metric_rows() -> None:
    rows = []
    for match_id in [1, 2, 3, 4]:
        for player_id, name, shots in [(1, "Target", 3), (2, "Near", 2), (3, "Far", 1)]:
            rows.append(
                {
                    "competition_name": "Premier League",
                    "season_name": "2015/2016",
                    "match_id": match_id,
                    "team_name": "Team",
                    "player_id": player_id,
                    "player_name": name,
                    "minutes": 90.0,
                    "position_group": "Centre Forward",
                    "position_group_minutes_share": 1.0,
                    "non_penalty_shots": shots + match_id,
                    "non_penalty_xg": 0.2 * shots,
                }
            )

    result = split_half_metric_reliability(
        pd.DataFrame(rows),
        metric_columns=["non_penalty_shots_p90"],
        min_minutes=90,
        random_state=1,
    )

    assert result.loc[0, "metric"] == "non_penalty_shots_p90"
    assert result.loc[0, "players_compared"] == 3
    assert result.loc[0, "correlation"] == pytest.approx(1.0)


def test_weight_sensitivity_summary_counts_top_n_appearances() -> None:
    profiles = pd.DataFrame(
        {
            "competition_name": ["PL", "PL", "PL"],
            "season_name": ["2015/2016", "2015/2016", "2015/2016"],
            "player_id": [1, 2, 3],
            "player_name": ["Target", "Near", "Far"],
            "team_name": ["A", "B", "C"],
            "minutes": [1800, 1700, 1600],
            "shots_p90": [3.0, 3.1, 0.5],
        }
    )

    result = weight_sensitivity_summary(
        profiles,
        target_player_id=1,
        feature_groups={"threat": ["shots_p90"]},
        group_weight_scenarios={"balanced": {"threat": 1.0}},
        build_feature_weights=build_feature_weights,
        top_n=1,
    )

    assert result.loc[0, "player_id"] == 2
    assert result.loc[0, "scenarios_in_top_n"] == 1


def test_case_study_to_markdown_contains_limitations() -> None:
    payload = {
        "title": "Example Case",
        "question": "Who is similar?",
        "benchmark": {
            "playerName": "Harry Kane",
            "teamName": "Tottenham Hotspur",
            "competitionName": "Premier League",
            "seasonName": "2015/2016",
            "minutes": 3486.65,
        },
        "scope": {"minMinutes": 900, "minPositionShare": 0.6},
        "candidates": [
            {
                "similarityRank": 2,
                "playerName": "Candidate",
                "teamName": "Club",
                "competitionName": "League",
                "profileDistance": 0.5,
                "rankInterval": {"lower": 2, "upper": 5},
                "note": "Close profile.",
            }
        ],
        "validation": {"bootstrapIterations": 10},
        "limitations": ["Historical sample only."],
    }

    markdown = case_study_to_markdown(payload)

    assert "Example Case" in markdown
    assert "Historical sample only." in markdown
