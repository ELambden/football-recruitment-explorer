"""Season-level player profile aggregation."""

from __future__ import annotations

import numpy as np
import pandas as pd

COUNT_COLUMNS = [
    "event_count",
    "shots",
    "non_penalty_shots",
    "passes_attempted",
    "completed_passes",
    "open_play_passes_attempted",
    "completed_open_play_passes",
    "pressured_passes_attempted",
    "completed_pressured_passes",
    "ball_receipts",
    "successful_ball_receipts",
    "successful_box_receipts",
    "carries",
    "carries_into_box",
    "successful_dribbles",
    "pressures",
    "final_third_pressures",
    "counterpressures",
    "ball_recoveries",
    "interceptions",
    "successful_interceptions",
    "clearances",
    "blocks",
    "tackles",
    "tackles_won",
    "aerial_duels",
    "aerials_won",
    "dribbled_past",
    "fouls_committed",
    "yellow_cards",
    "errors",
    "long_passes_attempted",
    "completed_long_passes",
    "crosses_attempted",
    "completed_crosses",
    "passes_into_box",
    "completed_passes_into_box",
    "passes_into_final_third",
    "completed_passes_into_final_third",
    "carries_into_final_third",
    "goalkeeper_actions",
    "goalkeeper_shots_faced",
    "goalkeeper_saves",
    "miscontrols",
    "dispossessed",
    "non_penalty_xg",
    "xg_assisted",
    "progressive_carry_distance",
]

PROFILE_KEYS = ["competition_name", "season_name", "player_id", "player_name"]


def _safe_divide(numerator: pd.Series, denominator: pd.Series) -> pd.Series:
    denominator = denominator.replace(0, np.nan)
    return numerator / denominator


def _primary_team(values: pd.Series) -> str:
    modes = values.dropna().mode()
    if modes.empty:
        return ""
    return str(modes.iloc[0])


def _team_list(values: pd.Series) -> str:
    teams = sorted({str(value) for value in values.dropna().unique()})
    return " / ".join(teams)


def calculate_position_group_shares(player_match: pd.DataFrame) -> pd.DataFrame:
    """Estimate season dominant position group from match-level role minutes."""

    required = set(PROFILE_KEYS + ["minutes", "position_group", "position_group_minutes_share"])
    missing = required - set(player_match.columns)
    if missing:
        raise KeyError(f"Missing columns: {sorted(missing)}")

    role_minutes = player_match[PROFILE_KEYS + ["position_group", "minutes"]].copy()
    role_minutes["position_group_minutes"] = (
        player_match["minutes"] * player_match["position_group_minutes_share"].fillna(1.0)
    )

    grouped = (
        role_minutes.groupby(PROFILE_KEYS + ["position_group"], as_index=False)[
            "position_group_minutes"
        ]
        .sum()
        .sort_values(PROFILE_KEYS + ["position_group_minutes"], ascending=[True, True, True, True, False])
    )

    totals = player_match.groupby(PROFILE_KEYS, as_index=False)["minutes"].sum().rename(
        columns={"minutes": "total_minutes"}
    )
    grouped = grouped.merge(totals, on=PROFILE_KEYS, how="left")
    grouped["position_group_minutes_share"] = _safe_divide(
        grouped["position_group_minutes"], grouped["total_minutes"]
    )

    dominant = grouped.drop_duplicates(PROFILE_KEYS).drop(columns=["total_minutes"])
    return dominant.reset_index(drop=True)


