"""Build compact player-match features from StatsBomb open data.

The script writes one compact cache file per match before combining them into
`data/processed/player_match_features.parquet`. That makes long open-data pulls
resumable without committing raw StatsBomb event files.
"""

from __future__ import annotations

import argparse
import shutil
import warnings
from pathlib import Path

import pandas as pd
from statsbombpy import sb
from statsbombpy.api_client import NoAuthWarning

from football_recruitment.data_audit import build_match_coverage, select_competitions
from football_recruitment.features import build_player_match_features

ROOT = Path(__file__).resolve().parents[1]
INTERIM_DIR = ROOT / "data" / "interim"
PROCESSED_DIR = ROOT / "data" / "processed"
MATCH_CACHE_DIR = INTERIM_DIR / "player_match_by_match"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--limit-matches",
        type=int,
        default=None,
        help="Optional per-competition match limit for fast development runs.",
    )
    parser.add_argument(
        "--rebuild-cache",
        action="store_true",
        help="Delete cached player-match files before building.",
    )
    return parser.parse_args()


def _cache_path(match_id: int) -> Path:
    return MATCH_CACHE_DIR / f"{match_id}.parquet"


def _build_or_load_match(match: dict) -> pd.DataFrame:
    match_id = int(match["match_id"])
    cache_path = _cache_path(match_id)
    if cache_path.exists():
        return pd.read_parquet(cache_path)

    events = sb.events(match_id=match_id)
    lineups = sb.lineups(match_id=match_id, fmt="dict")
    rows = build_player_match_features(
        events=events,
        lineups=lineups,
        match_metadata=match,
    )
    rows.to_parquet(cache_path, index=False)
    return rows


def main() -> None:
    args = parse_args()
    warnings.filterwarnings("ignore", category=NoAuthWarning)

    if args.rebuild_cache and MATCH_CACHE_DIR.exists():
        shutil.rmtree(MATCH_CACHE_DIR)

    MATCH_CACHE_DIR.mkdir(parents=True, exist_ok=True)
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    competitions = sb.competitions()
    selected = select_competitions(competitions)
    if selected.empty:
        raise RuntimeError("No configured competitions were found in StatsBomb open data")

    all_rows: list[pd.DataFrame] = []
    matches_by_key: dict[tuple[int, int], pd.DataFrame] = {}

    for competition in selected.itertuples(index=False):
        matches = sb.matches(
            competition_id=int(competition.competition_id),
            season_id=int(competition.season_id),
        ).copy()
        matches["competition_name"] = competition.competition_name
        matches["season_name"] = competition.season_name
        matches_by_key[(int(competition.competition_id), int(competition.season_id))] = matches

        if args.limit_matches is not None:
            matches = matches.head(args.limit_matches)

        total = len(matches)
        print(f"Processing {competition.competition_name}: {total} matches", flush=True)
        for index, match in enumerate(matches.to_dict(orient="records"), start=1):
            match_id = int(match["match_id"])
            cache_exists = _cache_path(match_id).exists()
            rows = _build_or_load_match(match)
            all_rows.append(rows)

            if index == 1 or index % 25 == 0 or index == total:
                verb = "cached" if cache_exists else "built"
                print(
                    f"  {competition.competition_name}: {index}/{total} "
                    f"matches ({verb} {match_id})",
                    flush=True,
                )

    if not all_rows:
        raise RuntimeError("No player-match rows were produced")

    player_match = pd.concat(all_rows, ignore_index=True)
    output_path = PROCESSED_DIR / "player_match_features.parquet"
    player_match.to_parquet(output_path, index=False)

    summary = pd.Series(
        {
            "rows": len(player_match),
            "matches": player_match["match_id"].nunique(),
            "players": player_match["player_id"].nunique(),
            "competitions": player_match["competition_name"].nunique(),
        }
    )

    coverage = build_match_coverage(selected, matches_by_key)
    coverage.to_csv(INTERIM_DIR / "match_coverage.csv", index=False)
    summary.to_csv(PROCESSED_DIR / "player_match_summary.csv", header=["value"])

    print(f"Wrote {output_path}", flush=True)
    print(summary.to_string(), flush=True)
    print("", flush=True)
    print("Source match coverage", flush=True)
    print(coverage.to_string(index=False), flush=True)


if __name__ == "__main__":
    main()
