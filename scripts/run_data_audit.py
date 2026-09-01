"""Run the first StatsBomb open-data audit."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
from statsbombpy import sb

from football_recruitment.data_audit import (
    build_match_coverage,
    event_schema_report,
    lineup_schema_report,
    select_competitions,
    validate_event_locations,
    write_json,
)


ROOT = Path(__file__).resolve().parents[1]
INTERIM_DIR = ROOT / "data" / "interim"


def main() -> None:
    INTERIM_DIR.mkdir(parents=True, exist_ok=True)

    competitions = sb.competitions()
    selected = select_competitions(competitions)
    if selected.empty:
        raise RuntimeError("No configured competitions were found in StatsBomb open data")

    selected.to_csv(INTERIM_DIR / "competition_scope.csv", index=False)

    matches_by_key = {}
    for row in selected.itertuples(index=False):
        matches = sb.matches(
            competition_id=int(row.competition_id),
            season_id=int(row.season_id),
        ).copy()
        if not matches["match_id"].is_unique:
            raise ValueError(
                f"Duplicate match IDs in {row.competition_name} {row.season_name}"
            )
        matches_by_key[(int(row.competition_id), int(row.season_id))] = matches

    coverage = build_match_coverage(selected, matches_by_key)
    coverage.to_csv(INTERIM_DIR / "match_coverage.csv", index=False)

    sample_key = (
        int(selected.iloc[0]["competition_id"]),
        int(selected.iloc[0]["season_id"]),
    )
    sample_match_id = int(matches_by_key[sample_key].iloc[0]["match_id"])

    events = sb.events(match_id=sample_match_id)
    if not events["id"].notna().all():
        raise ValueError("Sample event table has null event IDs")
    if not events["id"].is_unique:
        raise ValueError("Sample event table has duplicate event IDs")
    if "match_id" in events and not events["match_id"].eq(sample_match_id).all():
        raise ValueError("Sample event table contains an unexpected match ID")
    validate_event_locations(events)

    lineups = sb.lineups(match_id=sample_match_id, fmt="dict")

    write_json(
        INTERIM_DIR / "sample_event_schema.json",
        {"sample_match_id": sample_match_id, **event_schema_report(events)},
    )
    events["type"].value_counts().rename_axis("event_type").reset_index(
        name="count"
    ).to_csv(INTERIM_DIR / "sample_event_type_counts.csv", index=False)
    write_json(
        INTERIM_DIR / "sample_lineup_schema.json",
        {"sample_match_id": sample_match_id, **lineup_schema_report(lineups)},
    )

    print("Selected competitions")
    print(selected.to_string(index=False))
    print()
    print("Match coverage")
    print(coverage.to_string(index=False))
    print()
    print(f"Sample match ID: {sample_match_id}")
    print(f"Audit outputs written to {INTERIM_DIR}")


if __name__ == "__main__":
    main()

