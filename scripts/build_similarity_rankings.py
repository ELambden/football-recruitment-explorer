"""Build baseline centre-forward similarity rankings."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from football_recruitment.similarity import (
    CENTRE_FORWARD_FEATURE_COLUMNS,
    calculate_similarity,
    default_centre_forward_feature_weights,
)

ROOT = Path(__file__).resolve().parents[1]
PROCESSED_DIR = ROOT / "data" / "processed"
CENTRE_FORWARD_PATH = PROCESSED_DIR / "centre_forward_profiles.parquet"
RANKING_PATH = PROCESSED_DIR / "harry_kane_similarity_rankings.parquet"
RANKING_CSV_PATH = PROCESSED_DIR / "harry_kane_similarity_top20.csv"
SUMMARY_PATH = PROCESSED_DIR / "similarity_summary.csv"
FEATURE_WEIGHTS_PATH = PROCESSED_DIR / "centre_forward_similarity_feature_weights.csv"
REPORT_PATH = ROOT / "reports" / "harry_kane_similarity.md"

TARGET_PLAYER_ID = 10955
TARGET_PLAYER_NAME = "Harry Kane"



def _format_cell(value: object) -> str:
    if isinstance(value, float):
        return f"{value:.3f}"
    return str(value)


def dataframe_to_markdown(frame: pd.DataFrame) -> str:
    """Render a small DataFrame as a GitHub-flavoured markdown table."""

    columns = list(frame.columns)
    rows = [[_format_cell(value) for value in row] for row in frame.to_numpy()]
    header = "| " + " | ".join(columns) + " |"
    separator = "| " + " | ".join(["---"] * len(columns)) + " |"
    body = ["| " + " | ".join(row) + " |" for row in rows]
    return "\n".join([header, separator, *body])


DISPLAY_COLUMNS = [
    "candidate_rank",
    "similarity_rank",
    "similarity_percentile",
    "profile_distance",
    "player_id",
    "player_name",
    "team_name",
    "competition_name",
    "minutes",
    "matches",
    "non_penalty_xg_p90",
    "non_penalty_shots_p90",
    "average_non_penalty_xg_per_shot",
    "successful_box_receipts_p90",
    "xg_assisted_p90",
    "completed_open_play_passes_p90",
    "final_third_pressures_p90",
    "counterpressures_p90",
    "ball_security_errors_p90",
]


def main() -> None:
    if not CENTRE_FORWARD_PATH.exists():
        raise FileNotFoundError(
            "Run scripts/build_player_profiles.py before building similarity rankings."
        )

    centre_forwards = pd.read_parquet(CENTRE_FORWARD_PATH)
    feature_weights = default_centre_forward_feature_weights()

    rankings = calculate_similarity(
        centre_forwards,
        target_player_id=TARGET_PLAYER_ID,
        feature_columns=CENTRE_FORWARD_FEATURE_COLUMNS,
        feature_weights=feature_weights,
    )

    rankings.to_parquet(RANKING_PATH, index=False)

    candidates = rankings.loc[~rankings["is_target"]].copy()
    candidates["candidate_rank"] = range(1, len(candidates) + 1)
    top20 = candidates[DISPLAY_COLUMNS].head(20).copy()
    top20.to_csv(RANKING_CSV_PATH, index=False)

    feature_weights = pd.Series(feature_weights, name="weight").rename_axis("feature").reset_index()
    feature_weights.to_csv(FEATURE_WEIGHTS_PATH, index=False)

    summary = pd.Series(
        {
            "target_player_id": TARGET_PLAYER_ID,
            "target_player_name": TARGET_PLAYER_NAME,
            "ranked_profiles": len(rankings),
            "candidate_profiles_excluding_target": int((~rankings["is_target"]).sum()),
            "feature_count": len(CENTRE_FORWARD_FEATURE_COLUMNS),
        }
    )
    summary.to_csv(SUMMARY_PATH, header=["value"])

    target = rankings.loc[rankings["is_target"]].iloc[0]
    report_lines = [
        "# Harry Kane Similarity Shortlist",
        "",
        "Baseline centre-forward profile similarity using StatsBomb open event data.",
        "",
        "## Benchmark",
        "",
        (
            f"Harry Kane, Tottenham Hotspur, Premier League 2015/2016. "
            f"Player ID `{int(target['player_id'])}`; "
            f"minutes `{target['minutes']:.2f}`; "
            f"matches `{int(target['matches'])}`."
        ),
        "",
        "## Method",
        "",
        (
            "The model filters to centre-forwards with at least 900 minutes and "
            "at least 60% of their minutes at centre-forward. It compares players "
            "with robust-scaled, league-position-normalised role metrics and "
            "feature-group weights for threat, link play, progression, pressing "
            "and ball security."
        ),
        "",
        "Similarity is a relative ranking inside this historical reference cohort, "
        "not a statement that one player is a transfer recommendation or a universal "
        "percentage match.",
        "",
        "## Top 10 Candidates",
        "",
        dataframe_to_markdown(top20.head(10)),
        "",
        "## Feature Weights",
        "",
        dataframe_to_markdown(feature_weights),
        "",
    ]
    REPORT_PATH.write_text("\n".join(report_lines), encoding="utf-8")

    print(f"Wrote {RANKING_PATH}")
    print(f"Wrote {RANKING_CSV_PATH}")
    print(f"Wrote {FEATURE_WEIGHTS_PATH}")
    print(f"Wrote {REPORT_PATH}")
    print(summary.to_string())
    print()
    print(f"Top 10 profile alternatives to {TARGET_PLAYER_NAME}")
    print(top20.head(10).to_string(index=False))


if __name__ == "__main__":
    main()
