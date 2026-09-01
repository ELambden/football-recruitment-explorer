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


def _moves_into_final_third(start: Any, end: Any) -> bool:
    start_x = _x(start)
    end_x = _x(end)
    return (
        start_x is not None
        and end_x is not None
        and start_x < ATTACKING_THIRD_X_MIN <= end_x
    )


def _column(events: pd.DataFrame, column: str, default: Any = None) -> pd.Series:
    if column not in events:
        return pd.Series(default, index=events.index)
    return events[column]


def _truthy_column(events: pd.DataFrame, column: str) -> pd.Series:
    return _column(events, column, False).fillna(False).astype(bool)


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
    under_pressure_mask = _truthy_column(player_events, "under_pressure")

    shot_mask = event_type.eq("Shot")
    non_penalty_shot_mask = shot_mask & ~player_events["shot_type"].eq("Penalty")
    carry_mask = event_type.eq("Carry")
    pressure_mask = event_type.eq("Pressure")
    tackle_mask = event_type.eq("Duel") & _column(player_events, "duel_type").eq("Tackle")
    tackle_won_mask = tackle_mask & _column(player_events, "duel_outcome").isin(
        ["Won", "Success In Play", "Success Out"]
    )
    aerial_duel_mask = event_type.eq("Duel") & _column(player_events, "duel_type").eq("Aerial Lost")
    aerial_won_mask = (
        _truthy_column(player_events, "pass_aerial_won")
        | _truthy_column(player_events, "clearance_aerial_won")
        | _truthy_column(player_events, "shot_aerial_won")
    )
    interception_mask = event_type.eq("Interception")
    successful_interception_mask = interception_mask & _column(player_events, "interception_outcome").isin(
        ["Won", "Success In Play", "Success Out"]
    )
    long_pass_mask = pass_mask & _column(player_events, "pass_height").eq("High Pass")
    completed_long_pass_mask = long_pass_mask & player_events["pass_outcome"].isna()
    cross_mask = pass_mask & _truthy_column(player_events, "pass_cross")
    completed_cross_mask = cross_mask & player_events["pass_outcome"].isna()
    pass_into_box_mask = pass_mask & _column(player_events, "pass_end_location").map(_inside_box)
    completed_pass_into_box_mask = pass_into_box_mask & player_events["pass_outcome"].isna()
    pass_into_final_third_mask = pass_mask & player_events.apply(
        lambda row: _moves_into_final_third(row.get("location"), row.get("pass_end_location")),
        axis=1,
    )
    completed_pass_into_final_third_mask = (
        pass_into_final_third_mask & player_events["pass_outcome"].isna()
    )
    carry_into_final_third_mask = carry_mask & player_events.apply(
        lambda row: _moves_into_final_third(row.get("location"), row.get("carry_end_location")),
        axis=1,
    )
    goalkeeper_mask = event_type.eq("Goal Keeper")
    goalkeeper_save_mask = goalkeeper_mask & _column(player_events, "goalkeeper_type").isin(
        ["Shot Saved", "Save"]
    )
    goalkeeper_shot_faced_mask = goalkeeper_mask & _column(player_events, "goalkeeper_type").isin(
        ["Shot Faced", "Shot Saved", "Goal Conceded", "Save", "Penalty Conceded"]
    )

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
        "counterpressures": pressure_mask & _truthy_column(player_events, "counterpress"),
        "ball_recoveries": event_type.eq("Ball Recovery"),
        "interceptions": interception_mask,
        "successful_interceptions": successful_interception_mask,
        "clearances": event_type.eq("Clearance"),
        "blocks": event_type.eq("Block"),
        "tackles": tackle_mask,
        "tackles_won": tackle_won_mask,
        "aerial_duels": aerial_duel_mask | aerial_won_mask,
        "aerials_won": aerial_won_mask,
        "dribbled_past": event_type.eq("Dribbled Past"),
        "fouls_committed": event_type.eq("Foul Committed"),
        "yellow_cards": event_type.eq("Foul Committed")
        & _column(player_events, "foul_committed_card").isin(["Yellow Card", "Second Yellow"]),
        "errors": event_type.eq("Error"),
        "long_passes_attempted": long_pass_mask,
        "completed_long_passes": completed_long_pass_mask,
        "crosses_attempted": cross_mask,
        "completed_crosses": completed_cross_mask,
        "passes_into_box": pass_into_box_mask,
        "completed_passes_into_box": completed_pass_into_box_mask,
        "passes_into_final_third": pass_into_final_third_mask,
        "completed_passes_into_final_third": completed_pass_into_final_third_mask,
        "carries_into_final_third": carry_into_final_third_mask,
        "goalkeeper_actions": goalkeeper_mask,
        "goalkeeper_shots_faced": goalkeeper_shot_faced_mask,
        "goalkeeper_saves": goalkeeper_save_mask,
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
