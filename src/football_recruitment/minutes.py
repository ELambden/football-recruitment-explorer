"""Lineup-position interval parsing."""

from __future__ import annotations

from typing import Any

import pandas as pd

from football_recruitment.config import POSITION_TO_GROUP


def iter_team_lineups(
    lineups: dict[str, list[dict[str, Any]]] | dict[int, dict[str, Any]],
):
    """Yield team names and player lists from common StatsBomb lineup shapes."""

    for team_key, team_payload in lineups.items():
        if isinstance(team_payload, dict) and "lineup" in team_payload:
            yield team_payload.get("team_name", str(team_key)), team_payload["lineup"]
        else:
            yield str(team_key), team_payload


def clock_to_minutes(value: str | int | float | None) -> float | None:
    """Convert a StatsBomb clock value to elapsed minutes."""

    if value is None or pd.isna(value):
        return None
    if isinstance(value, int | float):
        return float(value)

    parts = str(value).split(":")
    if len(parts) == 1:
        return float(parts[0])
    if len(parts) == 2:
        minutes, seconds = parts
        return float(minutes) + float(seconds) / 60

    raise ValueError(f"Unsupported clock value: {value!r}")


def parse_lineup_intervals(
    lineups: dict[str, list[dict[str, Any]]] | dict[int, dict[str, Any]],
    *,
    match_id: int,
    match_duration: float,
) -> pd.DataFrame:
    """Return one row per player-position interval from raw lineups."""

    rows: list[dict[str, Any]] = []

    for team_name, players in iter_team_lineups(lineups):
        for player in players:
            player_id = player.get("player_id")
            player_name = player.get("player_name") or player.get("player_nickname")

            for position in player.get("positions", []):
                position_name = position.get("position")
                from_minute = clock_to_minutes(position.get("from")) or 0.0
                to_minute = clock_to_minutes(position.get("to")) or match_duration

                rows.append(
                    {
                        "match_id": int(match_id),
                        "team_name": team_name,
                        "player_id": player_id,
                        "player_name": player_name,
                        "position": position_name,
                        "position_group": POSITION_TO_GROUP.get(position_name, "Other"),
                        "from_minute": float(from_minute),
                        "to_minute": float(to_minute),
                        "minutes": max(float(to_minute) - float(from_minute), 0.0),
                    }
                )

    return pd.DataFrame(rows)


def dominant_position_group(intervals: pd.DataFrame) -> pd.DataFrame:
    """Calculate each player's dominant position group within a match or season."""

    required = {"player_id", "position_group", "minutes"}
    missing = required - set(intervals.columns)
    if missing:
        raise KeyError(f"Missing columns: {sorted(missing)}")

    grouped = (
        intervals.groupby(["player_id", "position_group"], as_index=False)["minutes"]
        .sum()
        .sort_values(["player_id", "minutes"], ascending=[True, False])
    )
    totals = grouped.groupby("player_id")["minutes"].transform("sum")
    grouped["position_group_minutes_share"] = grouped["minutes"] / totals
    return grouped.drop_duplicates("player_id").reset_index(drop=True)

