# Streamlit dashboard. Run with: streamlit run src/dashboard.py

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
from config import ASSETS_DIR, RAW_EVENTS_FILE, REPORTS_DIR
from data_loader import load_raw_data
from momentum import compute_momentum_index, momentum_summary
from player_analysis import compare_players, player_match_stats, player_rating, top_performers
from utils import list_matches

# Mapping from nice display names back to underscore format for internal code
REVERSE_COLUMN_MAPPING = {
    "Match Id": "match_id",
    "Team": "team",
    "Events": "events",
    "Passes": "passes",
    "Pass Accuracy Pct": "pass_accuracy_pct",
    "Shots": "shots",
    "Shots On Target": "shots_on_target",
    "Goals": "goals",
    "Xg": "xg",
    "Fouls": "fouls",
    "Tackles": "tackles",
    "Interceptions": "interceptions",
    "Yellow Cards": "yellow_cards",
    "Red Cards": "red_cards",
    "Possession Pct": "possession_pct",
    "Team Rating": "team_rating",
    "Match Quality": "match_quality",
    "Competitiveness Spread": "competitiveness_spread",
    "Top Team Rating": "top_team_rating",
    "Bottom Team Rating": "bottom_team_rating",
    "Matches": "matches",
    "Avg Possession Pct": "avg_possession_pct",
    "Avg Pass Accuracy Pct": "avg_pass_accuracy_pct",
    "Goals Per Match": "goals_per_match",
    "Xg Per Match": "xg_per_match",
    "Shot Conversion Pct": "shot_conversion_pct",
    "Player": "player",
    "Rating": "rating",
    "Position": "position",
    "Dribbles": "dribbles",
    "Total Xt": "total_xt",
    "Stat": "stat",
}

# Mapping for display: from underscore to nice format
DISPLAY_COLUMN_MAPPING = {v: k for k, v in REVERSE_COLUMN_MAPPING.items()}

def rename_columns_to_underscore(df: pd.DataFrame) -> pd.DataFrame:
    """Rename columns from nice display format to underscore format."""
    return df.rename(columns=REVERSE_COLUMN_MAPPING)

def rename_columns_for_display(df: pd.DataFrame) -> pd.DataFrame:
    """Rename columns from underscore format to nice display format."""
    return df.rename(columns=DISPLAY_COLUMN_MAPPING)

st.set_page_config(
    page_title="Football Tactical Momentum Analyzer",
    page_icon="⚽",
    layout="wide",
)

