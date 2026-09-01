from pathlib import Path

import pandas as pd
import streamlit as st


PROFILE_PATH = Path("data/processed/player_profiles.parquet")
RANKING_PATH = Path("data/processed/harry_kane_similarity_rankings.parquet")


@st.cache_data
def load_profiles() -> pd.DataFrame:
    if RANKING_PATH.exists():
        return pd.read_parquet(RANKING_PATH)
    if PROFILE_PATH.exists():
        return pd.read_parquet(PROFILE_PATH)
    raise FileNotFoundError("Run the profile-building pipeline before launching the app.")


st.set_page_config(page_title="Recruitment Explorer", layout="wide")
st.title("Centre-Forward Recruitment Explorer")

try:
    profiles = load_profiles()
except FileNotFoundError as exc:
    st.info(str(exc))
    st.stop()

minimum_minutes = st.sidebar.slider(
    "Minimum minutes",
    min_value=450,
    max_value=2500,
    value=900,
    step=90,
)

filtered = profiles.loc[profiles["minutes"] >= minimum_minutes].copy()

if "is_target" in filtered.columns:
    filtered = filtered.loc[~filtered["is_target"]].copy()

if "similarity_percentile" in profiles.columns:
    benchmark = st.sidebar.selectbox("Benchmark player", options=["Harry Kane"])
else:
    available_players = (
        profiles["player_name"].dropna().sort_values().drop_duplicates().tolist()
    )
    benchmark = st.sidebar.selectbox("Benchmark player", options=available_players)

st.subheader(f"Profile alternatives to {benchmark}")

if "similarity_percentile" in filtered.columns:
    filtered = filtered.sort_values("similarity_percentile", ascending=False)
else:
    st.info("Similarity rankings are not available yet. Run scripts/build_similarity_rankings.py.")
    filtered = filtered.sort_values("minutes", ascending=False)

display_columns = [
    "similarity_rank",
    "similarity_percentile",
    "profile_distance",
    "player_name",
    "team_name",
    "competition_name",
    "minutes",
    "matches",
    "position_group",
    "non_penalty_xg_p90",
    "non_penalty_shots_p90",
    "xg_assisted_p90",
    "final_third_pressures_p90",
]
existing_columns = [column for column in display_columns if column in filtered.columns]

st.dataframe(
    filtered[existing_columns].head(20),
    use_container_width=True,
    hide_index=True,
)

st.caption(
    "Event data: StatsBomb Open Data. Similarity describes event-derived profile "
    "proximity within the reference population and is not a transfer recommendation."
)
