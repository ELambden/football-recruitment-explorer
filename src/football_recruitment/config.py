"""Shared project configuration."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CompetitionScope:
    country_name: str
    competition_name: str
    season_name: str


COMPETITION_SCOPE = (
    CompetitionScope("England", "Premier League", "2015/2016"),
    CompetitionScope("France", "Ligue 1", "2015/2016"),
    CompetitionScope("Italy", "Serie A", "2015/2016"),
)

POSITION_GROUPS: dict[str, set[str]] = {
    "Goalkeeper": {"Goalkeeper"},
    "Centre Back": {"Left Center Back", "Center Back", "Right Center Back"},
    "Full Back / Wing Back": {
        "Left Back",
        "Right Back",
        "Left Wing Back",
        "Right Wing Back",
    },
    "Defensive Midfielder": {
        "Left Defensive Midfield",
        "Center Defensive Midfield",
        "Right Defensive Midfield",
    },
    "Central Midfielder": {
        "Left Center Midfield",
        "Center Midfield",
        "Right Center Midfield",
    },
    "Attacking Midfielder / Winger": {
        "Left Attacking Midfield",
        "Center Attacking Midfield",
        "Right Attacking Midfield",
        "Left Wing",
        "Right Wing",
    },
    "Centre Forward": {"Center Forward"},
}

POSITION_TO_GROUP = {
    position: group
    for group, positions in POSITION_GROUPS.items()
    for position in positions
}

FEATURE_GROUP_WEIGHTS: dict[str, float] = {
    "threat": 0.30,
    "link_play": 0.25,
    "progression": 0.20,
    "pressing": 0.15,
    "ball_security": 0.10,
}

