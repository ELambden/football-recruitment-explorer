"""Build season-level player profiles from player-match features."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from football_recruitment.profiles import build_player_profiles, filter_role_cohort

ROOT = Path(__file__).resolve().parents[1]
PROCESSED_DIR = ROOT / "data" / "processed"
PLAYER_MATCH_PATH = PROCESSED_DIR / "player_match_features.parquet"
PROFILE_PATH = PROCESSED_DIR / "player_profiles.parquet"
CENTRE_FORWARD_PATH = PROCESSED_DIR / "centre_forward_profiles.parquet"
SUMMARY_PATH = PROCESSED_DIR / "player_profile_summary.csv"


def main() -> None:
    if not PLAYER_MATCH_PATH.exists():
        raise FileNotFoundError(
            "Run scripts/build_player_match_features.py before building profiles."
        )

    player_match = pd.read_parquet(PLAYER_MATCH_PATH)
    profiles = build_player_profiles(player_match)
    centre_forwards = filter_role_cohort(
        profiles,
        position_group="Centre Forward",
        min_minutes=900,
        min_position_share=0.60,
    )

    profiles.to_parquet(PROFILE_PATH, index=False)
    centre_forwards.to_parquet(CENTRE_FORWARD_PATH, index=False)

    summary = pd.Series(
        {
            "profiles": len(profiles),
            "centre_forward_profiles_min_900": len(centre_forwards),
            "players": profiles["player_id"].nunique(),
            "competitions": profiles["competition_name"].nunique(),
            "total_minutes": round(float(profiles["minutes"].sum()), 1),
        }
    )
    summary.to_csv(SUMMARY_PATH, header=["value"])

    kane = profiles.loc[
        profiles["player_name"].str.contains("Harry Kane", case=False, na=False)
    ].copy()

    print(f"Wrote {PROFILE_PATH}")
    print(f"Wrote {CENTRE_FORWARD_PATH}")
    print(summary.to_string())
    print()
    print("Harry Kane benchmark rows")
    if kane.empty:
        print("No Harry Kane profile found")
    else:
        display_columns = [
            "competition_name",
            "season_name",
            "player_id",
            "player_name",
            "team_name",
            "minutes",
            "matches",
            "position_group",
            "position_group_minutes_share",
            "non_penalty_xg_p90",
            "non_penalty_shots_p90",
            "xg_assisted_p90",
            "final_third_pressures_p90",
        ]
        print(kane[display_columns].to_string(index=False))


if __name__ == "__main__":
    main()
