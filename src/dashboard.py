"""Streamlit dashboard. Run with: streamlit run src/dashboard.py"""

from __future__ import annotations

import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parent
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from analysis import (
    add_xt_column,
    correlation_matrix,
    match_ratings,
    performance_summary,
    team_match_stats,
    team_ratings,
    team_xt_summary,
)
from cleaner import clean_events
from config import ASSETS_DIR, RAW_EVENTS_FILE
from data_loader import load_raw_data
from momentum import compute_momentum_index, momentum_summary
from player_analysis import compare_players, player_match_stats, player_rating, top_performers
from utils import list_matches

st.set_page_config(
    page_title="Football Tactical Momentum Analyzer",
    page_icon="⚽",
    layout="wide",
)

@st.cache_data(show_spinner="Loading match data...")
def get_data() -> pd.DataFrame:
    raw = load_raw_data(RAW_EVENTS_FILE)
    return clean_events(raw)


df = get_data()

logo_path = ASSETS_DIR / "logo.png"
if logo_path.exists():
    st.sidebar.image(str(logo_path), use_container_width=True)

st.sidebar.title("⚽ Filters")

matches = list_matches(df)
match_labels = {
    row.match_id: f"#{row.match_id}: {row.home_team} vs {row.away_team}"
    for row in matches.itertuples()
}
match_id = st.sidebar.selectbox(
    "Match", options=matches["match_id"], format_func=lambda m: match_labels[m]
)

match_data = df[df["match_id"] == match_id]
teams = sorted(match_data["team"].unique())

minute_range = st.sidebar.slider(
    "Minute range", 0, int(match_data["minute"].max()) + 1,
    (0, int(match_data["minute"].max()) + 1),
)
event_types = st.sidebar.multiselect(
    "Event types", options=sorted(df["event_type"].unique()),
    default=sorted(df["event_type"].unique()),
)

filtered = match_data[
    (match_data["minute"] >= minute_range[0])
    & (match_data["minute"] <= minute_range[1])
    & (match_data["event_type"].isin(event_types))
]

st.sidebar.markdown("---")
st.sidebar.caption(f"{len(df):,} total events loaded across {matches.shape[0]} matches")

st.title("Football Tactical Momentum Analyzer")
st.subheader(match_labels[match_id])

momentum = compute_momentum_index(df, match_id=match_id)

fig = go.Figure()
fig.add_trace(
    go.Scatter(
        x=momentum["minute"], y=momentum["momentum_diff"],
        fill="tozeroy", mode="lines", name="Momentum",
        line=dict(color="#3ddc84"),
    )
)
fig.add_hline(y=0, line_color="white", opacity=0.4)
fig.update_layout(
    template="plotly_dark", height=380,
    xaxis_title="Minute", yaxis_title=f"{teams[0]} <— momentum —> {teams[1]}" if len(teams) == 2 else "Momentum",
    margin=dict(t=20, b=20),
)
st.plotly_chart(fig, use_container_width=True)

if len(teams) == 2:
    summary = momentum_summary(momentum, teams[0], teams[1])
    c1, c2, c3, c4 = st.columns(4)
    c1.metric(f"{teams[0]} minutes led", summary[f"{teams[0]}_minutes_led"])
    c2.metric(f"{teams[1]} minutes led", summary[f"{teams[1]}_minutes_led"])
    c3.metric("Lead changes", summary["lead_changes"])
    c4.metric("Even minutes", summary["even_minutes"])

st.markdown("---")

tab1, tab2, tab3, tab4, tab5 = st.tabs(
    ["📊 Team Stats", "🧑 Players", "🔥 Heatmaps & Shots", "📈 Correlations", "⬇️ Downloads"]
)

with tab1:
    stats = team_match_stats(df)
    ratings = team_ratings(stats)
    perf = performance_summary(stats)

    left, right = st.columns([2, 1])
    with left:
        st.markdown("#### Match stats")
        st.dataframe(stats[stats["match_id"] == match_id], use_container_width=True)
    with right:
        st.markdown("#### Team rating (this match)")
        st.dataframe(ratings[ratings["match_id"] == match_id], use_container_width=True)

    st.markdown("#### Season performance summary")
    st.dataframe(perf, use_container_width=True)

    fig2 = px.bar(perf, x="team", y="xg_per_match", color="team", template="plotly_dark",
                  title="xG per match by team")
    st.plotly_chart(fig2, use_container_width=True)

with tab2:
    p_stats = player_match_stats(df)
    p_ratings = player_rating(df)
    top = top_performers(p_stats, p_ratings, n=10)

    st.markdown("#### Top performers (all matches)")
    st.dataframe(top, use_container_width=True)

    st.markdown("#### Compare two players")
    all_players = sorted(p_stats["player"].unique())
    colA, colB = st.columns(2)
    player_a = colA.selectbox("Player A", all_players, index=0)
    player_b = colB.selectbox("Player B", all_players, index=min(1, len(all_players) - 1))
    comparison = compare_players(p_stats, player_a, player_b)
    st.dataframe(comparison, use_container_width=True)

with tab3:
    st.markdown("#### Filtered events on the pitch")
    fig3 = px.scatter(
        filtered, x="x", y="y", color="team", size="xg",
        hover_data=["player", "event_type", "minute"],
        template="plotly_dark", range_x=[0, 120], range_y=[0, 80],
        title="Event locations",
    )
    fig3.update_yaxes(autorange="reversed")
    st.plotly_chart(fig3, use_container_width=True)

    xt_df = add_xt_column(df)
    xt_summary = team_xt_summary(xt_df)
    st.markdown("#### Expected Threat (xT), this match")
    st.dataframe(xt_summary[xt_summary["match_id"] == match_id], use_container_width=True)

with tab4:
    stats = team_match_stats(df)
    corr = correlation_matrix(stats)
    fig4 = px.imshow(corr, text_auto=".2f", color_continuous_scale="RdBu_r", template="plotly_dark",
                      title="Stat correlation matrix")
    st.plotly_chart(fig4, use_container_width=True)

with tab5:
    st.markdown("#### Export current filtered event data")
    csv_bytes = filtered.to_csv(index=False).encode("utf-8")
    st.download_button("Download filtered events (CSV)", csv_bytes, "filtered_events.csv", "text/csv")

    full_csv = df.to_csv(index=False).encode("utf-8")
    st.download_button("Download all cleaned events (CSV)", full_csv, "events_clean.csv", "text/csv")

    st.info(
        "Run `python src/main.py` to regenerate the full PDF / Excel / HTML report bundle "
        "in the `reports/` folder."
    )
