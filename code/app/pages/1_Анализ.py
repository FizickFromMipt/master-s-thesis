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

st.set_page_config(page_title="Анализ | ЭПР в БЭК", layout="wide")
st.title("Анализ измерений")

with st.sidebar:
    st.header("Сценарий")
    preset_keys = list(PRESETS.keys())
    preset_labels = {k: PRESETS[k]["chamber"].label for k in preset_keys}
    preset_choice = st.selectbox(
        "Выберите пресет",
        preset_keys,
        format_func=lambda k: preset_labels[k],
        index=1,
    )
    st.caption("Синтетические данные для демонстрации пайплайна.")
    st.divider()
    st.header("Параметры обработки")
    gate_width = st.slider(
        "Ширина селекции по дальности, м",
        min_value=0.1,
        max_value=2.0,
        value=0.6,
        step=0.1,
    )
    seed = st.number_input("Seed генератора", value=42, step=1)
    st.divider()
    run = st.button("Обработать", type="primary", use_container_width=True)

preset = PRESETS[preset_choice]
chamber = preset["chamber"]
measurement = preset["measurement"]

left, right = st.columns([1, 1])
with left:
    st.subheader("Конфигурация")
    st.markdown(
        f"""
- **Сценарий:** {chamber.label}
- **Диапазон частот:** {measurement.f_start_hz / 1e9:.1f}–{measurement.f_stop_hz / 1e9:.1f} ГГц
- **Количество точек по частоте:** {measurement.n_freq}
- **Количество углов:** {measurement.n_angles}
- **Дальность цели:** {measurement.target_range_m:.2f} м
- **ЭПР цели (задано):** {measurement.target_rcs_dbsm:+.1f} дБ·м²
- **Помехи:** {len(chamber.clutter_ranges_m)} источник(ов),
  уровень {chamber.clutter_level_db:+.1f} дБ относительно цели
        """
    )
with right:
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

    st.subheader("Диаграмма обратного рассеяния (360°)")
    fig = go.Figure()
    fig.add_trace(
        go.Scatterpolar(
            r=result.rcs_raw_db,
            theta=sim.angles_deg,
            mode="lines",
            name="Сырая",
            line=dict(width=1),
        )
    )
    fig.add_trace(
        go.Scatterpolar(
            r=result.rcs_classic_db,
            theta=sim.angles_deg,
            mode="lines",
            name="Классика (time-gating)",
            line=dict(width=1.5, dash="dash"),
        )
    )
    fig.add_trace(
        go.Scatterpolar(
            r=result.rcs_cleaned_db,
            theta=sim.angles_deg,
            mode="lines",
            name="Гибридный метод",
            line=dict(width=2),
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
        legend=dict(orientation="h"),
        height=520,
        margin=dict(l=10, r=10, t=30, b=10),
    )
    st.plotly_chart(fig, use_container_width=True)

    col_a, col_b = st.columns([1, 1])
    with col_a:
        st.subheader("Range-Doppler изображение")
        fig_rd = go.Figure(
            data=go.Heatmap(
                z=result.range_doppler_db,
                x=result.ranges_m,
                y=np.linspace(-0.5, 0.5, result.range_doppler_db.shape[0]),
                colorscale="Viridis",
                zmin=-40,
                zmax=0,
                colorbar=dict(title="дБ"),
            )
        )
        fig_rd.update_layout(
            xaxis_title="Дальность, м",
            yaxis_title="Нормированная Doppler-частота",
            height=420,
            margin=dict(l=10, r=10, t=30, b=10),
        )
        st.plotly_chart(fig_rd, use_container_width=True)

    with col_b:
        st.subheader("Средний range-профиль")
        fig_rp = go.Figure()
        fig_rp.add_trace(
            go.Scatter(
                x=result.ranges_m,
                y=20 * np.log10(result.range_profile / result.range_profile.max() + 1e-12),
                mode="lines",
                name="|Profile|, дБ",
            )
        )
        fig_rp.add_vrect(
            x0=result.gate_low_m,
            x1=result.gate_high_m,
            line_width=0,
            fillcolor="green",
            opacity=0.15,
            annotation_text="ворота цели",
            annotation_position="top left",
        )
        fig_rp.update_layout(
            xaxis_title="Дальность, м",
            yaxis_title="Уровень, дБ",
            height=420,
            margin=dict(l=10, r=10, t=30, b=10),
            showlegend=False,
        )
        st.plotly_chart(fig_rp, use_container_width=True)

    st.subheader("Метрики")
    m1, m2, m3 = st.columns(3)
    m1.metric("PSR (подавление помех)", f"{result.psr_db:+.1f} дБ")
    rcs_peak_db = float(np.max(result.rcs_cleaned_db))
    m2.metric("Пиковый уровень ДОР (гибрид)", f"{rcs_peak_db:+.2f} дБ")
    m3.metric("Время обработки", f"{elapsed * 1000:.0f} мс")

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
