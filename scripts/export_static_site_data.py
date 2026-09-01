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
RANKING_PATH = PROCESSED_DIR / "harry_kane_similarity_rankings.parquet"
SITE_DATA_PATH = DOCS_DATA_DIR / "site-data.json"
METRICS_PATH = DOCS_DATA_DIR / "metrics.json"

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
    "ball_security_errors_p90",
]

METRIC_DEFINITIONS = [
    {
        "id": "non_penalty_xg_p90",
        "label": "NP xG/90",
        "shortLabel": "NP xG",
        "group": "Shooting threat",
        "format": ".2f",
        "higherIsBetter": True,
    },
    {
        "id": "non_penalty_shots_p90",
        "label": "NP shots/90",
        "shortLabel": "Shots",
        "group": "Shooting threat",
        "format": ".2f",
        "higherIsBetter": True,
    },
    {
        "id": "average_non_penalty_xg_per_shot",
        "label": "Avg NP xG/shot",
        "shortLabel": "Shot quality",
        "group": "Shooting threat",
        "format": ".3f",
        "higherIsBetter": True,
    },
    {
        "id": "xg_assisted_p90",
        "label": "xG assisted/90",
        "shortLabel": "xA",
        "group": "Link play / creation",
        "format": ".2f",
        "higherIsBetter": True,
    },
    {
        "id": "completed_open_play_passes_p90",
        "label": "Open-play passes completed/90",
        "shortLabel": "OP passes",
        "group": "Link play / creation",
        "format": ".1f",
        "higherIsBetter": True,
    },
    {
        "id": "pressured_pass_completion_pct",
        "label": "Pressured pass completion %",
        "shortLabel": "Pressured pass %",
        "group": "Link play / creation",
        "format": ".1f",
        "higherIsBetter": True,
    },
    {
        "id": "open_play_pass_completion_pct",
        "label": "Open-play pass completion %",
        "shortLabel": "OP pass %",
        "group": "Link play / creation",
        "format": ".1f",
        "higherIsBetter": True,
    },
    {
        "id": "successful_box_receipts_p90",
        "label": "Successful box receipts/90",
        "shortLabel": "Box receives",
        "group": "Box presence / progression",
        "format": ".2f",
        "higherIsBetter": True,
    },
    {
        "id": "carries_into_box_p90",
        "label": "Carries into box/90",
        "shortLabel": "Box carries",
        "group": "Box presence / progression",
        "format": ".2f",
        "higherIsBetter": True,
    },
    {
        "id": "progressive_carry_distance_p90",
        "label": "Progressive carry distance/90",
        "shortLabel": "Carry distance",
        "group": "Box presence / progression",
        "format": ".1f",
        "higherIsBetter": True,
    },
    {
        "id": "successful_dribbles_p90",
        "label": "Successful dribbles/90",
        "shortLabel": "Dribbles",
        "group": "Box presence / progression",
        "format": ".2f",
        "higherIsBetter": True,
    },
    {
        "id": "final_third_pressures_p90",
        "label": "Final-third pressures/90",
        "shortLabel": "F3 pressures",
        "group": "Pressing",
        "format": ".2f",
        "higherIsBetter": True,
    },
    {
        "id": "counterpressures_p90",
        "label": "Counterpressures/90",
        "shortLabel": "Counterpress",
        "group": "Pressing",
        "format": ".2f",
        "higherIsBetter": True,
    },
    {
        "id": "ball_security_errors_p90",
        "label": "Ball-security errors/90",
        "shortLabel": "Ball security",
        "group": "Ball security",
        "format": ".2f",
        "higherIsBetter": False,
        "displayNote": "Lower raw value is better; radar percentile is inverted.",
    },
]

