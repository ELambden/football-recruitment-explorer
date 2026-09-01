"""StatsBomb open-data audit helpers."""

from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path
from typing import Any

import pandas as pd

from football_recruitment.config import COMPETITION_SCOPE, CompetitionScope


AUDIT_COLUMNS = [
    "country_name",
    "competition_name",
    "competition_gender",
    "competition_id",
    "season_id",
    "season_name",
]


def select_competitions(
    competitions: pd.DataFrame,
    scope: tuple[CompetitionScope, ...] = COMPETITION_SCOPE,
) -> pd.DataFrame:
    """Return the configured competition-season rows from a StatsBomb table."""

    scoped_keys = {
        (item.country_name, item.competition_name, item.season_name)
        for item in scope
    }

    mask = competitions.apply(
        lambda row: (
            row.get("country_name"),
            row.get("competition_name"),
            row.get("season_name"),
        )
        in scoped_keys,
        axis=1,
    )

    selected = competitions.loc[mask, AUDIT_COLUMNS].copy()
    return selected.sort_values(["competition_name", "season_name"])


def build_match_coverage(
    selected_competitions: pd.DataFrame,
    matches_by_key: dict[tuple[int, int], pd.DataFrame],
) -> pd.DataFrame:
    """Summarise match and team coverage for each selected competition."""

    rows: list[dict[str, Any]] = []

    for row in selected_competitions.itertuples(index=False):
        key = (int(row.competition_id), int(row.season_id))
        matches = matches_by_key[key]
        teams = set(matches["home_team"].dropna()) | set(matches["away_team"].dropna())

        rows.append(
            {
                "country_name": row.country_name,
                "competition_name": row.competition_name,
                "season_name": row.season_name,
                "competition_id": int(row.competition_id),
                "season_id": int(row.season_id),
                "match_count": int(len(matches)),
                "unique_match_ids": int(matches["match_id"].nunique()),
                "team_count": int(len(teams)),
            }
        )

    return pd.DataFrame(rows).sort_values("competition_name")


def event_schema_report(events: pd.DataFrame) -> dict[str, Any]:
    """Build a compact event schema report for audit output."""

    return {
        "row_count": int(len(events)),
        "column_count": int(len(events.columns)),
        "columns": events.columns.tolist(),
        "event_types": events["type"].value_counts().head(50).to_dict()
        if "type" in events
        else {},
    }


def lineup_schema_report(lineups: Any) -> dict[str, Any]:
    """Summarise raw lineup structure without storing the full payload."""

    if isinstance(lineups, dict):
        teams = []
        first_team = []
        for team_id, team_payload in lineups.items():
            if isinstance(team_payload, dict):
                teams.append(team_payload.get("team_name", str(team_id)))
                first_team = team_payload.get("lineup", [])
            else:
                teams.append(str(team_id))
                first_team = team_payload
            if first_team:
                break
    else:
        teams = []
        first_team = lineups

    first_player = first_team[0] if first_team else {}
    return {
        "container_type": type(lineups).__name__,
        "teams": teams,
        "first_player_keys": sorted(first_player.keys()),
        "first_position_keys": sorted(
            first_player.get("positions", [{}])[0].keys()
            if first_player.get("positions")
            else []
        ),
    }


def validate_event_locations(events: pd.DataFrame) -> None:
    """Validate that StatsBomb start locations fit the 120 by 80 pitch."""

    if "location" not in events:
        return

    locations = events["location"].dropna()
    invalid = locations.loc[
        ~locations.map(
            lambda xy: (
                isinstance(xy, list)
                and len(xy) >= 2
                and 0 <= xy[0] <= 120
                and 0 <= xy[1] <= 80
            )
        )
    ]
    if not invalid.empty:
        raise ValueError(f"Found {len(invalid)} invalid event locations")


def write_json(path: Path, payload: dict[str, Any]) -> None:
    """Write stable, human-readable JSON."""

    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def configured_scope_as_records() -> list[dict[str, str]]:
    """Return configured scope rows for display or logging."""

    return [asdict(item) for item in COMPETITION_SCOPE]

