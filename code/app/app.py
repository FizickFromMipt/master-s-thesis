"""Главная — минимальный лаунчер."""

import streamlit as st

from core.ui import init_page, render_footer

# Используемая предобученная модель (HF: llava-hf/llava-v1.6-mistral-7b-hf)
MODEL_NAME = "LLaVA-1.6 (Mistral-7B)"

init_page("Главная", sidebar="collapsed")

st.title("Восстановление ДОР и диагностика помех")
st.caption("Демонстрация пайплайна обработки радиолокационных измерений.")

with st.container(border=True):
    st.markdown(
        f"Это не готовый продукт, а **демонстрация подхода**. "
        f"Сырые измерения проходят сигнальную обработку, а **предобученная "
        f"модель {MODEL_NAME}** диагностирует источники помех. "
        f"На выходе — **диаграмма обратного рассеяния (ДОР)** эталонного цилиндра."
    )

st.write("")

if st.button("Анализ измерений", type="primary", use_container_width=True,
             icon=":material/insights:"):
    st.switch_page("pages/1_Анализ.py")

if st.button("Загрузить замеры", use_container_width=True,
             icon=":material/upload:"):
    st.switch_page("pages/3_Загрузка.py")

render_footer()
