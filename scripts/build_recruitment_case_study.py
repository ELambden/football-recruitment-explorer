"""Build the Harry Kane recruitment case study and dashboard payload."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

from football_recruitment.case_study import (
    build_recruitment_case_study,
    case_study_to_markdown,
)

ROOT = Path(__file__).resolve().parents[1]
PROCESSED_DIR = ROOT / "data" / "processed"
DOCS_DATA_DIR = ROOT / "docs" / "data"
REPORTS_DIR = ROOT / "reports"

PLAYER_MATCH_PATH = PROCESSED_DIR / "player_match_features.parquet"
PROFILE_PATH = PROCESSED_DIR / "player_profiles.parquet"
CASE_STUDY_PATH = PROCESSED_DIR / "recruitment_case_study.json"
DOCS_CASE_STUDY_PATH = DOCS_DATA_DIR / "case-study.json"
RANKINGS_PATH = PROCESSED_DIR / "recruitment_case_study_rankings.parquet"
RELIABILITY_PATH = PROCESSED_DIR / "recruitment_metric_reliability.csv"
BOOTSTRAP_PATH = PROCESSED_DIR / "recruitment_rank_bootstrap.csv"
SENSITIVITY_PATH = PROCESSED_DIR / "recruitment_weight_sensitivity.csv"
REPORT_PATH = REPORTS_DIR / "harry_kane_recruitment_case_study.md"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--bootstrap-iterations",
        type=int,
        default=100,
        help="Number of deterministic match-resampling iterations for rank intervals.",
    )
    return parser.parse_args()


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> None:
    args = parse_args()
    if not PROFILE_PATH.exists() or not PLAYER_MATCH_PATH.exists():
        raise FileNotFoundError("Run the player-match and profile pipelines before building the case study.")

    profiles = pd.read_parquet(PROFILE_PATH)
    player_match = pd.read_parquet(PLAYER_MATCH_PATH)
    payload, tables = build_recruitment_case_study(
        profiles,
        player_match,
        bootstrap_iterations=args.bootstrap_iterations,
    )

    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    DOCS_DATA_DIR.mkdir(parents=True, exist_ok=True)
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    write_json(CASE_STUDY_PATH, payload)
    write_json(DOCS_CASE_STUDY_PATH, payload)
    tables["rankings"].to_parquet(RANKINGS_PATH, index=False)
    tables["reliability"].to_csv(RELIABILITY_PATH, index=False)
    tables["bootstrap"].to_csv(BOOTSTRAP_PATH, index=False)
    tables["sensitivity"].to_csv(SENSITIVITY_PATH, index=False)
    REPORT_PATH.write_text(case_study_to_markdown(payload), encoding="utf-8")

    print(f"Wrote {DOCS_CASE_STUDY_PATH}")
    print(f"Wrote {CASE_STUDY_PATH}")
    print(f"Wrote {REPORT_PATH}")
    print(f"Candidates: {len(payload['candidates'])}")
    print(f"Bootstrap iterations: {payload['validation']['bootstrapIterations']}")


if __name__ == "__main__":
    main()
