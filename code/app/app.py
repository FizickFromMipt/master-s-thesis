"""Главная страница."""

import streamlit as st

from core.ui import init_page, render_footer

init_page("Главная", sidebar="collapsed")

# ── Hero ──────────────────────────────────────────────────────────
st.markdown(
    """
    <div class="hero">
        <span class="hero__eyebrow">Магистерская ВКР · 2026</span>
        <h1 class="hero__title">
            Гибридный метод устранения <em>помех</em> при&nbsp;измерении ЭПР
            в&nbsp;безэховых камерах
        </h1>
        <p class="hero__lead">
            ISAR-фокусировка плюс автоматизированная атрибуция помеховых
            сигналов визуально-языковой моделью. Восстанавливает диаграмму
            обратного рассеяния и&nbsp;объясняет, что именно происходило
            в&nbsp;камере во время измерения.
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)

cta1, cta2, _ = st.columns([1.4, 1.2, 4])
with cta1:
    st.page_link(
        "pages/1_Анализ.py",
        label="Запустить анализ",
        icon=":material/insights:",
    )
with cta2:
    st.page_link(
        "pages/2_О_работе.py",
        label="О работе",
        icon=":material/description:",
    )

st.write("")
st.write("")

# ── Три карточки с описанием пайплайна ────────────────────────────
f1, f2, f3 = st.columns(3, gap="medium")
with f1:
    with st.container(border=True):
        st.markdown(":material/radar: **Сигнальная часть**")
        st.write(
            "ISAR-фокусировка сырых IQ-данных, построение range-Doppler "
            "изображения, селекция по дальности и адаптивная фильтрация."
        )
with f2:
    with st.container(border=True):
        st.markdown(":material/smart_toy: **Аналитическая часть**")
        st.write(
            "Визуально-языковая модель интерпретирует range-Doppler "
            "изображение и атрибутирует источники помех — стены, "
            "оснастка, мультипут."
        )
with f3:
    with st.container(border=True):
        st.markdown(":material/insights: **Результат**")
        st.write(
            "Восстановленная ДОР с количественной оценкой подавления "
            "(PSR, разрешение, погрешность ЭПР) и текстовым объяснением."
        )

st.write("")

# ── Блок-схема + блок инфо ────────────────────────────────────────
left, right = st.columns([2, 1], gap="large")

with left:
    with st.container(border=True):
        st.subheader("Блок-схема метода")
        st.code(
            """
  IQ (сырые)
      |
      v
  [ ISAR-фокусировка ]
      |
      v
  [ Range-Doppler изображение ]----+
      |                            |
      v                            v
  [ Подавление помех ]      [ VLM-атрибуция ]
      |                            |
      v                            v
  [ Восстановление ДОР ]   [ Диагностический отчёт ]
      \\__________________________/
                  |
                  v
         Итоговый результат
            """,
            language="text",
        )

with right:
    with st.container(border=True):
        st.subheader("Метрики")
        st.markdown(
            """
- **PSR** — Parasitic Suppression Ratio, дБ
- **Ширина главного лепестка** ДОР
- **Уровень боковых максимумов**
- **Погрешность ЭПР** относительно эталона
- **Время обработки**
            """
        )
    with st.container(border=True):
        st.subheader("Авторы")
        st.markdown(
            """
**Студент:** Певненко А.А., М01-402б
**Руководитель:** Елизаров С.В., к.т.н.
**База:** ПАО «Радиофизика»
            """
        )

render_footer()
