# Football Recruitment Explorer

An interactive portfolio project built with StatsBomb Open Data. It shows how event data can be turned into clear, football-specific player profiles and visual tools for comparing recruitment options.

The dashboard focuses on the 2015/16 Premier League, Ligue 1, and Serie A seasons. It is a historical analysis tool, not a live transfer model. Its purpose is to show careful data handling, thoughtful football interpretation, and polished visual presentation.

## What This Shows

This project is designed to demonstrate that I can:

- work with real football event data from StatsBomb
- clean and check a dataset before drawing conclusions from it
- turn match events into useful player-level measures
- compare players by role, not just by raw totals
- build clear football visuals for scouting-style exploration
- explain the limits of the data honestly
- package the work into a reproducible public portfolio project

## The Dashboard

The main output is a static web dashboard in `docs/`, designed to run on GitHub Pages without a Python server.

It includes:

- a pitch-based role selector for exploring different position groups
- filters for competition, team, minutes played, and player name
- a compare tray for pinning up to four players
- a radar chart using role-based percentiles
- percentile strips showing raw values beside profile context
- a landscape scatter plot with axis values, grid lines, and quadrant labels
- browser-side nearest-profile matching based on selected metrics
- a sortable player ledger with the selected metrics
- URL-shareable dashboard state

The dashboard uses precomputed JSON files, so the browser only has to render the final player profiles and visuals.

Local preview:

```bash
python -m http.server 8000 --directory docs
```

Then open:

```text
http://localhost:8000
```

## Data Source

This project uses [StatsBomb Open Data](https://github.com/statsbomb/open-data).

The current scope is:

| Competition | Season | Matches | Teams |
| --- | --- | ---: | ---: |
| Premier League | 2015/2016 | 380 | 20 |
| Ligue 1 | 2015/2016 | 377 | 20 |
| Serie A | 2015/2016 | 380 | 20 |

Raw StatsBomb files are not committed to this repository. The repo contains source code, compact processed outputs, dashboard data, tests, and written reports.

## How The Analysis Works

The pipeline has four main stages.

1. Data audit

Checks the selected competitions, match coverage, event fields, lineup fields, and sample pitch coordinates.

```bash
python scripts/run_data_audit.py
```

2. Player-match features

Builds one row per player per match. This step calculates minutes played from lineup data and counts useful event actions such as shots, xG, passes, box receipts, carries, pressures, tackles, aerials, goalkeeper actions, miscontrols, and dispossessions.

```bash
python scripts/build_player_match_features.py
```

Current output:

| Output | Rows | Matches | Players | Competitions |
| --- | ---: | ---: | ---: | ---: |
| `data/processed/player_match_features.parquet` | 31,546 | 1,137 | 1,653 | 3 |

3. Player profiles

Aggregates match rows into player-season profiles. Metrics are converted into per-90 rates where useful, and each player is assigned a dominant position group.

```bash
python scripts/build_player_profiles.py
```

Current output:

| Output | Rows | Notes |
| --- | ---: | --- |
| `data/processed/player_profiles.parquet` | 1,684 | One row per player, competition, and season |
| `data/processed/centre_forward_profiles.parquet` | 47 | Centre-forwards with 900+ minutes and 60%+ role share |

4. Dashboard export

Creates the JSON files used by the static dashboard.

```bash
python scripts/export_static_site_data.py
```

## Similarity And Validation

The project also includes a centre-forward similarity example using Harry Kane's 2015/16 profile as the benchmark.

```bash
python scripts/build_similarity_rankings.py
python scripts/build_recruitment_case_study.py
```

These scripts are kept as technical evidence rather than the main website experience. They show how a shortlist can be created and checked using:

- role and minutes filters
- robust scaling so extreme values do not dominate the comparison
- league-and-position context for the main role metrics
- feature weights grouped around threat, link play, progression, pressing, and ball security
- split-half reliability checks
- bootstrap rank intervals
- weight-sensitivity checks

The key point is profile similarity, not player quality and not transfer advice.

## Running The Project

Create the environment:

```bash
conda env create -f environment.yml
conda activate football-recruitment
python -m pip install -e .
```

Run the full local checks:

```bash
conda run -n football-recruitment pytest -q
node --check docs/app.js
```

Regenerate the main processed outputs:

```bash
python scripts/run_data_audit.py
python scripts/build_player_match_features.py
python scripts/build_player_profiles.py
python scripts/export_static_site_data.py
```

## Repository Guide

```text
docs/       Static dashboard for GitHub Pages
data/       Audit outputs and compact processed tables
reports/    Written shortlist/report outputs
scripts/    Reproducible pipeline entry points
src/        Reusable Python analysis code
tests/      Unit and export-contract tests
```

## Limits Of The Work

This project uses one historical season across three open-data leagues. That is enough for strong descriptive analysis and player-profile comparison, but not enough for a serious future-performance model.

The data does not include everything a real recruitment department would need. It does not cover age, contracts, wages, injuries, physical testing, personality, tactical instructions, scouting video, or true league-strength adjustments.

For that reason, the project is best read as a football analytics and visualisation sample: a clear, reproducible way to turn event data into useful player comparisons.
