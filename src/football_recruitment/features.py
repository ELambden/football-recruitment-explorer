"""Player-match feature engineering from StatsBomb event data."""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from football_recruitment.minutes import dominant_position_group, parse_lineup_intervals

BOX_X_MIN = 102.0
BOX_Y_MIN = 18.0
BOX_Y_MAX = 62.0
ATTACKING_THIRD_X_MIN = 80.0


def _xy(value: Any) -> tuple[float, float] | tuple[None, None]:
    if isinstance(value, list | tuple) and len(value) >= 2:
        return float(value[0]), float(value[1])
    return None, None


def _x(value: Any) -> float | None:
    x, _ = _xy(value)
    return x


def _inside_box(value: Any) -> bool:
    x, y = _xy(value)
    return x is not None and x >= BOX_X_MIN and BOX_Y_MIN <= y <= BOX_Y_MAX


def _in_attacking_third(value: Any) -> bool:
    x = _x(value)
    return x is not None and x >= ATTACKING_THIRD_X_MIN


def derive_match_duration(events: pd.DataFrame) -> float:
    """Estimate match duration from event minute and second columns."""

    if events.empty or "minute" not in events:
        return 90.0

    seconds = events.get("second", pd.Series(0, index=events.index)).fillna(0)
    elapsed = events["minute"].fillna(0).astype(float) + seconds.astype(float) / 60
    return max(float(elapsed.max()), 90.0)


def _sum_by_player(events: pd.DataFrame, mask: pd.Series, column: str) -> pd.Series:
    if column not in events:
        return pd.Series(dtype=float)
    return events.loc[mask].groupby("player_id")[column].sum(min_count=1)


def _count_by_player(events: pd.DataFrame, mask: pd.Series) -> pd.Series:
    return events.loc[mask].groupby("player_id").size()


def _completed_pass_mask(events: pd.DataFrame) -> pd.Series:
    return events["type"].eq("Pass") & events["pass_outcome"].isna()


def _open_play_pass_mask(events: pd.DataFrame) -> pd.Series:
    return events["type"].eq("Pass") & events["pass_type"].isna()


def _assisted_shot_xg_by_passer(events: pd.DataFrame) -> pd.Series:
    required = {"id", "type", "player_id", "shot_key_pass_id", "shot_statsbomb_xg"}
    if not required <= set(events.columns):
        return pd.Series(dtype=float)

    shots = events.loc[
        events["type"].eq("Shot") & events["shot_key_pass_id"].notna(),
        ["shot_key_pass_id", "shot_statsbomb_xg"],
    ].copy()
    passes = events.loc[events["type"].eq("Pass"), ["id", "player_id"]].copy()

    assisted = shots.merge(passes, left_on="shot_key_pass_id", right_on="id", how="inner")
    return assisted.groupby("player_id")["shot_statsbomb_xg"].sum()