ROLE_PRESETS = {
    "Centre Forward": [
        "non_penalty_xg_p90",
        "non_penalty_shots_p90",
        "successful_box_receipts_p90",
        "xg_assisted_p90",
        "completed_open_play_passes_p90",
        "final_third_pressures_p90",
        "ball_security_errors_p90",
    ],
    "Attacking Midfielder / Winger": [
        "xg_assisted_p90",
        "completed_open_play_passes_p90",
        "successful_dribbles_p90",
        "progressive_carry_distance_p90",
        "carries_into_box_p90",
        "final_third_pressures_p90",
        "ball_security_errors_p90",
    ],
    "Central Midfielder": [
        "completed_open_play_passes_p90",
        "pressured_pass_completion_pct",
        "progressive_carry_distance_p90",
        "xg_assisted_p90",
        "counterpressures_p90",
        "ball_security_errors_p90",
    ],
    "Defensive Midfielder": [
        "completed_open_play_passes_p90",
        "pressured_pass_completion_pct",
        "progressive_carry_distance_p90",
        "final_third_pressures_p90",
        "counterpressures_p90",
        "ball_security_errors_p90",
    ],
    "Full Back / Wing Back": [
        "completed_open_play_passes_p90",
        "open_play_pass_completion_pct",
        "progressive_carry_distance_p90",
        "xg_assisted_p90",
        "final_third_pressures_p90",
        "ball_security_errors_p90",
    ],
    "Centre Back": [
        "completed_open_play_passes_p90",
        "open_play_pass_completion_pct",
        "pressured_pass_completion_pct",
        "progressive_carry_distance_p90",
        "ball_security_errors_p90",
    ],
    "Goalkeeper": [
        "completed_open_play_passes_p90",
        "open_play_pass_completion_pct",
        "pressured_pass_completion_pct",
        "ball_security_errors_p90",
    ],
    "Other": [
        "completed_open_play_passes_p90",
        "non_penalty_shots_p90",
        "xg_assisted_p90",
        "progressive_carry_distance_p90",
        "final_third_pressures_p90",
        "ball_security_errors_p90",
    ],
}

DEFAULT_ROLE = "Centre Forward"
DEFAULT_PLAYERS = [10955, 3018, 20521, 4269]


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


def merge_similarity_fields(profiles: pd.DataFrame) -> pd.DataFrame:
    if not RANKING_PATH.exists():
        profiles["similarity_rank"] = np.nan
        profiles["similarity_percentile"] = np.nan
        profiles["profile_distance"] = np.nan
        profiles["is_target"] = False
        profiles["is_kane_similarity_candidate"] = False
        return profiles

    rankings = pd.read_parquet(RANKING_PATH)[
        [
            "competition_name",
            "season_name",
            "player_id",
            "similarity_rank",
            "similarity_percentile",
            "profile_distance",
            "is_target",
        ]
    ].copy()
    merged = profiles.merge(
        rankings,
        on=["competition_name", "season_name", "player_id"],
        how="left",
    )
    merged["is_target"] = merged["is_target"].fillna(False).astype(bool)
    merged["is_kane_similarity_candidate"] = merged["similarity_rank"].notna()
    return merged


def build_site_data() -> dict[str, Any]:
    if not PROFILE_PATH.exists():
        raise FileNotFoundError("Run scripts/build_player_profiles.py before exporting site data.")

    profiles = pd.read_parquet(PROFILE_PATH)
    missing = set(DASHBOARD_COLUMNS) - set(profiles.columns)
    if missing:
        raise KeyError(f"Missing dashboard columns: {sorted(missing)}")

    profiles = profiles[DASHBOARD_COLUMNS].copy()
    profiles = merge_similarity_fields(profiles)
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
            "similarityRank": _clean_value(row.get("similarity_rank")),
            "similarityPercentile": _clean_value(row.get("similarity_percentile")),
            "profileDistance": _clean_value(row.get("profile_distance")),
            "isTarget": bool(row.get("is_target", False)),
            "isKaneSimilarityCandidate": bool(row.get("is_kane_similarity_candidate", False)),
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
        "defaultPlayerIds": DEFAULT_PLAYERS,
        "players": records,
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
            "similarityRank",
            "similarityPercentile",
        ],
    }


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> None:
    site_data = build_site_data()
    metrics_data = build_metrics_data()
    write_json(SITE_DATA_PATH, site_data)
    write_json(METRICS_PATH, metrics_data)
    print(f"Wrote {SITE_DATA_PATH}")
    print(f"Wrote {METRICS_PATH}")
    print(f"Players: {site_data['scope']['players']}")
    print(f"Metrics: {len(metrics_data['metricDefinitions'])}")


if __name__ == "__main__":
    main()
