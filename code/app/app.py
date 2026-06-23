"""Главная — минимальный лаунчер."""

import streamlit as st

from core.ui import init_page, render_footer

init_page("Главная", sidebar="collapsed")

st.title("ЭПР в БЭК")
st.caption("Подавление помех и восстановление диаграммы обратного рассеяния.")

st.write("")

if st.button("Анализ измерений", type="primary", use_container_width=True,
             icon=":material/insights:"):
    st.switch_page("pages/1_Анализ.py")

if st.button("Загрузить замеры", use_container_width=True,
             icon=":material/upload:"):
    st.switch_page("pages/3_Загрузка.py")

render_footer()
