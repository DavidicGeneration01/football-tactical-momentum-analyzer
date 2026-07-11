# CLI pipeline. Run with: python src/main.py

from __future__ import annotations

import sys
from pathlib import Path
from typing import Callable

_SRC = Path(__file__).resolve().parent
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from logger import get_logger
from utils import timer

log = get_logger(__name__)


def _build_wsgi_app() -> Callable[[dict, Callable[[str, list[tuple[str, str]]], None]], list[bytes]]:
    def app(environ, start_response):
        status = "200 OK"
        headers = [("Content-Type", "text/plain; charset=utf-8")]
        body = (
            "Football Tactical Momentum Analyzer is ready. "
            "Use the CLI entrypoint to run the full pipeline."
        ).encode("utf-8")
        start_response(status, headers)
        return [body]

    return app


app = _build_wsgi_app()
application = app


@timer
def run_pipeline() -> None:
    from analysis import (
        add_xt_column,
        correlation_matrix,
        match_ratings,
        performance_summary,
        team_match_stats,
        team_ratings,
        team_xt_summary,
    )
    from cleaner import clean_events, save_processed
    from config import RAW_EVENTS_FILE, ensure_directories
    from data_loader import load_raw_data
    from momentum import compute_momentum_index, momentum_summary
    from player_analysis import player_match_stats, player_rating, top_performers
    from report_generator import generate_all_reports
    from utils import list_matches
    from visualization import generate_all_charts

    ensure_directories()

    log.info("=== Load and clean ===")
    raw = load_raw_data(RAW_EVENTS_FILE)
    df = clean_events(raw)
    save_processed(df)

    log.info("=== Analytics ===")
    stats = team_match_stats(df)
    ratings = team_ratings(stats)
    m_ratings = match_ratings(stats)
    perf = performance_summary(stats)
    corr = correlation_matrix(stats)

    xt_df = add_xt_column(df)
    xt_summary = team_xt_summary(xt_df)

    p_stats = player_match_stats(df)
    p_ratings = player_rating(df)
    top_players = top_performers(p_stats, p_ratings, n=15)

    matches = list_matches(df)
    first_match_id = int(matches.iloc[0]["match_id"])
    momentum_df = compute_momentum_index(df, match_id=first_match_id)
    teams_in_match = sorted(df[df["match_id"] == first_match_id]["team"].unique())
    if len(teams_in_match) == 2:
        m_summary = momentum_summary(momentum_df, teams_in_match[0], teams_in_match[1])
        log.info("Momentum summary for match %s: %s", first_match_id, m_summary)

    log.info("=== Dashboard note ===")
    log.info("Run `streamlit run src/dashboard.py` for the interactive dashboard.")

    log.info("=== Charts and reports ===")
    chart_paths = generate_all_charts(
        df, momentum_df, teams_in_match, perf, corr, top_players,
    )

    report_tables = {
        "team_match_stats": stats,
        "team_ratings": ratings,
        "match_ratings": m_ratings,
        "performance_summary": perf,
        "player_top_performers": top_players,
        "team_expected_threat": xt_summary,
        "correlation_matrix": corr.reset_index().rename(columns={"index": "stat"}),
    }
    outputs = generate_all_reports(report_tables, chart_paths)

    log.info("Pipeline complete. Reports available at: %s", {k: str(v) for k, v in outputs.items()})


if __name__ == "__main__":
    run_pipeline()
