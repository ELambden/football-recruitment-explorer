import pandas as pd

from football_recruitment.minutes import (
    clock_to_minutes,
    dominant_position_group,
    parse_lineup_intervals,
)


def test_clock_to_minutes_handles_mm_ss() -> None:
    assert clock_to_minutes("81:30") == 81.5


def test_parse_lineup_intervals_uses_match_duration_for_open_interval() -> None:
    lineups = {
        "Tottenham Hotspur": [
            {
                "player_id": 1,
                "player_name": "Example Forward",
                "positions": [
                    {
                        "position": "Center Forward",
                        "from": "00:00",
                        "to": None,
                    }
                ],
            }
        ]
    }

    result = parse_lineup_intervals(lineups, match_id=123, match_duration=95.0)

    assert result.loc[0, "minutes"] == 95.0
    assert result.loc[0, "position_group"] == "Centre Forward"


def test_parse_lineup_intervals_handles_statsbombpy_dict_shape() -> None:
    lineups = {
        33: {
            "team_id": 33,
            "team_name": "Tottenham Hotspur",
            "lineup": [
                {
                    "player_id": 1,
                    "player_name": "Example Forward",
                    "positions": [
                        {
                            "position": "Center Forward",
                            "from": "00:00",
                            "to": "81:30",
                        }
                    ],
                }
            ],
        }
    }

    result = parse_lineup_intervals(lineups, match_id=123, match_duration=95.0)

    assert result.loc[0, "team_name"] == "Tottenham Hotspur"
    assert result.loc[0, "minutes"] == 81.5


def test_dominant_position_group_returns_largest_minutes_share() -> None:
    intervals = pd.DataFrame(
        {
            "player_id": [1, 1],
            "position_group": ["Centre Forward", "Attacking Midfielder / Winger"],
            "minutes": [70.0, 20.0],
        }
    )

    result = dominant_position_group(intervals)

    assert result.loc[0, "position_group"] == "Centre Forward"
    assert result.loc[0, "position_group_minutes_share"] == 70 / 90