def aggregate_event_features(events: pd.DataFrame) -> pd.DataFrame:
    """Aggregate compact event-derived features to one row per player."""

    if "player_id" not in events:
        return pd.DataFrame(columns=["player_id"])

    player_events = events.loc[events["player_id"].notna()].copy()
    if player_events.empty:
        return pd.DataFrame(columns=["player_id"])

    player_events["player_id"] = player_events["player_id"].astype(int)

    event_type = player_events["type"]
    pass_mask = event_type.eq("Pass")
    open_play_pass_mask = _open_play_pass_mask(player_events)
    completed_pass_mask = _completed_pass_mask(player_events)
    completed_open_play_pass_mask = open_play_pass_mask & player_events["pass_outcome"].isna()
    under_pressure_mask = player_events.get("under_pressure", False).fillna(False).astype(bool)

    shot_mask = event_type.eq("Shot")
    non_penalty_shot_mask = shot_mask & ~player_events["shot_type"].eq("Penalty")
    carry_mask = event_type.eq("Carry")
    pressure_mask = event_type.eq("Pressure")

    features = pd.DataFrame(index=sorted(player_events["player_id"].unique()))
    features.index.name = "player_id"

    count_masks = {
        "event_count": pd.Series(True, index=player_events.index),
        "shots": shot_mask,
        "non_penalty_shots": non_penalty_shot_mask,
        "passes_attempted": pass_mask,
        "completed_passes": completed_pass_mask,
        "open_play_passes_attempted": open_play_pass_mask,
        "completed_open_play_passes": completed_open_play_pass_mask,
        "pressured_passes_attempted": pass_mask & under_pressure_mask,
        "completed_pressured_passes": completed_pass_mask & under_pressure_mask,
        "ball_receipts": event_type.eq("Ball Receipt*"),
        "successful_ball_receipts": event_type.eq("Ball Receipt*")
        & player_events["ball_receipt_outcome"].isna(),
        "successful_box_receipts": event_type.eq("Ball Receipt*")
        & player_events["ball_receipt_outcome"].isna()
        & player_events["location"].map(_inside_box),
        "carries": carry_mask,
        "carries_into_box": carry_mask
        & ~player_events["location"].map(_inside_box)
        & player_events["carry_end_location"].map(_inside_box),
        "successful_dribbles": event_type.eq("Dribble")
        & player_events["dribble_outcome"].eq("Complete"),
        "pressures": pressure_mask,
        "final_third_pressures": pressure_mask
        & player_events["location"].map(_in_attacking_third),
        "counterpressures": pressure_mask
        & player_events.get("counterpress", False).fillna(False).astype(bool),
        "miscontrols": event_type.eq("Miscontrol"),
        "dispossessed": event_type.eq("Dispossessed"),
    }

    for column, mask in count_masks.items():
        features[column] = _count_by_player(player_events, mask)

    features["non_penalty_xg"] = _sum_by_player(
        player_events, non_penalty_shot_mask, "shot_statsbomb_xg"
    )
    features["xg_assisted"] = _assisted_shot_xg_by_passer(player_events)

    carry_rows = player_events.loc[carry_mask, ["player_id", "location", "carry_end_location"]].copy()
    if not carry_rows.empty:
        carry_rows["start_x"] = carry_rows["location"].map(_x)
        carry_rows["end_x"] = carry_rows["carry_end_location"].map(_x)
        carry_rows["progressive_carry_distance"] = (
            carry_rows["end_x"] - carry_rows["start_x"]
        ).clip(lower=0)
        features["progressive_carry_distance"] = carry_rows.groupby("player_id")[
            "progressive_carry_distance"
        ].sum()
    else:
        features["progressive_carry_distance"] = 0.0

    features = features.fillna(0).reset_index()
    return features


def build_player_match_features(
    *,
    events: pd.DataFrame,
    lineups: dict[str, list[dict[str, Any]]] | dict[int, dict[str, Any]],
    match_metadata: pd.Series | dict[str, Any],
) -> pd.DataFrame:
    """Build one compact player-match row per player listed in the lineup."""

    match = dict(match_metadata)
    match_id = int(match["match_id"])
    match_duration = derive_match_duration(events)

    intervals = parse_lineup_intervals(
        lineups, match_id=match_id, match_duration=match_duration
    )
    minutes = (
        intervals.groupby(["match_id", "team_name", "player_id", "player_name"], as_index=False)[
            "minutes"
        ]
        .sum()
        .assign(player_id=lambda df: df["player_id"].astype(int))
    )

    dominant = dominant_position_group(intervals)[
        ["player_id", "position_group", "position_group_minutes_share"]
    ].assign(player_id=lambda df: df["player_id"].astype(int))

    event_features = aggregate_event_features(events)
    rows = minutes.merge(dominant, on="player_id", how="left").merge(
        event_features, on="player_id", how="left"
    )

    count_columns = [
        column
        for column in rows.columns
        if column
        not in {
            "match_id",
            "team_name",
            "player_id",
            "player_name",
            "minutes",
            "position_group",
            "position_group_minutes_share",
        }
    ]
    rows[count_columns] = rows[count_columns].fillna(0)

    rows["competition_name"] = match.get("competition_name")
    rows["season_name"] = match.get("season_name")
    rows["home_team"] = match.get("home_team")
    rows["away_team"] = match.get("away_team")
    rows["match_date"] = match.get("match_date")
    rows["match_duration"] = match_duration

    ordered_columns = [
        "competition_name",
        "season_name",
        "match_id",
        "match_date",
        "home_team",
        "away_team",
        "team_name",
        "player_id",
        "player_name",
        "minutes",
        "position_group",
        "position_group_minutes_share",
        "match_duration",
    ] + count_columns

    return rows[ordered_columns].sort_values(["team_name", "player_name"])