def add_rate_metrics(profiles: pd.DataFrame) -> pd.DataFrame:
    """Add centre-forward profile metrics as per-90 rates and ratios."""

    result = profiles.copy()
    nineties = result["minutes"] / 90

    per_90_columns = {
        "non_penalty_xg": "non_penalty_xg_p90",
        "non_penalty_shots": "non_penalty_shots_p90",
        "successful_box_receipts": "successful_box_receipts_p90",
        "carries_into_box": "carries_into_box_p90",
        "xg_assisted": "xg_assisted_p90",
        "completed_open_play_passes": "completed_open_play_passes_p90",
        "progressive_carry_distance": "progressive_carry_distance_p90",
        "successful_dribbles": "successful_dribbles_p90",
        "final_third_pressures": "final_third_pressures_p90",
        "counterpressures": "counterpressures_p90",
        "ball_recoveries": "ball_recoveries_p90",
        "interceptions": "interceptions_p90",
        "successful_interceptions": "successful_interceptions_p90",
        "clearances": "clearances_p90",
        "blocks": "blocks_p90",
        "tackles": "tackles_p90",
        "tackles_won": "tackles_won_p90",
        "aerial_duels": "aerial_duels_p90",
        "aerials_won": "aerials_won_p90",
        "dribbled_past": "dribbled_past_p90",
        "fouls_committed": "fouls_committed_p90",
        "yellow_cards": "yellow_cards_p90",
        "errors": "errors_p90",
        "long_passes_attempted": "long_passes_attempted_p90",
        "completed_long_passes": "completed_long_passes_p90",
        "crosses_attempted": "crosses_attempted_p90",
        "completed_crosses": "completed_crosses_p90",
        "passes_into_box": "passes_into_box_p90",
        "completed_passes_into_box": "completed_passes_into_box_p90",
        "passes_into_final_third": "passes_into_final_third_p90",
        "completed_passes_into_final_third": "completed_passes_into_final_third_p90",
        "carries_into_final_third": "carries_into_final_third_p90",
        "goalkeeper_actions": "goalkeeper_actions_p90",
        "goalkeeper_shots_faced": "goalkeeper_shots_faced_p90",
        "goalkeeper_saves": "goalkeeper_saves_p90",
    }

    for source in per_90_columns:
        if source not in result.columns:
            result[source] = 0

    for source, target in per_90_columns.items():
        result[target] = _safe_divide(result[source], nineties)

    for column in [
        "completed_pressured_passes",
        "pressured_passes_attempted",
        "completed_open_play_passes",
        "open_play_passes_attempted",
        "completed_long_passes",
        "long_passes_attempted",
        "completed_crosses",
        "crosses_attempted",
        "tackles_won",
        "tackles",
        "aerials_won",
        "aerial_duels",
        "goalkeeper_saves",
        "goalkeeper_shots_faced",
        "miscontrols",
        "dispossessed",
    ]:
        if column not in result.columns:
            result[column] = 0

    result["average_non_penalty_xg_per_shot"] = _safe_divide(
        result["non_penalty_xg"], result["non_penalty_shots"]
    ).fillna(0)
    result["pressured_pass_completion_pct"] = 100 * _safe_divide(
        result["completed_pressured_passes"], result["pressured_passes_attempted"]
    )
    result["open_play_pass_completion_pct"] = 100 * _safe_divide(
        result["completed_open_play_passes"], result["open_play_passes_attempted"]
    )
    result["long_pass_completion_pct"] = 100 * _safe_divide(
        result["completed_long_passes"], result["long_passes_attempted"]
    )
    result["cross_completion_pct"] = 100 * _safe_divide(
        result["completed_crosses"], result["crosses_attempted"]
    )
    result["tackle_success_pct"] = 100 * _safe_divide(
        result["tackles_won"], result["tackles"]
    )
    result["aerial_win_pct"] = 100 * _safe_divide(
        result["aerials_won"], result["aerial_duels"]
    )
    result["goalkeeper_save_pct"] = 100 * _safe_divide(
        result["goalkeeper_saves"], result["goalkeeper_shots_faced"]
    )
    result["defensive_actions"] = (
        result["ball_recoveries"]
        + result["interceptions"]
        + result["clearances"]
        + result["blocks"]
        + result["tackles"]
    )
    result["defensive_actions_p90"] = _safe_divide(result["defensive_actions"], nineties)
    result["ball_security_errors"] = result["miscontrols"] + result["dispossessed"]
    result["ball_security_errors_p90"] = _safe_divide(
        result["ball_security_errors"], nineties
    )

    return result


def add_league_position_z_scores(
    profiles: pd.DataFrame,
    metric_columns: list[str],
) -> pd.DataFrame:
    """Add league-position normalised z-score columns for selected metrics."""

    result = profiles.copy()
    group_keys = ["competition_name", "season_name", "position_group"]

    for metric in metric_columns:
        mean = result.groupby(group_keys)[metric].transform("mean")
        std = result.groupby(group_keys)[metric].transform("std").replace(0, np.nan)
        result[f"{metric}_league_pos_z"] = (result[metric] - mean) / std

    return result


def build_player_profiles(player_match: pd.DataFrame) -> pd.DataFrame:
    """Aggregate player-match features into one player-season profile row."""

    player_match = player_match.copy()
    for column in COUNT_COLUMNS:
        if column not in player_match.columns:
            player_match[column] = 0

    grouped_counts = player_match.groupby(PROFILE_KEYS, as_index=False)[COUNT_COLUMNS].sum()
    minutes = player_match.groupby(PROFILE_KEYS, as_index=False).agg(
        minutes=("minutes", "sum"),
        matches=("match_id", "nunique"),
        starts=("minutes", lambda values: int((values >= 45).sum())),
        team_name=("team_name", _primary_team),
        teams=("team_name", _team_list),
    )

    profiles = minutes.merge(grouped_counts, on=PROFILE_KEYS, how="left")
    positions = calculate_position_group_shares(player_match)
    profiles = profiles.merge(positions, on=PROFILE_KEYS, how="left")

    profiles = add_rate_metrics(profiles)

    z_metrics = [
        "non_penalty_xg_p90",
        "non_penalty_shots_p90",
        "average_non_penalty_xg_per_shot",
        "successful_box_receipts_p90",
        "carries_into_box_p90",
        "xg_assisted_p90",
        "completed_open_play_passes_p90",
        "progressive_carry_distance_p90",
        "successful_dribbles_p90",
        "final_third_pressures_p90",
        "counterpressures_p90",
        "ball_security_errors_p90",
    ]
    profiles = add_league_position_z_scores(profiles, z_metrics)

    return profiles.sort_values(
        ["competition_name", "season_name", "player_name", "player_id"]
    ).reset_index(drop=True)


def filter_role_cohort(
    profiles: pd.DataFrame,
    *,
    position_group: str,
    min_minutes: float = 900,
    min_position_share: float = 0.60,
) -> pd.DataFrame:
    """Filter profiles to a transparent role and minutes cohort."""

    return profiles.loc[
        profiles["position_group"].eq(position_group)
        & profiles["minutes"].ge(min_minutes)
        & profiles["position_group_minutes_share"].ge(min_position_share)
    ].copy()
