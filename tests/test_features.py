import pandas as pd

from football_recruitment.features import (
    aggregate_event_features,
    build_player_match_features,
    derive_match_duration,
)


def test_derive_match_duration_uses_latest_event_clock() -> None:
    events = pd.DataFrame({"minute": [0, 94], "second": [0, 30]})
    assert derive_match_duration(events) == 94.5


def test_aggregate_event_features_counts_core_centre_forward_actions() -> None:
    events = pd.DataFrame(
        [
            {
                "id": "pass-1",
                "type": "Pass",
                "player_id": 1,
                "location": [70, 40],
                "pass_outcome": None,
                "pass_type": None,
                "under_pressure": True,
                "pass_assisted_shot_id": "shot-1",
                "shot_key_pass_id": None,
                "shot_statsbomb_xg": None,
                "shot_type": None,
                "carry_end_location": None,
                "ball_receipt_outcome": None,
                "dribble_outcome": None,
                "counterpress": None,
            },
            {
                "id": "shot-1",
                "type": "Shot",
                "player_id": 2,
                "location": [110, 40],
                "pass_outcome": None,
                "pass_type": None,
                "under_pressure": None,
                "pass_assisted_shot_id": None,
                "shot_key_pass_id": "pass-1",
                "shot_statsbomb_xg": 0.25,
                "shot_type": "Open Play",
                "carry_end_location": None,
                "ball_receipt_outcome": None,
                "dribble_outcome": None,
                "counterpress": None,
            },
            {
                "id": "carry-1",
                "type": "Carry",
                "player_id": 1,
                "location": [90, 40],
                "carry_end_location": [104, 40],
                "pass_outcome": None,
                "pass_type": None,
                "under_pressure": None,
                "pass_assisted_shot_id": None,
                "shot_key_pass_id": None,
                "shot_statsbomb_xg": None,
                "shot_type": None,
                "ball_receipt_outcome": None,
                "dribble_outcome": None,
                "counterpress": None,
            },
            {
                "id": "pressure-1",
                "type": "Pressure",
                "player_id": 1,
                "location": [95, 20],
                "counterpress": True,
                "pass_outcome": None,
                "pass_type": None,
                "under_pressure": None,
                "pass_assisted_shot_id": None,
                "shot_key_pass_id": None,
                "shot_statsbomb_xg": None,
                "shot_type": None,
                "carry_end_location": None,
                "ball_receipt_outcome": None,
                "dribble_outcome": None,
            },
        ]
    )

    result = aggregate_event_features(events).set_index("player_id")

    assert result.loc[1, "completed_open_play_passes"] == 1
    assert result.loc[1, "completed_pressured_passes"] == 1
    assert result.loc[1, "carries_into_box"] == 1
    assert result.loc[1, "progressive_carry_distance"] == 14
    assert result.loc[1, "final_third_pressures"] == 1
    assert result.loc[1, "counterpressures"] == 1
    assert result.loc[1, "xg_assisted"] == 0.25
    assert result.loc[2, "non_penalty_xg"] == 0.25


def test_build_player_match_features_merges_minutes_and_events() -> None:
    lineups = {
        33: {
            "team_id": 33,
            "team_name": "Tottenham Hotspur",
            "lineup": [
                {
                    "player_id": 1,
                    "player_name": "Example Forward",
                    "positions": [
                        {"position": "Center Forward", "from": "00:00", "to": None}
                    ],
                }
            ],
        }
    }
    events = pd.DataFrame(
        [
            {
                "id": "shot-1",
                "type": "Shot",
                "player_id": 1,
                "location": [110, 40],
                "minute": 94,
                "second": 30,
                "shot_type": "Open Play",
                "shot_statsbomb_xg": 0.3,
                "pass_outcome": None,
                "pass_type": None,
                "under_pressure": None,
                "ball_receipt_outcome": None,
                "carry_end_location": None,
                "dribble_outcome": None,
                "counterpress": None,
                "shot_key_pass_id": None,
            }
        ]
    )

    result = build_player_match_features(
        events=events,
        lineups=lineups,
        match_metadata={
            "competition_name": "Premier League",
            "season_name": "2015/2016",
            "match_id": 123,
            "match_date": "2015-08-08",
            "home_team": "Tottenham Hotspur",
            "away_team": "Example FC",
        },
    )

    assert len(result) == 1
    assert result.loc[0, "minutes"] == 94.5
    assert result.loc[0, "position_group"] == "Centre Forward"
    assert result.loc[0, "non_penalty_shots"] == 1
    assert result.loc[0, "non_penalty_xg"] == 0.3
