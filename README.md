# Football Recruitment Explorer

Portfolio project for building football-data experience with StatsBomb open event data.

The first case study is a historical recruitment-methodology demo:

> Which centre-forwards in selected 2015/16 StatsBomb open-data competitions most closely reproduce the event-derived profile of a benchmark player?

The intended first benchmark is Harry Kane in the 2015/16 Premier League. This is not a 2026 transfer recommendation model. It is a reproducible demonstration of event-data ingestion, player-match feature engineering, similarity modelling, validation, and Streamlit presentation.

## Data Source

This project uses StatsBomb Open Data. If publishing analysis, credit StatsBomb as the data source and follow their branding requirements.

Primary source:

- StatsBomb Open Data: https://github.com/statsbomb/open-data

The open-data repository stores:

- `competitions.json`
- `matches/{competition_id}/{season_id}.json`
- `events/{match_id}.json`
- `lineups/{match_id}.json`
- `three-sixty/{match_id}.json` for selected matches

Raw StatsBomb data should not be committed to this repository. The project should commit source code, audit outputs, compact processed tables, and written analysis.

## First Milestone

Run a data audit before writing recruitment metrics.

```bash
conda env create -f environment.yml
conda activate football-recruitment
python -m pip install -e .
python scripts/run_data_audit.py
```

The audit writes:

- `data/interim/competition_scope.csv`
- `data/interim/match_coverage.csv`
- `data/interim/sample_event_schema.json`
- `data/interim/sample_event_type_counts.csv`
- `data/interim/sample_lineup_schema.json`

Record the verified match counts here after running the audit:

| Competition | Season | Match count | Team count | Notes |
| --- | --- | ---: | ---: | --- |
| Premier League | 2015/2016 | 380 | 20 | Verified by `scripts/run_data_audit.py` |
| Ligue 1 | 2015/2016 | 377 | 20 | Verified by `scripts/run_data_audit.py` |
| Serie A | 2015/2016 | 380 | 20 | Verified by `scripts/run_data_audit.py` |

## Planned Build Sequence

1. Data audit: verify competition coverage, event schema, lineup schema, and sample coordinate validity.
2. Player-match table: calculate exact minutes, dominant position group, and compact event counts.

```bash
python scripts/build_player_match_features.py
```

This writes `data/processed/player_match_features.parquet` and uses an ignored per-match cache in `data/interim/player_match_by_match/` so interrupted runs can resume.

Current verified output:

| Artifact | Rows | Matches | Players | Competitions |
| --- | ---: | ---: | ---: | ---: |
| `data/processed/player_match_features.parquet` | 31,546 | 1,137 | 1,653 | 3 |

The player-match table currently includes exact lineup minutes, dominant position group, shot volume, non-penalty xG, pass completion counts, pressured passing, box receipts, carries into the box, progressive carry distance, dribbles, pressures, counterpressures, miscontrols, dispossessions, and xG assisted.

3. Player profiles: aggregate centre-forward player-seasons with per-90 and opportunity-adjusted metrics.

```bash
python scripts/build_player_profiles.py
```

Current verified output:

| Artifact | Rows | Notes |
| --- | ---: | --- |
| `data/processed/player_profiles.parquet` | 1,684 | One row per competition-season-player profile |
| `data/processed/centre_forward_profiles.parquet` | 47 | Centre-forwards with 900+ minutes and 60%+ centre-forward share |

Initial benchmark row:

| Player | Player ID | Competition | Team | Minutes | Matches | Centre-forward share |
| --- | ---: | --- | --- | ---: | ---: | ---: |
| Harry Kane | 10,955 | Premier League 2015/2016 | Tottenham Hotspur | 3,486.65 | 38 | 1.00 |

The first profile build includes non-penalty xG per 90, non-penalty shots per 90, average non-penalty xG per shot, box receipts per 90, carries into the box per 90, xG assisted per 90, completed open-play passes per 90, pressured-pass completion, progressive carry distance per 90, successful dribbles per 90, final-third pressures per 90, counterpressures per 90, and ball-security errors per 90. It also adds league-position z-scores for the main role metrics.

4. Similarity model: robust scaling, feature-group weights, and benchmark-player rankings.
5. Validation: split-half reliability, match bootstrap rank intervals, and weight sensitivity.
6. Streamlit app: interactive recruitment explorer, player comparison, and methodology pages.

## Project Structure

```text
app/
  app.py
data/
  raw/
  interim/
  processed/
notebooks/
scripts/
  run_data_audit.py
src/
  football_recruitment/
tests/
```

## Scope And Limitations

The first release focuses on event-derived centre-forward profiles. Event data does not directly measure off-ball runs away from recorded events, acceleration, maximum speed, injury risk, wage feasibility, contract feasibility, personality, tactical instructions, or true league-transfer equivalence.

League-normalised metrics should be described as relative to the observed league and position cohort, not as a full league-strength adjustment.

