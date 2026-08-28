"""Entry point da aplicação Streamlit."""

from __future__ import annotations

from pathlib import Path

import streamlit as st

ROOT_DIR = Path(__file__).resolve().parents[1]
PAGES_DIR = ROOT_DIR / "frontend" / "pages"


def _apply_app_styles() -> None:
    st.markdown(
        """
        <style>
        :root {
            --app-background: transparent;
            --app-surface: transparent;
            --app-muted: color-mix(in srgb, currentColor 6%, transparent);
            --app-ink: currentColor;
            --app-slate: color-mix(in srgb, currentColor 70%, transparent);
            --app-primary: #C44DFF;
            --app-primary-start: #FF4DFF;
            --app-primary-end: #8C1AFF;
            --app-border: color-mix(in srgb, currentColor 16%, transparent);
            --app-primary-soft: rgba(196, 77, 255, 0.10);
        }
        [data-testid="stAppViewContainer"] {
            background: var(--app-background);
            color: inherit;
        }
        [data-testid="stHeader"] {
            background: Canvas !important;
            backdrop-filter: none;
        }
        [data-testid="stDecoration"] {
            background: linear-gradient(
                90deg,
                var(--app-primary-start),
                var(--app-primary),
                var(--app-primary-end)
            ) !important;
        }
        .block-container {
            max-width: 1600px;
            padding-top: 4rem;
            padding-bottom: 2rem;
        }
        [data-testid="stSidebar"] {
            background: var(--app-muted);
            border-right: 1px solid var(--app-border);
        }
        [data-testid="stSidebar"] section {
            padding: 1rem;
        }
        [data-testid="stMetric"] {
            min-height: 6.5rem;
        }
        [data-testid="stMetricLabel"] p {
            color: var(--app-slate);
            font-weight: 600;
        }
        [data-testid="stMetricValue"] {
            color: var(--app-ink);
            font-variant-numeric: tabular-nums;
        }
        button[kind="primary"] {
            background: linear-gradient(135deg, #FF4DFF, #8C1AFF);
            border: 0;
        }
        [data-testid="stDataFrame"] {
            border: 1px solid var(--app-border);
            border-radius: 12px;
        }
        div[data-testid="stVerticalBlockBorderWrapper"] {
            background: var(--app-surface);
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def main() -> None:
    st.set_page_config(
        page_title="Obras Públicas",
        layout="wide",
        initial_sidebar_state="auto",
    )
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
        st.Page(
            str(PAGES_DIR / "analytical_chat.py"),
            title="Chat com os dados",
            icon=":material/chat:",
        ),
    ]
    navigation = st.navigation(pages, position="top")
    navigation.run()


main()
