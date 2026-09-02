"""Export processed football profiles for the static GitHub Pages dashboard."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
PROCESSED_DIR = ROOT / "data" / "processed"
DOCS_DATA_DIR = ROOT / "docs" / "data"

PROFILE_PATH = PROCESSED_DIR / "player_profiles.parquet"
SITE_DATA_PATH = DOCS_DATA_DIR / "site-data.json"
METRICS_PATH = DOCS_DATA_DIR / "metrics.json"
PLAYERS_PATH = DOCS_DATA_DIR / "players.json"

DASHBOARD_COLUMNS = [
    "player_id",
    "player_name",
    "team_name",
    "teams",
    "competition_name",
    "season_name",
    "position_group",
    "position_group_minutes_share",
    "minutes",
    "matches",
    "starts",
    "non_penalty_xg_p90",
    "non_penalty_shots_p90",
    "average_non_penalty_xg_per_shot",
    "successful_box_receipts_p90",
    "carries_into_box_p90",
    "xg_assisted_p90",
    "completed_open_play_passes_p90",
    "pressured_pass_completion_pct",
    "open_play_pass_completion_pct",
    "progressive_carry_distance_p90",
    "successful_dribbles_p90",
    "final_third_pressures_p90",
    "counterpressures_p90",
    "ball_recoveries_p90",
    "interceptions_p90",
    "successful_interceptions_p90",
    "clearances_p90",
    "blocks_p90",
    "tackles_p90",
    "tackles_won_p90",
    "tackle_success_pct",
    "aerial_duels_p90",
    "aerials_won_p90",
    "aerial_win_pct",
    "dribbled_past_p90",
    "defensive_actions_p90",
    "long_passes_attempted_p90",
    "completed_long_passes_p90",
    "long_pass_completion_pct",
    "crosses_attempted_p90",
    "completed_crosses_p90",
    "cross_completion_pct",
    "passes_into_box_p90",
    "completed_passes_into_box_p90",
    "passes_into_final_third_p90",
    "completed_passes_into_final_third_p90",
    "carries_into_final_third_p90",
    "fouls_committed_p90",
    "yellow_cards_p90",
    "errors_p90",
    "goalkeeper_actions_p90",
    "goalkeeper_shots_faced_p90",
    "goalkeeper_saves_p90",
    "goalkeeper_save_pct",
    "ball_security_errors_p90",
]

METRIC_DEFINITIONS = [
    {"id": "non_penalty_xg_p90", "label": "NP xG/90", "shortLabel": "NP xG", "group": "Shooting threat", "format": ".2f", "higherIsBetter": True},
    {"id": "non_penalty_shots_p90", "label": "NP shots/90", "shortLabel": "Shots", "group": "Shooting threat", "format": ".2f", "higherIsBetter": True},
    {"id": "average_non_penalty_xg_per_shot", "label": "Avg NP xG/shot", "shortLabel": "Shot quality", "group": "Shooting threat", "format": ".3f", "higherIsBetter": True},
    {"id": "xg_assisted_p90", "label": "xG assisted/90", "shortLabel": "xA", "group": "Creation", "format": ".2f", "higherIsBetter": True},
    {"id": "passes_into_box_p90", "label": "Passes into box/90", "shortLabel": "Box passes", "group": "Creation", "format": ".2f", "higherIsBetter": True},
    {"id": "completed_passes_into_box_p90", "label": "Completed passes into box/90", "shortLabel": "Comp box pass", "group": "Creation", "format": ".2f", "higherIsBetter": True},
    {"id": "passes_into_final_third_p90", "label": "Passes into final third/90", "shortLabel": "F3 passes", "group": "Creation", "format": ".2f", "higherIsBetter": True},
    {"id": "completed_passes_into_final_third_p90", "label": "Completed passes into final third/90", "shortLabel": "Comp F3 pass", "group": "Creation", "format": ".2f", "higherIsBetter": True},
    {"id": "completed_open_play_passes_p90", "label": "Open-play passes completed/90", "shortLabel": "OP passes", "group": "Passing", "format": ".1f", "higherIsBetter": True},
    {"id": "pressured_pass_completion_pct", "label": "Pressured pass completion %", "shortLabel": "Pressured pass %", "group": "Passing", "format": ".1f", "higherIsBetter": True},
    {"id": "open_play_pass_completion_pct", "label": "Open-play pass completion %", "shortLabel": "OP pass %", "group": "Passing", "format": ".1f", "higherIsBetter": True},
    {"id": "long_passes_attempted_p90", "label": "Long passes attempted/90", "shortLabel": "Long pass att", "group": "Passing style", "format": ".2f", "higherIsBetter": True},
    {"id": "completed_long_passes_p90", "label": "Completed long passes/90", "shortLabel": "Long pass comp", "group": "Passing style", "format": ".2f", "higherIsBetter": True},
    {"id": "long_pass_completion_pct", "label": "Long pass completion %", "shortLabel": "Long pass %", "group": "Passing style", "format": ".1f", "higherIsBetter": True},
    {"id": "crosses_attempted_p90", "label": "Crosses attempted/90", "shortLabel": "Cross att", "group": "Passing style", "format": ".2f", "higherIsBetter": True},
    {"id": "completed_crosses_p90", "label": "Completed crosses/90", "shortLabel": "Cross comp", "group": "Passing style", "format": ".2f", "higherIsBetter": True},
    {"id": "cross_completion_pct", "label": "Cross completion %", "shortLabel": "Cross %", "group": "Passing style", "format": ".1f", "higherIsBetter": True},
    {"id": "successful_box_receipts_p90", "label": "Successful box receipts/90", "shortLabel": "Box receives", "group": "Carrying / receiving", "format": ".2f", "higherIsBetter": True},
    {"id": "carries_into_box_p90", "label": "Carries into box/90", "shortLabel": "Box carries", "group": "Carrying / receiving", "format": ".2f", "higherIsBetter": True},
    {"id": "carries_into_final_third_p90", "label": "Carries into final third/90", "shortLabel": "F3 carries", "group": "Carrying / receiving", "format": ".2f", "higherIsBetter": True},
    {"id": "progressive_carry_distance_p90", "label": "Progressive carry distance/90", "shortLabel": "Carry distance", "group": "Carrying / receiving", "format": ".1f", "higherIsBetter": True},
    {"id": "successful_dribbles_p90", "label": "Successful dribbles/90", "shortLabel": "Dribbles", "group": "Carrying / receiving", "format": ".2f", "higherIsBetter": True},
    {"id": "final_third_pressures_p90", "label": "Final-third pressures/90", "shortLabel": "F3 pressures", "group": "Pressing", "format": ".2f", "higherIsBetter": True},
    {"id": "counterpressures_p90", "label": "Counterpressures/90", "shortLabel": "Counterpress", "group": "Pressing", "format": ".2f", "higherIsBetter": True},
    {"id": "defensive_actions_p90", "label": "Defensive actions/90", "shortLabel": "Def actions", "group": "Defending", "format": ".2f", "higherIsBetter": True},
    {"id": "ball_recoveries_p90", "label": "Ball recoveries/90", "shortLabel": "Recoveries", "group": "Defending", "format": ".2f", "higherIsBetter": True},
    {"id": "interceptions_p90", "label": "Interceptions/90", "shortLabel": "Interceptions", "group": "Defending", "format": ".2f", "higherIsBetter": True},
    {"id": "successful_interceptions_p90", "label": "Successful interceptions/90", "shortLabel": "Succ intercep", "group": "Defending", "format": ".2f", "higherIsBetter": True},
    {"id": "clearances_p90", "label": "Clearances/90", "shortLabel": "Clearances", "group": "Defending", "format": ".2f", "higherIsBetter": True},
    {"id": "blocks_p90", "label": "Blocks/90", "shortLabel": "Blocks", "group": "Defending", "format": ".2f", "higherIsBetter": True},
    {"id": "tackles_p90", "label": "Tackles/90", "shortLabel": "Tackles", "group": "Defending", "format": ".2f", "higherIsBetter": True},
    {"id": "tackles_won_p90", "label": "Tackles won/90", "shortLabel": "Tackles won", "group": "Defending", "format": ".2f", "higherIsBetter": True},
    {"id": "tackle_success_pct", "label": "Tackle success %", "shortLabel": "Tackle %", "group": "Defending", "format": ".1f", "higherIsBetter": True},
    {"id": "aerial_duels_p90", "label": "Aerial duels/90", "shortLabel": "Aerial duels", "group": "Aerials", "format": ".2f", "higherIsBetter": True},
    {"id": "aerials_won_p90", "label": "Aerials won/90", "shortLabel": "Aerial wins", "group": "Aerials", "format": ".2f", "higherIsBetter": True},
    {"id": "aerial_win_pct", "label": "Aerial win %", "shortLabel": "Aerial %", "group": "Aerials", "format": ".1f", "higherIsBetter": True},
    {"id": "dribbled_past_p90", "label": "Dribbled past/90", "shortLabel": "Not dribbled", "group": "Defensive security", "format": ".2f", "higherIsBetter": False, "displayNote": "Lower raw value is better; radar percentile is inverted."},
    {"id": "ball_security_errors_p90", "label": "Ball-security errors/90", "shortLabel": "Ball security", "group": "Defensive security", "format": ".2f", "higherIsBetter": False, "displayNote": "Lower raw value is better; radar percentile is inverted."},
    {"id": "fouls_committed_p90", "label": "Fouls committed/90", "shortLabel": "Foul control", "group": "Discipline", "format": ".2f", "higherIsBetter": False, "displayNote": "Lower raw value is better; radar percentile is inverted."},
    {"id": "yellow_cards_p90", "label": "Yellow cards/90", "shortLabel": "Card control", "group": "Discipline", "format": ".2f", "higherIsBetter": False, "displayNote": "Lower raw value is better; radar percentile is inverted."},
    {"id": "errors_p90", "label": "Errors/90", "shortLabel": "Error control", "group": "Discipline", "format": ".2f", "higherIsBetter": False, "displayNote": "Lower raw value is better; radar percentile is inverted."},
    {"id": "goalkeeper_actions_p90", "label": "Goalkeeper actions/90", "shortLabel": "GK actions", "group": "Goalkeeping", "format": ".2f", "higherIsBetter": True},
    {"id": "goalkeeper_shots_faced_p90", "label": "GK shots faced/90", "shortLabel": "Shots faced", "group": "Goalkeeping", "format": ".2f", "higherIsBetter": True, "displayNote": "This is workload, not a quality measure."},
    {"id": "goalkeeper_saves_p90", "label": "GK saves/90", "shortLabel": "Saves", "group": "Goalkeeping", "format": ".2f", "higherIsBetter": True},
    {"id": "goalkeeper_save_pct", "label": "GK save %", "shortLabel": "Save %", "group": "Goalkeeping", "format": ".1f", "higherIsBetter": True},
]

ROLE_PRESETS = {
    "Centre Forward": ["non_penalty_xg_p90", "non_penalty_shots_p90", "successful_box_receipts_p90", "xg_assisted_p90", "completed_open_play_passes_p90", "final_third_pressures_p90", "ball_security_errors_p90"],
    "Attacking Midfielder / Winger": ["xg_assisted_p90", "passes_into_box_p90", "successful_dribbles_p90", "progressive_carry_distance_p90", "carries_into_box_p90", "final_third_pressures_p90", "ball_security_errors_p90"],
    "Central Midfielder": ["completed_open_play_passes_p90", "pressured_pass_completion_pct", "passes_into_final_third_p90", "progressive_carry_distance_p90", "ball_recoveries_p90", "counterpressures_p90", "ball_security_errors_p90"],
    "Defensive Midfielder": ["completed_open_play_passes_p90", "pressured_pass_completion_pct", "ball_recoveries_p90", "interceptions_p90", "tackles_won_p90", "counterpressures_p90", "ball_security_errors_p90"],
    "Full Back / Wing Back": ["completed_open_play_passes_p90", "crosses_attempted_p90", "passes_into_final_third_p90", "progressive_carry_distance_p90", "tackles_won_p90", "final_third_pressures_p90", "ball_security_errors_p90"],
    "Centre Back": ["completed_open_play_passes_p90", "long_pass_completion_pct", "aerials_won_p90", "clearances_p90", "blocks_p90", "interceptions_p90", "dribbled_past_p90"],
    "Goalkeeper": ["goalkeeper_save_pct", "goalkeeper_saves_p90", "goalkeeper_shots_faced_p90", "completed_long_passes_p90", "long_pass_completion_pct", "open_play_pass_completion_pct", "errors_p90"],
    "Other": ["completed_open_play_passes_p90", "non_penalty_shots_p90", "xg_assisted_p90", "progressive_carry_distance_p90", "defensive_actions_p90", "ball_security_errors_p90"],
}


DEFAULT_ROLE = "Centre Forward"


def _clean_value(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, (np.floating, float)):
        if not np.isfinite(value):
            return None
        return round(float(value), 6)
    if isinstance(value, (np.integer, int)):
        return int(value)
    if pd.isna(value):
        return None
    return value


def _role_percentile(values: pd.Series, *, higher_is_better: bool) -> pd.Series:
    numeric = pd.to_numeric(values, errors="coerce")
    if higher_is_better:
        return 100 * numeric.rank(method="average", pct=True)
    return 100 * numeric.rank(method="average", pct=True, ascending=False)


def add_metric_percentiles(profiles: pd.DataFrame) -> pd.DataFrame:
    result = profiles.copy()
    for metric in METRIC_DEFINITIONS:
        metric_id = metric["id"]
        percentile_column = f"{metric_id}_role_percentile"
        result[percentile_column] = result.groupby("position_group", group_keys=False)[
            metric_id
        ].transform(
            lambda values, higher_is_better=metric["higherIsBetter"]: _role_percentile(
                values, higher_is_better=higher_is_better
            )
        )
    return result


def build_site_data() -> dict[str, Any]:
    if not PROFILE_PATH.exists():
        raise FileNotFoundError("Run scripts/build_player_profiles.py before exporting site data.")

    profiles = pd.read_parquet(PROFILE_PATH)
    missing = set(DASHBOARD_COLUMNS) - set(profiles.columns)
    if missing:
        raise KeyError(f"Missing dashboard columns: {sorted(missing)}")

    profiles = profiles[DASHBOARD_COLUMNS].copy()
    profiles = add_metric_percentiles(profiles)

    percentile_columns = [f"{metric['id']}_role_percentile" for metric in METRIC_DEFINITIONS]
    records = []
    for row in profiles.to_dict(orient="records"):
        raw_metrics = {metric["id"]: _clean_value(row.get(metric["id"])) for metric in METRIC_DEFINITIONS}
        percentiles = {
            metric["id"]: _clean_value(row.get(f"{metric['id']}_role_percentile"))
            for metric in METRIC_DEFINITIONS
        }
        record = {
            "playerId": _clean_value(row["player_id"]),
            "playerName": row["player_name"],
            "teamName": row["team_name"],
            "teams": row["teams"],
            "competitionName": row["competition_name"],
            "seasonName": row["season_name"],
            "positionGroup": row["position_group"],
            "positionShare": _clean_value(row["position_group_minutes_share"]),
            "minutes": _clean_value(row["minutes"]),
            "matches": _clean_value(row["matches"]),
            "starts": _clean_value(row["starts"]),
            "metrics": raw_metrics,
            "percentiles": percentiles,
        }
        records.append(record)

    position_groups = sorted(profiles["position_group"].dropna().unique().tolist())
    competitions = sorted(profiles["competition_name"].dropna().unique().tolist())
    teams = sorted(profiles["team_name"].dropna().unique().tolist())

    return {
        "generatedAt": datetime.now(UTC).isoformat(),
        "source": "StatsBomb Open Data",
        "scope": {
            "seasons": sorted(profiles["season_name"].dropna().unique().tolist()),
            "competitions": competitions,
            "positionGroups": position_groups,
            "players": len(records),
        },
        "defaultRole": DEFAULT_ROLE,
        "players": records,
    }


def _round_browser_number(value: Any, digits: int) -> Any:
    value = _clean_value(value)
    if isinstance(value, float):
        return round(value, digits)
    return value


def build_players_data(site_data: dict[str, Any] | None = None) -> dict[str, Any]:
    """Return a compact browser payload for the redesigned static explorer."""

    site_data = site_data or build_site_data()
    players = []
    for player in site_data["players"]:
        players.append(
            {
                "id": f"{player['competitionName']}|{player['seasonName']}|{player['playerId']}",
                "n": player["playerName"],
                "t": player["teamName"],
                "c": player["competitionName"],
                "g": player["positionGroup"],
                "sh": _round_browser_number(player["positionShare"], 2),
                "min": _round_browser_number(player["minutes"], 0),
                "m": _clean_value(player["matches"]),
                "st": _clean_value(player["starts"]),
                "v": {key: _round_browser_number(value, 3) for key, value in player["metrics"].items()},
                "p": {key: _round_browser_number(value, 1) for key, value in player["percentiles"].items()},
            }
        )

    return {
        "generatedAt": site_data["generatedAt"],
        "source": site_data["source"],
        "scope": site_data["scope"],
        "defaultRole": site_data["defaultRole"],
        "players": players,
    }


def build_metrics_data() -> dict[str, Any]:
    return {
        "metricDefinitions": METRIC_DEFINITIONS,
        "rolePresets": ROLE_PRESETS,
        "defaultRole": DEFAULT_ROLE,
        "defaultMetricIds": ROLE_PRESETS[DEFAULT_ROLE],
        "tableColumns": [
            "playerName",
            "teamName",
            "competitionName",
            "positionGroup",
            "minutes",
            "matches",
            "starts",
        ],
    }


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def write_compact_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")


def main() -> None:
    site_data = build_site_data()
    metrics_data = build_metrics_data()
    players_data = build_players_data(site_data)
    write_json(SITE_DATA_PATH, site_data)
    write_compact_json(PLAYERS_PATH, players_data)
    write_json(METRICS_PATH, metrics_data)
    print(f"Wrote {SITE_DATA_PATH}")
    print(f"Wrote {PLAYERS_PATH}")
    print(f"Wrote {METRICS_PATH}")
    print(f"Players: {site_data['scope']['players']}")
    print(f"Metrics: {len(metrics_data['metricDefinitions'])}")


if __name__ == "__main__":
    main()
