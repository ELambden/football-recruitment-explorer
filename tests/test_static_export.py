import json
from pathlib import Path

import pandas as pd

from scripts.export_static_site_data import (
    METRIC_DEFINITIONS,
    add_metric_percentiles,
    build_metrics_data,
    build_players_data,
    build_site_data,
)


def test_metric_presets_reference_defined_metrics() -> None:
    metrics = build_metrics_data()
    metric_ids = {metric["id"] for metric in metrics["metricDefinitions"]}

    for preset in metrics["rolePresets"].values():
        assert set(preset) <= metric_ids


def test_add_metric_percentiles_inverts_ball_security_errors() -> None:
    frame = pd.DataFrame(
        {
            "position_group": ["Centre Forward", "Centre Forward"],
            **{
                metric["id"]: [1.0, 2.0]
                for metric in METRIC_DEFINITIONS
            },
        }
    )
    frame.loc[0, "ball_security_errors_p90"] = 1.0
    frame.loc[1, "ball_security_errors_p90"] = 5.0

    result = add_metric_percentiles(frame)

    assert result.loc[0, "ball_security_errors_p90_role_percentile"] > result.loc[
        1, "ball_security_errors_p90_role_percentile"
    ]
    assert result.loc[1, "non_penalty_xg_p90_role_percentile"] > result.loc[
        0, "non_penalty_xg_p90_role_percentile"
    ]


def test_build_site_data_contains_profiles_and_valid_percentiles() -> None:
    site_data = build_site_data()
    assert site_data["players"]

    metric_ids = {metric["id"] for metric in METRIC_DEFINITIONS}
    deprecated_keys = {
        "similarityRank",
        "similarityPercentile",
        "profileDistance",
        "isTarget",
        "isKaneSimilarityCandidate",
    }
    for player in site_data["players"][:25]:
        assert deprecated_keys.isdisjoint(player)
        assert set(player["metrics"]) == metric_ids
        assert set(player["percentiles"]) == metric_ids
        for value in player["percentiles"].values():
            assert value is None or 0 <= value <= 100


def test_docs_html_references_existing_static_assets() -> None:
    docs = Path("docs")
    if not (docs / "index.html").exists():
        return
    html = (docs / "index.html").read_text(encoding="utf-8")
    assert "styles.css" in html
    assert "app.js" in html
    assert "data/site-data.json" in html or "site-data.json" in html


def test_build_players_data_is_compact_dashboard_contract() -> None:
    site_data = build_site_data()
    players_data = build_players_data(site_data)

    assert players_data["players"]
    player = players_data["players"][0]
    assert set(player) == {"id", "n", "t", "c", "g", "sh", "min", "m", "st", "v", "p"}
    assert set(player["v"]) == {metric["id"] for metric in METRIC_DEFINITIONS}
    assert set(player["p"]) == {metric["id"] for metric in METRIC_DEFINITIONS}
