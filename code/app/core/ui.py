"""UI-обвязка: тёмная финтех-тема (стиль Stockline), сплеш-экран, бургер-меню."""

from __future__ import annotations

import base64
import time
from functools import lru_cache
from pathlib import Path

import streamlit as st

APP_ROOT = Path(__file__).resolve().parents[1]
# Предпочитаем logo.png (новый логотип), иначе старый logo.jpg.
_PNG = APP_ROOT / "assets" / "logo.png"
LOGO_PATH = _PNG if _PNG.exists() else APP_ROOT / "assets" / "logo.jpg"

REPO_URL = "https://github.com/FizickFromMipt/master-s-thesis"

_NAV = [
    ("Главная", "app.py", ":material/home:"),
    ("Анализ", "pages/1_Анализ.py", ":material/insights:"),
    ("Загрузка", "pages/3_Загрузка.py", ":material/upload:"),
]


@lru_cache(maxsize=1)
def _logo_uri() -> str:
    mime = "image/png" if LOGO_PATH.suffix.lower() == ".png" else "image/jpeg"
    b64 = base64.b64encode(LOGO_PATH.read_bytes()).decode("ascii")
    return f"data:{mime};base64,{b64}"


def init_page(page_title: str, *, sidebar: str = "collapsed") -> None:
    """Вызывается в самом верху каждой страницы."""
    st.set_page_config(
        page_title=f"{page_title} · ДОР",
        page_icon=str(LOGO_PATH),
        layout="centered",
        initial_sidebar_state=sidebar,
    )
    _inject_css()
    _maybe_splash()
    _render_drawer()


def render_footer() -> None:
    """Лёгкий минималистичный подвал."""
    st.markdown(
        """
        <div class="app-footer">
            Designed by <strong>Alex Pevnenko</strong> © 2026
        </div>
        """,
        unsafe_allow_html=True,
    )


def _maybe_splash() -> None:
    """Сплеш с логотипом — один раз за сессию: держим ~1.2с, затем убираем."""
    if st.session_state.get("_splash_done"):
        return
    ph = st.empty()
    ph.markdown(
        f'<div class="splash"><img class="splash__logo" src="{_logo_uri()}" alt="logo"></div>',
        unsafe_allow_html=True,
    )
    time.sleep(1.2)
    ph.empty()
    st.session_state["_splash_done"] = True


def _render_drawer() -> None:
    """Навигация внутри выдвижной панели (открывается бургер-кнопкой)."""
    with st.sidebar:
        st.markdown(
            f"""
            <div class="drawer-brand">
                <img class="drawer-brand__logo"
                     src="{_logo_uri()}" alt="logo">
                <span class="drawer-brand__title">ДОР · демо</span>
            </div>
            """,
            unsafe_allow_html=True,
        )
        for label, path, icon in _NAV:
            st.page_link(path, label=label, icon=icon)
        st.markdown('<div class="drawer-sep"></div>', unsafe_allow_html=True)


