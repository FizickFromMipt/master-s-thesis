"""Общая UI-обвязка: тема, шапка с верхней навигацией, футер."""

from __future__ import annotations

import base64
from functools import lru_cache
from pathlib import Path

import streamlit as st

APP_ROOT = Path(__file__).resolve().parents[1]
LOGO_PATH = APP_ROOT / "assets" / "logo.jpg"

REPO_URL = "https://github.com/FizickFromMipt/master-s-thesis"

_NAV = [
    ("Главная", "app.py"),
    ("Анализ", "pages/1_Анализ.py"),
    ("О работе", "pages/2_О_работе.py"),
]


@lru_cache(maxsize=1)
def _logo_b64() -> str:
    return base64.b64encode(LOGO_PATH.read_bytes()).decode("ascii")


def init_page(page_title: str, *, sidebar: str = "collapsed") -> None:
    """В самом верху каждой страницы. По умолчанию сайдбар свёрнут."""
    st.set_page_config(
        page_title=f"{page_title} · ЭПР в БЭК",
        page_icon=str(LOGO_PATH),
        layout="wide",
        initial_sidebar_state=sidebar,
    )
    _inject_css()
    _render_top_nav()


def render_footer() -> None:
    """В самом низу каждой страницы."""
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
        /* ── скрыть стандартный хром Streamlit ───────────────────── */
        #MainMenu {visibility: hidden;}
        header[data-testid="stHeader"] {visibility: hidden; height: 0;}
        footer {visibility: hidden;}
        /* убрать автонавигацию по pages/ из сайдбара (все варианты) */
        [data-testid="stSidebarNav"],
        [data-testid="stSidebarNavItems"],
        [data-testid="stSidebarNavLink"],
        [data-testid="stSidebarNavLinkContainer"],
        [data-testid="stSidebarNavSeparator"],
        section[data-testid="stSidebar"] nav,
        section[data-testid="stSidebar"] ul[data-testid*="Nav"] {
            display: none !important;
            height: 0 !important;
            visibility: hidden !important;
        }
        /* в шапке сайдбара тоже бывает кнопка-список страниц */
        section[data-testid="stSidebar"] [data-testid="stSidebarHeader"] > div:not(:last-child) {
            display: none !important;
        }
        /* зафиксировать сайдбар: спрятать кнопку сворачивания/раскрытия */
        [data-testid="stSidebarCollapseButton"],
        [data-testid="stSidebarCollapsedControl"],
        [data-testid="collapsedControl"],
        button[kind="headerNoPadding"],
        section[data-testid="stSidebar"] button[data-testid*="collaps" i],
        section[data-testid="stSidebar"] button[aria-label*="sidebar" i] {
            display: none !important;
        }

        /* ── фон: радиолокационные пульсации + soft-aurora ───────── */
        [data-testid="stAppViewContainer"] {
            background-color: #F8F9FC;
            background-image:
                radial-gradient(ellipse 1200px 900px at 0% 0%,
                    rgba(45, 46, 131, 0.06) 0%, transparent 55%),
                radial-gradient(ellipse 1100px 850px at 100% 100%,
                    rgba(85, 87, 217, 0.05) 0%, transparent 55%),
                url("data:image/svg+xml;charset=utf-8,%3Csvg xmlns='http://www.w3.org/2000/svg' width='240' height='240' viewBox='0 0 240 240'%3E%3Cg fill='none' stroke='%232D2E83' stroke-width='0.5' opacity='0.05'%3E%3Ccircle cx='0' cy='0' r='40'/%3E%3Ccircle cx='0' cy='0' r='80'/%3E%3Ccircle cx='0' cy='0' r='120'/%3E%3Ccircle cx='0' cy='0' r='160'/%3E%3Ccircle cx='0' cy='0' r='200'/%3E%3Ccircle cx='240' cy='240' r='40'/%3E%3Ccircle cx='240' cy='240' r='80'/%3E%3Ccircle cx='240' cy='240' r='120'/%3E%3Ccircle cx='240' cy='240' r='160'/%3E%3C/g%3E%3C/svg%3E");
            background-repeat: no-repeat, no-repeat, repeat;
            background-position: 0 0, 100% 100%, 0 0;
        }
        /* main и pages не должны перекрывать фон */
        [data-testid="stMain"],
        section[data-testid="stMain"] > div {
            background: transparent !important;
        }

        /* ── глобальное ──────────────────────────────────────────── */
        html, body, [class*="css"] {
            font-family: -apple-system, BlinkMacSystemFont, "Inter",
                         "Segoe UI", Roboto, "Helvetica Neue", sans-serif;
        }
        .block-container {
            padding-top: 1.25rem;
            padding-bottom: 6rem;
            max-width: 1280px;
        }
        h1 { font-weight: 700; letter-spacing: -0.015em; color: #15172B; }
        h2, h3 { color: #1F2140; font-weight: 600; }

        /* ── верхняя навигация ───────────────────────────────────── */
        .top-nav__brand {
            display: flex;
            align-items: center;
            gap: 0.85rem;
        }
        .top-nav__logo {
            height: 44px;
            width: 44px;
            object-fit: contain;
            flex-shrink: 0;
        }
        .top-nav__title {
            font-size: 1rem;
            font-weight: 700;
            color: #2D2E83;
            line-height: 1.2;
            margin: 0;
        }
        .top-nav__subtitle {
            font-size: 0.75rem;
            color: #8A8E9F;
            font-weight: 400;
            margin: 0;
        }
        .top-nav-divider {
            height: 1px;
            background: linear-gradient(
                to right, transparent, #E4E6EE 15%, #E4E6EE 85%, transparent
            );
            margin: 0.5rem 0 2rem;
        }

        /* ссылки навигации — стиль "tab" */
        [data-testid="stPageLink"] {
            text-align: center;
        }
        [data-testid="stPageLink"] a {
            padding: 8px 14px !important;
            border-radius: 8px !important;
            font-weight: 500 !important;
            color: #4A4E70 !important;
            transition: background 0.15s, color 0.15s !important;
        }
        [data-testid="stPageLink"] a:hover {
            background: #E8E9F4 !important;
            color: #2D2E83 !important;
        }

        /* ── hero (главная) ──────────────────────────────────────── */
        .hero { padding: 1.5rem 0 0.5rem; }
        .hero__eyebrow {
            display: inline-block;
            font-size: 0.75rem;
            font-weight: 600;
            color: #2D2E83;
            background: #E8E9F4;
            padding: 5px 12px;
            border-radius: 999px;
            text-transform: uppercase;
            letter-spacing: 0.06em;
            margin-bottom: 1rem;
        }
        .hero__title {
            font-size: 2.6rem;
            font-weight: 800;
            letter-spacing: -0.02em;
            color: #15172B;
            line-height: 1.12;
            margin: 0 0 1.1rem;
            max-width: 820px;
        }
        .hero__title em {
            font-style: normal;
            background: linear-gradient(135deg, #2D2E83 0%, #5557D9 100%);
            -webkit-background-clip: text;
            background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        .hero__lead {
            font-size: 1.1rem;
            color: #4A4E70;
            line-height: 1.55;
            max-width: 720px;
            margin: 0 0 1.5rem;
        }

        /* ── карточки (st.container border=True) ─────────────────── */
        [data-testid="stVerticalBlockBorderWrapper"] {
            background: #FFFFFF;
            box-shadow:
                0 1px 2px rgba(20, 22, 50, 0.04),
                0 2px 12px rgba(20, 22, 50, 0.04);
            border-radius: 14px !important;
            border: 1px solid #ECEEF5 !important;
            transition: box-shadow 0.2s, transform 0.2s;
        }
        [data-testid="stVerticalBlockBorderWrapper"]:hover {
            box-shadow:
                0 1px 2px rgba(20, 22, 50, 0.05),
                0 4px 20px rgba(20, 22, 50, 0.07);
        }

        /* ── кнопки ──────────────────────────────────────────────── */
        .stButton > button {
            border-radius: 8px;
            font-weight: 500;
            transition: all 0.15s;
        }
        .stButton > button[kind="primary"] {
            box-shadow: 0 1px 3px rgba(45, 46, 131, 0.25);
        }
        .stButton > button[kind="primary"]:hover {
            box-shadow: 0 2px 8px rgba(45, 46, 131, 0.35);
            transform: translateY(-1px);
        }

        /* ── метрики ─────────────────────────────────────────────── */
        [data-testid="stMetric"] {
            background: linear-gradient(135deg, #F7F8FC 0%, #EFF1FA 100%);
            border: 1px solid #E4E6EE;
            border-radius: 12px;
            padding: 16px 20px;
        }
        [data-testid="stMetricValue"] {
            color: #2D2E83 !important;
            font-weight: 700 !important;
        }

        /* ── input-ы ─────────────────────────────────────────────── */
        [data-baseweb="input"], [data-baseweb="select"] {
            border-radius: 8px !important;
        }

        /* ── sidebar (для страницы Анализ) ───────────────────────── */
        section[data-testid="stSidebar"] {
            background: #F7F8FB;
            border-right: 1px solid #E4E6EE;
        }
        section[data-testid="stSidebar"] h2,
        section[data-testid="stSidebar"] h3 {
            font-size: 0.95rem !important;
            color: #2D2E83 !important;
            margin-top: 0.5rem !important;
        }

        /* ── sticky-футер ────────────────────────────────────────── */
        .app-footer {
            position: fixed;
            left: 0; right: 0; bottom: 0;
            padding: 0.7rem 1.5rem;
            background: rgba(255, 255, 255, 0.92);
            backdrop-filter: blur(10px);
            -webkit-backdrop-filter: blur(10px);
            border-top: 1px solid #E4E6EE;
            font-size: 0.8rem;
            color: #6B6E80;
            text-align: center;
            z-index: 1000;
        }
        .app-footer a {
            color: #2D2E83;
            text-decoration: none;
            font-weight: 500;
        }
        .app-footer a:hover { text-decoration: underline; }
        .app-footer__sep { margin: 0 0.6rem; opacity: 0.5; }
        </style>
        """,
        unsafe_allow_html=True,
    )


def _render_top_nav() -> None:
    cols = st.columns([4, 1, 1, 1], vertical_alignment="center")
    with cols[0]:
        st.markdown(
            f"""
            <div class="top-nav__brand">
                <img class="top-nav__logo"
                     src="data:image/jpeg;base64,{_logo_b64()}"
                     alt="logo">
                <div>
                    <p class="top-nav__title">ЭПР в БЭК · гибридный метод</p>
                    <p class="top-nav__subtitle">МФТИ ФРКТ · кафедра РФиТК · 2026</p>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    for i, (label, path) in enumerate(_NAV):
        with cols[i + 1]:
            st.page_link(path, label=label)

    st.markdown('<div class="top-nav-divider"></div>', unsafe_allow_html=True)
