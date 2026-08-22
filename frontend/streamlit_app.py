"""Entry point da aplicação Streamlit."""

from __future__ import annotations

from pathlib import Path

import streamlit as st

ROOT_DIR = Path(__file__).resolve().parents[1]
PAGES_DIR = ROOT_DIR / "frontend" / "pages"
LOGO_PATH = ROOT_DIR / "assets" / "brand" / "vertere-ai-logo.png"


def _apply_app_styles() -> None:
    st.markdown(
        """
        <style>
        :root {
            --vertere-background: transparent;
            --vertere-surface: transparent;
            --vertere-muted: color-mix(in srgb, currentColor 6%, transparent);
            --vertere-ink: currentColor;
            --vertere-slate: color-mix(in srgb, currentColor 70%, transparent);
            --vertere-primary: #C44DFF;
            --vertere-primary-end: #8C1AFF;
            --vertere-border: color-mix(in srgb, currentColor 16%, transparent);
            --vertere-primary-soft: rgba(196, 77, 255, 0.10);
        }
        [data-testid="stAppViewContainer"] {
            background: var(--vertere-background);
            color: inherit;
        }
        [data-testid="stHeader"] {
            background: transparent;
        }
        .block-container {
            max-width: 1600px;
            padding-top: 1.5rem;
            padding-bottom: 2rem;
        }
        [data-testid="stSidebar"] {
            background: var(--vertere-muted);
            border-right: 1px solid var(--vertere-border);
        }
        [data-testid="stSidebar"] section {
            padding: 1rem;
        }
        [data-testid="stMetric"] {
            min-height: 6.5rem;
        }
        [data-testid="stMetricLabel"] p {
            color: var(--vertere-slate);
            font-weight: 600;
        }
        [data-testid="stMetricValue"] {
            color: var(--vertere-ink);
            font-variant-numeric: tabular-nums;
        }
        button[kind="primary"] {
            background: linear-gradient(135deg, #FF4DFF, #8C1AFF);
            border: 0;
        }
        [data-testid="stDataFrame"] {
            border: 1px solid var(--vertere-border);
            border-radius: 12px;
        }
        div[data-testid="stVerticalBlockBorderWrapper"] {
            background: var(--vertere-surface);
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def main() -> None:
    st.set_page_config(
        page_title="Vertere Obras Públicas",
        page_icon=str(LOGO_PATH),
        layout="wide",
        initial_sidebar_state="expanded",
    )
    if hasattr(st, "logo") and LOGO_PATH.exists():
        st.logo(str(LOGO_PATH), size="medium")
    _apply_app_styles()

    pages = [
        st.Page(
            str(PAGES_DIR / "overview.py"),
            title="Visão geral",
            icon=":material/dashboard:",
            default=True,
        ),
        st.Page(
            str(PAGES_DIR / "project_detail.py"),
            title="Detalhe do projeto",
            icon=":material/search:",
        ),
    ]
    navigation = st.navigation(pages, position="top")
    navigation.run()


main()