BRAND_CSS = """
<style>
    :root {
        --mint: #cdf5bd;
        --sage: #9bcaa8;
        --forest: #102a22;
        --panel: #173b35;
        --panel-soft: #24483f;
        --grid: #5b9b8c;
        --cream: #f8fbf4;
        --ink: #f6f7f2;
        --navy: #090a28;
        --peach: #ffbd78;
        --butter: #fff0a8;
        --teal: #4f9b92;
    }

    .stApp {
        background: #E5E4E2;
        color: var(--ink);
    }

    [data-testid="stAppViewContainer"],
    [data-testid="stMain"] {
        background: #ffffff;
    }

    [data-testid="stHeader"] {
        background: transparent;
    }

    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #c9f1bf, #1d4750);
        border-right: 2px solid rgba(255, 255, 255, .18);
    }

    section[data-testid="stSidebar"] h1,
    section[data-testid="stSidebar"] h2,
    section[data-testid="stSidebar"] h3,
    section[data-testid="stSidebar"] label,
    section[data-testid="stSidebar"] p {
        color: #ffffff;
    }

    .block-container {
        padding-top: 3.2rem;
        max-width: 1500px;
    }

    .dash-hero {
        display: flex;
        align-items: center;
        gap: 28px;
        background: var(--forest);
        color: var(--ink);
        padding: 24px 28px;
        border-radius: 6px;
        box-shadow: 0 18px 38px rgba(10, 33, 35, .2);
        margin: 0 0 1rem 0;
    }

    .dash-title {
        min-width: 230px;
        font-size: clamp(1.75rem, 2.5vw, 2.5rem);
        line-height: 1.05;
        font-weight: 800;
        letter-spacing: 0;
        margin: 0;
    }

    .dash-rule {
        width: 3px;
        align-self: stretch;
        min-height: 70px;
        background: rgba(248, 251, 244, .86);
    }

    .dash-copy {
        color: var(--ink);
        max-width: 460px;
        font-weight: 700;
        line-height: 1.55;
    }

    .dash-tag {
        margin-left: auto;
        font-size: clamp(2rem, 3vw, 3rem);
        line-height: 1;
        font-weight: 900;
        text-align: right;
        white-space: nowrap;
    }

    .match-strip {
        background: var(--cream);
        color: var(--navy);
        padding: 10px 16px;
        font-weight: 800;
        text-align: center;
        border-radius: 7px;
        margin: .5rem 0 .45rem 0;
        border: 1px solid rgba(255, 255, 255, .6);
    }

    .match-strip {
        text-align: left;
        margin-bottom: .7rem;
    }

    [data-testid="stMarkdownContainer"] h4,
    [data-testid="stMarkdownContainer"] h4 a,
    [data-testid="stMarkdownContainer"] h4 span {
        background: transparent !important;
        color: #000000 !important;
        padding: 0;
        font-weight: 800;
        text-align: center;
        border-radius: 0;
        margin: .5rem 0 .45rem 0;
        border: 0;
    }

    h1, h2, h3, h5, h6 {
        color: var(--forest);
        letter-spacing: 0;
    }

    div[data-testid="stVerticalBlock"] > div[data-testid="stVerticalBlockBorderWrapper"] {
        background: var(--panel);
    }

    div[data-testid="stMetric"] {
        background: linear-gradient(180deg, var(--panel-soft), var(--forest));
        border: 1px solid rgba(118, 180, 166, .75);
        border-radius: 6px;
        padding: 14px 16px;
        min-height: 98px;
    }

    div[data-testid="stMetric"] label,
    div[data-testid="stMetricValue"] {
        color: var(--ink);
    }

    .stTabs [data-baseweb="tab-list"] {
        gap: 6px;
        border-bottom: 0;
        background: transparent;
    }

    .stTabs [data-baseweb="tab"] {
        color: var(--navy);
        background: var(--cream);
        border-radius: 7px 7px 0 0;
        padding: 10px 18px;
        font-weight: 800;
    }

    .stTabs [aria-selected="true"] {
        color: var(--ink);
        background: var(--forest);
    }

    [data-testid="stDataFrame"] {
        border: 1px solid rgba(16, 42, 34, .18);
        background: transparent;
        border-radius: 4px;
    }

    [data-testid="stDataFrame"] [role="columnheader"],
    [data-testid="stDataFrame"] [data-testid="stDataFrameColumnHeader"],
    [data-testid="stDataFrame"] th,
    [data-testid="stDataFrame"] thead,
    [data-testid="stDataFrame"] thead tr,
    [data-testid="stDataFrame"] thead th {
        color: var(--forest) !important;
    }

    .stButton > button,
    .stDownloadButton > button {
        background: var(--cream);
        color: var(--navy);
        border: 1px solid var(--grid);
        border-radius: 7px;
        font-weight: 800;
    }

    .stButton > button:hover,
    .stDownloadButton > button:hover {
        background: var(--peach);
        color: var(--navy);
        border-color: var(--peach);
    }

    div[data-testid="stAlert"] {
        background: var(--panel-soft);
        color: var(--ink);
        border-left-color: var(--peach);
    }

    div[data-testid="stSelectbox"] div,
    div[data-testid="stMultiSelect"] div,
    div[data-testid="stSlider"] div {
        color: #101b2f;
    }

    [data-testid="stSidebar"] div[data-baseweb="select"] > div {
        background: var(--cream);
        color: var(--navy);
        border-radius: 7px;
    }

    @media (max-width: 900px) {
        .dash-hero {
            align-items: flex-start;
            flex-wrap: wrap;
        }

        .dash-rule {
            display: none;
        }

        .dash-tag {
            margin-left: 0;
            width: 100%;
            text-align: left;
            font-size: 2rem;
        }
    }
</style>
"""

