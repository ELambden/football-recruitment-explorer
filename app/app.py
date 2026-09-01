from pathlib import Path

import pandas as pd
import streamlit as st


PROFILE_PATH = Path("data/processed/player_profiles.parquet")


@st.cache_data
def load_profiles() -> pd.DataFrame:
    if not PROFILE_PATH.exists():
        raise FileNotFoundError(
            "Run the profile-building pipeline before launching the app."
        )
    return pd.read_parquet(PROFILE_PATH)


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

available_players = (
    filtered["player_name"].dropna().sort_values().drop_duplicates().tolist()
)
benchmark = st.sidebar.selectbox("Benchmark player", options=available_players)

st.subheader(f"Profile alternatives to {benchmark}")

display_columns = [
    "player_name",
    "team_name",
    "competition_name",
    "minutes",
    "similarity_percentile",
    "archetype",
]
existing_columns = [column for column in display_columns if column in filtered.columns]

st.dataframe(
    filtered[existing_columns]
    .sort_values("similarity_percentile", ascending=False)
    .head(20),
    use_container_width=True,
    hide_index=True,
)

st.caption(
    "Event data: StatsBomb Open Data. Similarity describes event-derived profile "
    "proximity within the reference population and is not a transfer recommendation."
)