def _inject_css() -> None:
    st.markdown(
        """
        <style>
        /* ── чистим хром, но оставляем бургер (он живёт внутри toolbar) ── */
        #MainMenu, [data-testid="stToolbarActions"], [data-testid="stStatusWidget"],
        [data-testid="stDecoration"], footer { display: none !important; visibility: hidden !important; }
        header[data-testid="stHeader"] { background: transparent !important; }
        [data-testid="stSidebarNav"],
        [data-testid="stSidebarNavItems"],
        section[data-testid="stSidebar"] nav,
        section[data-testid="stSidebar"] ul[data-testid*="Nav"] {
            display: none !important; height: 0 !important;
        }

        /* ── палитра: тёмная финтех (Stockline) ──────────────────── */
        :root {
            --grn:   #34E0A1;   /* мятный акцент */
            --grn-d: #28C78D;   /* hover */
            --grn-soft: rgba(52,224,161,0.12);
            --bg:    #0E1116;
            --card:  #171C26;
            --card2: #1E2531;
            --text:  #F2F5F7;
            --sub:   #8B95A5;
            --border:#252C38;
        }

        [data-testid="stAppViewContainer"] {
            background:
                radial-gradient(900px 600px at 100% -10%, rgba(52,224,161,0.10), transparent 55%),
                var(--bg);
        }
        [data-testid="stMain"], section[data-testid="stMain"] > div { background: transparent !important; }

        html, body, [class*="css"] {
            font-family: -apple-system, BlinkMacSystemFont, "SF Pro Text",
                         "Segoe UI", Roboto, "Helvetica Neue", sans-serif;
        }
        .block-container { padding-top: 3.6rem; padding-bottom: 2.5rem; }
        h1, h2, h3, h4 { color: var(--text) !important; }
        h1 { font-weight: 800; font-size: 1.7rem; letter-spacing: -0.02em; }
        h2 { font-size: 1.2rem; font-weight: 700; }
        h3 { font-size: 1.02rem; font-weight: 600; }
        p, li, label, span, [data-testid="stMarkdownContainer"] { color: var(--text); }
        [data-testid="stCaptionContainer"] p { color: var(--sub) !important; }

        /* ── карточки ────────────────────────────────────────────── */
        [data-testid="stVerticalBlockBorderWrapper"] {
            background: var(--card);
            border: 1px solid var(--border) !important;
            border-radius: 18px !important;
            box-shadow: 0 8px 28px rgba(0,0,0,0.35);
        }

        /* ── кнопки ──────────────────────────────────────────────── */
        .stButton > button {
            border-radius: 12px;
            font-weight: 700;
            padding: 0.62rem 1.1rem;
            border: 1px solid var(--grn);
            background: transparent;
            color: var(--grn);
            transition: all 0.15s ease;
        }
        .stButton > button:hover {
            background: var(--grn-soft);
            border-color: var(--grn);
            color: var(--grn);
        }
        .stButton > button[kind="primary"] {
            background: var(--grn);
            border: none;
            color: #07120D;
            box-shadow: 0 8px 22px rgba(52,224,161,0.28);
        }
        .stButton > button[kind="primary"]:hover {
            background: var(--grn-d);
            color: #07120D;
            box-shadow: 0 10px 28px rgba(52,224,161,0.40);
            transform: translateY(-1px);
        }
        .stButton > button[kind="primary"]:active { transform: translateY(0); }
        [data-testid="stDownloadButton"] > button {
            border-radius: 12px; font-weight: 700;
            background: var(--grn); color: #07120D; border: none;
        }

        /* ── метрики ─────────────────────────────────────────────── */
        [data-testid="stMetric"] {
            background: var(--card);
            border: 1px solid var(--border);
            border-radius: 16px;
            padding: 14px 16px;
        }
        [data-testid="stMetricValue"] { color: var(--grn) !important; font-weight: 800 !important; }
        [data-testid="stMetricLabel"] p { color: var(--sub) !important; }

        /* ── inputs / поля ───────────────────────────────────────── */
        [data-baseweb="input"], [data-baseweb="select"], [data-baseweb="textarea"],
        [data-baseweb="base-input"] {
            border-radius: 12px !important; background: var(--card2) !important;
        }
        [data-baseweb="input"] input, [data-baseweb="textarea"] textarea { color: var(--text) !important; }
        [data-testid="stFileUploaderDropzone"] {
            border-radius: 14px; background: var(--card) !important; border-color: var(--border) !important;
        }
        [data-testid="stForm"] { border-color: var(--border) !important; }
        .stSlider [data-baseweb="slider"] [role="slider"] { background: var(--grn) !important; }

        /* ════════════════ СПЛЕШ-ЭКРАН ════════════════ */
        .splash {
            position: fixed; inset: 0; z-index: 2147483000;
            display: flex; align-items: center; justify-content: center;
            background: var(--bg);
            pointer-events: none;
        }
        .splash__logo {
            width: 132px; height: 132px; object-fit: contain;
            background: #FFFFFF; border-radius: 28px; padding: 18px;
            box-shadow: 0 0 0 1px var(--border), 0 12px 40px rgba(52,224,161,0.30);
            animation: splashIn 1.5s ease;
        }
        @keyframes splashIn {
            0%   { transform: scale(0.86); opacity: 0; }
            22%  { opacity: 1; }
            100% { transform: scale(1); opacity: 1; }
        }

        /* ════════════════ БУРГЕР (раскрытие сайдбара) ════════════════ */
        [data-testid="stExpandSidebarButton"] {
            display: flex !important; visibility: visible !important; opacity: 1 !important;
            align-items: center !important; justify-content: center !important;
            width: 42px !important; height: 42px !important; margin: 0.35rem !important;
            background: var(--card2) !important;
            border: 1px solid var(--border) !important;
            border-radius: 12px !important;
            box-shadow: 0 4px 14px rgba(0,0,0,0.4) !important;
        }
        [data-testid="stExpandSidebarButton"] > * { display: none !important; }
        [data-testid="stExpandSidebarButton"]::after {
            content: "☰"; font-size: 21px; line-height: 1; color: var(--grn);
        }
        [data-testid="stExpandSidebarButton"]:hover { border-color: var(--grn) !important; }
        [data-testid="stSidebarCollapseButton"] { display: flex !important; visibility: visible !important; }

        /* ── выдвижная панель (drawer) ───────────────────────────── */
        section[data-testid="stSidebar"] {
            background: var(--card);
            border-right: 1px solid var(--border);
        }
        .drawer-brand { display: flex; align-items: center; gap: 0.6rem; padding: 0.2rem 0 0.6rem; }
        .drawer-brand__logo {
            height: 34px; width: 34px; object-fit: contain;
            background: #FFFFFF; border-radius: 9px; padding: 3px;
        }
        .drawer-brand__title { font-size: 1rem; font-weight: 800; color: var(--text); }
        .drawer-sep { height: 1px; background: var(--border); margin: 0.6rem 0 0.4rem; }
        section[data-testid="stSidebar"] [data-testid="stPageLink"] a {
            display: block; padding: 9px 12px !important; border-radius: 10px !important;
            font-weight: 600 !important; color: var(--text) !important;
        }
        section[data-testid="stSidebar"] [data-testid="stPageLink"] a:hover {
            background: var(--grn-soft) !important; color: var(--grn) !important;
        }
        section[data-testid="stSidebar"] h2,
        section[data-testid="stSidebar"] h3 { font-size: 0.95rem !important; color: var(--text) !important; }

        /* ── подвал ──────────────────────────────────────────────── */
        .app-footer {
            margin-top: 2.6rem;
            padding: 1rem 0 0.4rem;
            border-top: 1px solid var(--border);
            text-align: center;
            font-size: 0.8rem;
            color: var(--sub);
        }
        .app-footer a { color: var(--grn); text-decoration: none; font-weight: 600; }
        .app-footer a:hover { text-decoration: underline; }
        .app-footer__sep { margin: 0 0.5rem; opacity: 0.5; }

        /* ═══════════════ МОБИЛЬНАЯ АДАПТАЦИЯ (≤768px) ═══════════════ */
        @media (max-width: 768px) {
            html, body { overflow-x: hidden !important; max-width: 100vw !important; }
            [data-testid="stAppViewContainer"], [data-testid="stMain"],
            [data-testid="stMainBlockContainer"] { overflow-x: hidden !important; max-width: 100vw !important; }
            .block-container { padding: 3.4rem 0.8rem 2.5rem !important; }

            [data-testid="stHorizontalBlock"] { flex-wrap: wrap !important; gap: 0.6rem !important; }
            [data-testid="stHorizontalBlock"] > [data-testid="stColumn"] {
                flex: 1 1 100% !important; min-width: 100% !important; width: 100% !important;
            }
            h1 { font-size: 1.5rem !important; }

            section[data-testid="stSidebar"] { min-width: 84vw !important; width: 84vw !important; }
            section[data-testid="stSidebar"][aria-expanded="false"] {
                transform: translateX(-100%) !important; min-width: 84vw !important; width: 84vw !important;
            }
            .js-plotly-plot, .stPlotlyChart, [data-testid="stDataFrame"] { width: 100% !important; }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