st.markdown(BRAND_CSS, unsafe_allow_html=True)

CHART_COLORS = ["#ffbd78", "#d99a63", "#fff0a8", "#4f9b92"]
CHART_LAYOUT = dict(
    paper_bgcolor="#173b35",
    plot_bgcolor="#173b35",
    font=dict(color="#f6f7f2"),
    title=dict(font=dict(color="#ffffff")),
    legend=dict(font=dict(color="#ffffff"), title=dict(font=dict(color="#ffffff"))),
    xaxis=dict(
        color="#ffffff",
        title_font=dict(color="#ffffff"),
        tickfont=dict(color="#ffffff"),
        gridcolor="rgba(118, 180, 166, .35)",
        zerolinecolor="rgba(248, 251, 244, .35)",
    ),
    yaxis=dict(
        color="#ffffff",
        title_font=dict(color="#ffffff"),
        tickfont=dict(color="#ffffff"),
        gridcolor="rgba(118, 180, 166, .35)",
        zerolinecolor="rgba(248, 251, 244, .35)",
    ),
)

@st.cache_data(show_spinner="Loading match data...")
def get_data() -> pd.DataFrame:
    raw = load_raw_data(RAW_EVENTS_FILE)
    return clean_events(raw)


df = get_data()

logo_path = ASSETS_DIR / "logo.png"
if logo_path.exists():
    st.sidebar.image(str(logo_path), use_container_width=True)

st.sidebar.title("Filters")

