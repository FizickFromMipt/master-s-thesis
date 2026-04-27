"""Страница интерактивного анализа."""

import sys
import time
from pathlib import Path

import numpy as np
import plotly.graph_objects as go
import streamlit as st

APP_ROOT = Path(__file__).resolve().parents[1]
if str(APP_ROOT) not in sys.path:
    sys.path.insert(0, str(APP_ROOT))

from core.processing import process  # noqa: E402
from core.synthetic import PRESETS, simulate  # noqa: E402
from core.ui import init_page, render_footer  # noqa: E402

init_page("Анализ", sidebar="expanded")

st.title("Анализ измерений")
st.caption("Интерактивная демонстрация пайплайна на синтетических данных.")

with st.sidebar:
    st.subheader("Сценарий")
    preset_keys = list(PRESETS.keys())
    preset_labels = {k: PRESETS[k]["chamber"].label for k in preset_keys}
    preset_choice = st.selectbox(
        "Пресет камеры",
        preset_keys,
        format_func=lambda k: preset_labels[k],
        index=1,
    )
    st.caption("Синтетические данные для демонстрации пайплайна.")

    st.subheader("Параметры обработки")
    gate_width = st.slider(
        "Ширина селекции по дальности, м",
        min_value=0.1,
        max_value=2.0,
        value=0.6,
        step=0.1,
    )
    seed = st.number_input("Seed генератора", value=42, step=1)
    st.write("")
    run = st.button("Обработать", type="primary", use_container_width=True)

preset = PRESETS[preset_choice]
chamber = preset["chamber"]
measurement = preset["measurement"]

left, right = st.columns([1, 1], gap="large")
with left:
    with st.container(border=True):
        st.subheader("Конфигурация")
        st.markdown(
            f"""
- **Сценарий:** {chamber.label}
- **Диапазон частот:** {measurement.f_start_hz / 1e9:.1f}–{measurement.f_stop_hz / 1e9:.1f} ГГц
- **Точек по частоте:** {measurement.n_freq}
- **Углов:** {measurement.n_angles}
- **Дальность цели:** {measurement.target_range_m:.2f} м
- **ЭПР цели (задано):** {measurement.target_rcs_dbsm:+.1f} дБ·м²
- **Помехи:** {len(chamber.clutter_ranges_m)} источник(ов),
  уровень {chamber.clutter_level_db:+.1f} дБ относительно цели
            """
        )
with right:
    with st.container(border=True):
        st.subheader("Ожидаемый результат")
        st.markdown(
            """
- восстановленная ДОР ближе к эталонной форме;
- выраженное снижение помеховых лепестков;
- положительный PSR (чем больше, тем лучше подавление);
- диагностический отчёт об источниках помех.
            """
        )

if run:
    with st.spinner("Симуляция и обработка…"):
        t0 = time.perf_counter()
        sim = simulate(chamber, measurement, seed=int(seed))
        result = process(sim, gate_width_m=gate_width)
        elapsed = time.perf_counter() - t0

    st.success(
        f"Готово за {elapsed * 1000:.0f} мс. "
        f"Ворота по дальности: "
        f"{result.gate_low_m:.2f}–{result.gate_high_m:.2f} м."
    )

    st.subheader("Метрики")
    m1, m2, m3 = st.columns(3)
    m1.metric("PSR (подавление помех)", f"{result.psr_db:+.1f} дБ")
    rcs_peak_db = float(np.max(result.rcs_cleaned_db))
    m2.metric("Пиковый уровень ДОР (гибрид)", f"{rcs_peak_db:+.2f} дБ")
    m3.metric("Время обработки", f"{elapsed * 1000:.0f} мс")

    st.subheader("Диаграмма обратного рассеяния (360°)")
    fig = go.Figure()
    fig.add_trace(
        go.Scatterpolar(
            r=result.rcs_raw_db,
            theta=sim.angles_deg,
            mode="lines",
            name="Сырая",
            line=dict(width=1, color="#9CA0BF"),
        )
    )
    fig.add_trace(
        go.Scatterpolar(
            r=result.rcs_classic_db,
            theta=sim.angles_deg,
            mode="lines",
            name="Классика (time-gating)",
            line=dict(width=1.5, dash="dash", color="#5A9B8E"),
        )
    )
    fig.add_trace(
        go.Scatterpolar(
            r=result.rcs_cleaned_db,
            theta=sim.angles_deg,
            mode="lines",
            name="Гибридный метод",
            line=dict(width=2.5, color="#2D2E83"),
        )
    )
    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                range=[-40, 5],
                ticksuffix=" дБ",
                tickfont=dict(size=10),
            ),
            angularaxis=dict(direction="clockwise"),
        ),
        legend=dict(orientation="h", y=-0.05),
        height=520,
        margin=dict(l=10, r=10, t=30, b=10),
        paper_bgcolor="rgba(0,0,0,0)",
    )
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("Средний range-профиль")
    fig_rp = go.Figure()
    fig_rp.add_trace(
        go.Scatter(
            x=result.ranges_m,
            y=20 * np.log10(result.range_profile / result.range_profile.max() + 1e-12),
            mode="lines",
            name="|Profile|, дБ",
            line=dict(color="#2D2E83", width=2),
        )
    )
    fig_rp.add_vrect(
        x0=result.gate_low_m,
        x1=result.gate_high_m,
        line_width=0,
        fillcolor="#2D2E83",
        opacity=0.12,
        annotation_text="ворота цели",
        annotation_position="top left",
    )
    fig_rp.update_layout(
        xaxis_title="Дальность, м",
        yaxis_title="Уровень, дБ",
        height=380,
        margin=dict(l=10, r=10, t=30, b=10),
        showlegend=False,
        paper_bgcolor="rgba(0,0,0,0)",
    )
    st.plotly_chart(fig_rp, use_container_width=True)

    st.subheader("Диагностический отчёт (заготовка VLM)")
    st.info(
        f"**Сценарий:** {chamber.label}\n\n"
        f"В range-Doppler изображении обнаружено "
        f"{len(chamber.clutter_ranges_m)} выраженных помеховых источник(а) "
        f"на дальностях: "
        f"{', '.join(f'{r:.1f} м' for r in chamber.clutter_ranges_m)}.\n\n"
        "**Предположительная природа:** переотражения от стенок камеры и "
        "оснастки поворотной установки; возможен мультипут через пол.\n\n"
        "**Рекомендация:** применён гибридный метод с селекцией по "
        "дальности и сглаживанием краёв окна, что дало показанный PSR. "
        "Полный VLM-анализ с привязкой к классам источников помех будет "
        "добавлен в следующих итерациях."
    )
else:
    st.info("Нажмите «Обработать» в панели слева, чтобы запустить демонстрацию.")

render_footer()
