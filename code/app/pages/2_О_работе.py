"""Страница «О работе»."""

import sys
from pathlib import Path

import streamlit as st

APP_ROOT = Path(__file__).resolve().parents[1]
if str(APP_ROOT) not in sys.path:
    sys.path.insert(0, str(APP_ROOT))

from core.ui import init_page, render_footer  # noqa: E402

init_page("О работе")

st.title("О работе")
st.caption("Магистерская ВКР, защита — 1 июня 2026.")

col_left, col_right = st.columns([2, 1], gap="large")

with col_left:
    with st.container(border=True):
        st.subheader("Тема")
        st.markdown(
            "Устранение помеховых сигналов при измерении диаграмм обратного "
            "рассеяния в безэховых камерах с неудовлетворительными безэховыми "
            "условиями."
        )

    with st.container(border=True):
        st.subheader("Научная новизна")
        st.markdown(
            "Разработка гибридного метода обработки сигналов БЭК с "
            "неудовлетворительными безэховыми условиями, сочетающего "
            "классическую ISAR-фокусировку с автоматизированной атрибуцией "
            "помеховых сигналов на базе мультимодальной языковой модели (VLM)."
        )

    with st.container(border=True):
        st.subheader("Ключевая литература")
        st.markdown(
            """
1. Chen V. C., Martorella M. *Inverse Synthetic Aperture Radar Imaging.*
2. Karakassiliotis. *ISAR Part I: Introduction.*
3. Елизаров С. В. Синтез РЛИ методом ISAR. *Радиолокация и связь*, 2019.
4. Елизаров С. В. Частотно-временной метод в задачах измерения ЭПР.
   *Радиолокация и связь*.
5. Мицмахер М. Ю., Торгованов В. А. *Безэховые камеры СВЧ.*
6. Майзельс Е. Н., Торгованов В. А. *Исследование характеристик
   рассеяния радиолокационных целей.* — М.: Советское радио, 1972.
            """
        )

with col_right:
    with st.container(border=True):
        st.subheader("Автор и руководитель")
        st.markdown(
            """
- **Студент:** Певненко Александр Александрович
- **Группа:** М01-402б
- **Научный руководитель:** Елизаров С.В., к.т.н.
            """
        )

    with st.container(border=True):
        st.subheader("Кафедра")
        st.markdown(
            """
- **МФТИ**, ФРКТ
- Кафедра радиофизики и технической кибернетики
- **База эксперимента:** ПАО «Радиофизика»
            """
        )

    with st.container(border=True):
        st.subheader("Статус разработки")
        st.markdown(
            """
- ✅ Шаблон ВКР (ГОСТ 7.32-2017)
- ✅ План эксперимента
- 🔄 Обзор литературы (гл. 1)
- 🔄 Сигнальный пайплайн (прототип)
- 📅 VLM-интеграция
- 📅 Натурные измерения в БЭК
            """
        )

render_footer()