matches = list_matches(df)
match_labels = {
    row.match_id: f"{row.match_id}: {row.home_team} vs {row.away_team}"
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

st.markdown(
    """
    <div class="dash-hero">
        <div class="dash-title">Momentum<br>Tracker</div>
        <div class="dash-rule"></div>
        <div class="dash-copy">Track team pressure, attacking swings, player output, and match reports across the league.</div>
        <div class="dash-tag">Tactical Analysis</div>
    </div>
    """,
    unsafe_allow_html=True,
)
st.markdown(f"<div class='match-strip'>{match_labels[match_id]}</div>", unsafe_allow_html=True)

momentum = compute_momentum_index(df, match_id=match_id)

fig = go.Figure()
fig.add_trace(
    go.Scatter(
        x=momentum["minute"], y=momentum["momentum_diff"],
        fill="tozeroy", mode="lines", name="Momentum",
        line=dict(color="#ffbd78", width=4),
        fillcolor="rgba(255, 240, 168, 0.45)",
    )
)
fig.add_hline(y=0, line_color="#f8fbf4", opacity=0.45)
fig.update_layout(
    template="plotly_dark", height=380,
    xaxis_title="Minute", yaxis_title=f"{teams[0]} <— momentum —> {teams[1]}" if len(teams) == 2 else "Momentum",
    margin=dict(t=20, b=20),
    **CHART_LAYOUT,
)
st.plotly_chart(fig, use_container_width=True)

if len(teams) == 2:
    summary = momentum_summary(momentum, teams[0], teams[1])
    c1, c2, c3, c4 = st.columns(4)
    c1.metric(f"{teams[0]} minutes led", summary[f"{teams[0]}_minutes_led"])
    c2.metric(f"{teams[1]} minutes led", summary[f"{teams[1]}_minutes_led"])
    c3.metric("Lead changes", summary["lead_changes"])
    c4.metric("Even minutes", summary["even_minutes"])

st.markdown(
    """
    <style>
    button[data-baseweb="tab"] p {
        font-size: 20px !important; 
        font-weight: bold !important; 
    }
    </style>

    """,
    unsafe_allow_html=True

)

tab1, tab2, tab3, tab4, tab5 = st.tabs(
    ["Team Stats", "Players", "Heatmaps & Shots", "Correlations", "Downloads"]
)

with tab1:
    stats = team_match_stats(df)
    ratings = team_ratings(stats)
    perf = performance_summary(stats)

    left, right = st.columns([2, 1])
    with left:
        st.markdown("#### Match stats")
        st.dataframe(rename_columns_for_display(stats[stats["match_id"] == match_id]), use_container_width=True)
    with right:
        st.markdown("#### Team rating (this match)")
        st.dataframe(rename_columns_for_display(ratings[ratings["match_id"] == match_id]), use_container_width=True)

    st.markdown("#### Season performance summary")
    st.dataframe(rename_columns_for_display(perf), use_container_width=True)

    fig2 = px.bar(perf, x="team", y="xg_per_match", color="team", template="plotly_dark",
                  color_discrete_sequence=CHART_COLORS,
                  title="xG per match by team")
    fig2.update_layout(**CHART_LAYOUT)
    st.plotly_chart(fig2, use_container_width=True)

with tab2:
    p_stats = player_match_stats(df)
    p_ratings = player_rating(df)
    top = top_performers(p_stats, p_ratings, n=10)

    st.markdown("#### Top performers (all matches)")
    st.dataframe(rename_columns_for_display(top), use_container_width=True)

    st.markdown("#### Compare two players")
    all_players = sorted(p_stats["player"].unique())
    colA, colB = st.columns(2)
    player_a = colA.selectbox("Player A", all_players, index=0)
    player_b = colB.selectbox("Player B", all_players, index=min(1, len(all_players) - 1))
    comparison = compare_players(p_stats, player_a, player_b)
    st.dataframe(rename_columns_for_display(comparison), use_container_width=True)

with tab3:
    st.markdown("#### Filtered events on the pitch")
    fig3 = px.scatter(
        filtered, x="x", y="y", color="team", size="xg",
        hover_data=["player", "event_type", "minute"],
        template="plotly_dark", range_x=[0, 120], range_y=[0, 80],
        color_discrete_sequence=CHART_COLORS,
        title="Event locations",
    )
    fig3.update_yaxes(autorange="reversed")
    fig3.update_layout(**CHART_LAYOUT)
    st.plotly_chart(fig3, use_container_width=True)

    xt_df = add_xt_column(df)
    xt_summary = team_xt_summary(xt_df)
    st.markdown("#### Expected Threat (xT), this match")
    st.dataframe(rename_columns_for_display(xt_summary[xt_summary["match_id"] == match_id]), use_container_width=True)

with tab4:
    stats = team_match_stats(df)
    corr = correlation_matrix(stats)
    fig4 = px.imshow(corr, text_auto=".2f", color_continuous_scale=["#0e2a2b", "#4f9b92", "#fff0a8", "#ffbd78"], template="plotly_dark",
                      title="Stat correlation matrix")
    fig4.update_layout(**CHART_LAYOUT)
    st.plotly_chart(fig4, use_container_width=True)

with tab5:
    st.markdown("#### Export current filtered event data")
    csv_bytes = filtered.to_csv(index=False).encode("utf-8")
    st.download_button("Download filtered events (CSV)", csv_bytes, "filtered_events.csv", "text/csv")

    full_csv = df.to_csv(index=False).encode("utf-8")
    st.download_button("Download all cleaned events (CSV)", full_csv, "events_clean.csv", "text/csv")
    
    pdf_path = REPORTS_DIR / "report.pdf"
    if pdf_path.exists():
        st.download_button(
            "Download full PDF report",
            pdf_path.read_bytes(),
            "report.pdf",
            "application/pdf"
        )
    else:
        st.info(
            "Run `python src/main.py` to generate the full PDF report, then return here to download it."
    )
