"""Общая UI-обвязка: тема, шапка, футер. Используется всеми страницами."""

from __future__ import annotations

import base64
from functools import lru_cache
from pathlib import Path

import streamlit as st

APP_ROOT = Path(__file__).resolve().parents[1]
LOGO_PATH = APP_ROOT / "assets" / "logo.jpg"

BRAND_TITLE = "ЭПР в БЭК · гибридный метод"
DEPARTMENT = "МФТИ · ФРКТ · кафедра радиофизики и технической кибернетики"
THESIS_LINE = "Магистерская выпускная квалификационная работа · 2026"
REPO_URL = "https://github.com/FizickFromMipt/master-s-thesis"


@lru_cache(maxsize=1)
def _logo_b64() -> str:
    return base64.b64encode(LOGO_PATH.read_bytes()).decode("ascii")


def init_page(page_title: str) -> None:
    """Вызывать в самом верху каждого скрипта страницы."""
    st.set_page_config(
        page_title=f"{page_title} · ЭПР в БЭК",
        page_icon=str(LOGO_PATH),
        layout="wide",
        initial_sidebar_state="expanded",
    )
    _inject_css()
    _render_header()
    _render_sidebar_brand()


def render_footer() -> None:
    """Вызывать в самом конце каждого скрипта страницы."""
    st.markdown(
        f"""
        <div class="app-footer">
            <span>Designed by <strong>Alex Pevnenko</strong> © 2026</span>
            <span class="app-footer__sep">·</span>
            <a href="{REPO_URL}" target="_blank" rel="noopener">GitHub</a>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _inject_css() -> None:
    st.markdown(
        """
        <style>
        /* убрать стандартный хром Streamlit */
        #MainMenu {visibility: hidden;}
        header[data-testid="stHeader"] {visibility: hidden; height: 0;}
        footer {visibility: hidden;}

        /* основной контейнер */
        .block-container {
            padding-top: 1.25rem;
            padding-bottom: 5rem;
            max-width: 1280px;
        }

        /* шапка */
        .app-header {
            display: flex;
            align-items: center;
            gap: 1rem;
            padding: 0.5rem 0 1rem;
            border-bottom: 1px solid #E4E6EE;
            margin-bottom: 1.5rem;
        }
        .app-header__logo {
            height: 56px;
            width: 56px;
            object-fit: contain;
            flex-shrink: 0;
        }
        .app-header__text { display: flex; flex-direction: column; gap: 2px; }
        .app-header__title {
            font-size: 1.05rem;
            font-weight: 600;
            color: #2D2E83;
            margin: 0; line-height: 1.25;
        }
        .app-header__subtitle {
            font-size: 0.82rem;
            color: #6B6E80;
            margin: 0; line-height: 1.3;
        }

        /* типографика */
        h1 { font-weight: 700; letter-spacing: -0.015em; color: #15172B; }
        h2, h3 { color: #1F2140; }

        /* sidebar */
        section[data-testid="stSidebar"] {
            background: #F4F5FA;
            border-right: 1px solid #E4E6EE;
        }
        section[data-testid="stSidebar"] .sidebar-brand {
            display: flex; flex-direction: column; align-items: center;
            gap: 0.5rem; padding: 0.5rem 0 1rem;
            border-bottom: 1px solid #E4E6EE; margin-bottom: 1rem;
        }
        section[data-testid="stSidebar"] .sidebar-brand img {
            height: 64px; width: 64px; object-fit: contain;
        }
        section[data-testid="stSidebar"] .sidebar-brand .name {
            font-size: 0.85rem; font-weight: 600; color: #2D2E83;
            text-align: center; line-height: 1.25;
        }

        /* кнопки */
        .stButton > button {
            border-radius: 8px;
            font-weight: 500;
        }

        /* метрики */
        [data-testid="stMetric"] {
            background: #F7F8FC;
            border: 1px solid #E4E6EE;
            border-radius: 10px;
            padding: 12px 16px;
        }

        /* sticky footer */
        .app-footer {
            position: fixed;
            left: 0; right: 0; bottom: 0;
            padding: 0.7rem 1.5rem;
            background: rgba(255, 255, 255, 0.92);
            backdrop-filter: blur(8px);
            -webkit-backdrop-filter: blur(8px);
            border-top: 1px solid #E4E6EE;
            font-size: 0.8rem;
            color: #6B6E80;
            text-align: center;
            z-index: 1000;
        }
        .app-footer a {
            color: #2D2E83;
            text-decoration: none;
        }
        .app-footer a:hover { text-decoration: underline; }
        .app-footer__sep { margin: 0 0.5rem; opacity: 0.5; }
        </style>
        """,
        unsafe_allow_html=True,
    )


def _render_header() -> None:
    st.markdown(
        f"""
        <div class="app-header">
            <img class="app-header__logo"
                 src="data:image/jpeg;base64,{_logo_b64()}"
                 alt="Кафедра РФиТК">
            <div class="app-header__text">
                <p class="app-header__title">{DEPARTMENT}</p>
                <p class="app-header__subtitle">{THESIS_LINE}</p>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _render_sidebar_brand() -> None:
    with st.sidebar:
        st.markdown(
            f"""
            <div class="sidebar-brand">
                <img src="data:image/jpeg;base64,{_logo_b64()}" alt="logo">
                <div class="name">Кафедра РФиТК<br>МФТИ · ФРКТ</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
