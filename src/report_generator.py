"""Report exports: CSV, Excel, HTML, and PDF."""

from __future__ import annotations

import datetime as dt
from pathlib import Path

import pandas as pd
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (
    Image,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from config import DATA_REPORTS_DIR, REPORTS_DIR
from logger import get_logger

log = get_logger(__name__)

def export_csvs(tables: dict[str, pd.DataFrame], out_dir: Path = DATA_REPORTS_DIR) -> list[Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    paths = []
    for name, table in tables.items():
        path = out_dir / f"{name}.csv"
        table.to_csv(path, index=False)
        paths.append(path)
        log.info("Exported CSV: %s", path)
    return paths

def export_excel(tables: dict[str, pd.DataFrame], filename: str = "analysis.xlsx") -> Path:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    path = REPORTS_DIR / filename
    with pd.ExcelWriter(path, engine="openpyxl") as writer:
        for sheet_name, table in tables.items():
            safe_name = sheet_name[:31]  # Excel gets picky here
            # Rename columns to nice display format
            display_table = table.rename(columns=COLUMN_NAME_MAPPING)
            display_table.to_excel(writer, sheet_name=safe_name, index=False)

            worksheet = writer.sheets[safe_name]
            for i, col in enumerate(display_table.columns, start=1):
                max_len = max(
                    display_table[col].astype(str).map(len).max() if len(display_table) else 0, len(str(col))
                )
                worksheet.column_dimensions[worksheet.cell(row=1, column=i).column_letter].width = min(
                    max_len + 3, 40
                )
    log.info("Exported Excel workbook: %s", path)
    return path

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>{title}</title>
<style>
  body {{ font-family: -apple-system, Segoe UI, Roboto, sans-serif; background:#0b1220; color:#e6edf3; margin:0; padding:2rem; }}
  h1 {{ color:#3ddc84; }}
  h2 {{ color:#9ecbff; border-bottom:1px solid #223; padding-bottom:.3rem; margin-top:2.5rem; }}
  table {{ border-collapse: collapse; width:100%; margin:1rem 0; }}
  th, td {{ border:1px solid #223; padding:.5rem .7rem; text-align:left; font-size:.9rem; }}
  th {{ background:#132038; }}
  tr:nth-child(even) {{ background:#101a2e; }}
  .meta {{ color:#8899aa; font-size:.85rem; }}
  .card {{ background:#101a2e; border:1px solid #223; border-radius:10px; padding:1rem 1.3rem; margin:1rem 0; }}
</style>
</head>
<body>
<h1>{title}</h1>
<p class="meta">Built {timestamp}</p>
{body}
</body>
</html>
"""


def _df_to_html_table(df: pd.DataFrame) -> str:
    return df.to_html(index=False, border=0, classes="", justify="left")


def export_html_report(tables: dict[str, pd.DataFrame], filename: str = "report.html") -> Path:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    sections = []
    for name, table in tables.items():
        title = name.replace("_", " ").title()
        sections.append(f"<h2>{title}</h2>\n<div class='card'>{_df_to_html_table(table)}</div>")

    html = HTML_TEMPLATE.format(
        title="Football Tactical Momentum Analyzer — Report",
        timestamp=dt.datetime.now().strftime("%Y-%m-%d %H:%M"),
        body="\n".join(sections),
    )
    path = REPORTS_DIR / filename
    path.write_text(html, encoding="utf-8")
    log.info("Exported HTML report: %s", path)
    return path

def _df_to_pdf_table(df: pd.DataFrame, max_rows: int = 15) -> Table:
    preview = df.head(max_rows)
    data = [list(preview.columns)] + preview.astype(str).values.tolist()
    table = Table(data, repeatRows=1)
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#132038")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTSIZE", (0, 0), (-1, -1), 7),
                ("GRID", (0, 0), (-1, -1), 0.4, colors.grey),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.whitesmoke, colors.HexColor("#eef2f7")]),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ]
        )
    )
    return table


def export_pdf_report(
    tables: dict[str, pd.DataFrame],
    chart_paths: list[Path] | None = None,
    filename: str = "report.pdf",
) -> Path:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    path = REPORTS_DIR / filename

    doc = SimpleDocTemplate(str(path), pagesize=A4, topMargin=1.5 * cm, bottomMargin=1.5 * cm)
    styles = getSampleStyleSheet()
    story = [
        Paragraph("Football Tactical Momentum Analyzer", styles["Title"]),
        Paragraph(f"Built {dt.datetime.now().strftime('%Y-%m-%d %H:%M')}", styles["Normal"]),
        Spacer(1, 0.8 * cm),
    ]

    for chart in chart_paths or []:
        try:
            story.append(Paragraph(chart.stem.replace("_", " ").title(), styles["Heading2"]))
            story.append(Image(str(chart), width=16 * cm, height=9 * cm, kind="proportional"))
            story.append(Spacer(1, 0.6 * cm))
        except Exception as exc:  # pragma: no cover
            log.warning("Could not embed chart %s: %s", chart, exc)

    for name, table in tables.items():
        story.append(Paragraph(name.replace("_", " ").title(), styles["Heading2"]))
        story.append(_df_to_pdf_table(table))
        story.append(Spacer(1, 0.8 * cm))

    doc.build(story)
    log.info("Exported PDF report: %s", path)
    return path


def generate_all_reports(
    tables: dict[str, pd.DataFrame], chart_paths: list[Path] | None = None
) -> dict[str, Path]:
    outputs = {
        "excel": export_excel(tables),
        "html": export_html_report(tables),
        "pdf": export_pdf_report(tables, chart_paths),
    }
    export_csvs(tables)
    return outputs
