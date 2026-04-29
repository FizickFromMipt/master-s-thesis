"""Страница интерактивного анализа."""

import io
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import plotly.graph_objects as go
import streamlit as st

APP_ROOT = Path(__file__).resolve().parents[1]
if str(APP_ROOT) not in sys.path:
    sys.path.insert(0, str(APP_ROOT))

from core import vlm_client  # noqa: E402
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
    st.caption("Синтетика для демонстрации пайплайна.")

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
cyl = measurement.cylinder

left, right = st.columns([1, 1], gap="large")
with left:
    with st.container(border=True):
        st.subheader("Конфигурация")
        st.markdown(
            f"""
- **Сценарий:** {chamber.label}
- **Цилиндр:** {cyl.description}
- **Диапазон частот:** {measurement.f_start_hz / 1e9:.1f}–{measurement.f_stop_hz / 1e9:.1f} ГГц
- **Точек по частоте:** {measurement.n_freq}
- **Углов:** {measurement.n_angles}
- **Дальность цели:** {measurement.target_range_m:.2f} м
- **Помехи:** {len(chamber.clutter_ranges_m)} источник(ов),
  уровень {chamber.clutter_level_db:+.1f} дБ относительно цели
            """
        )
with right:
    with st.container(border=True):
        st.subheader("Целевые показатели")
        st.markdown(
            """
- Δ между теоретической и экспериментальной σ — **до 1.5 дБ**
- ДОР приведена к **0 дБ·м² ≈ 1 м²** (нормировка по медиане);
  справочно стелс-уровни — **10⁻² … 10⁻³ м²**
- Положительный PSR (чем больше, тем лучше подавление)
- Восстановленная ДОР ближе к эталонной форме цилиндра
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
    rcs_peak_db = float(np.max(result.rcs_cleaned_db))
    rcs_max_m2 = float(sim.meta.get("rcs_max_m2", 0.0))
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("PSR", f"{result.psr_db:+.1f} дБ")
    m2.metric("Пик ДОР (гибрид)", f"{rcs_peak_db:+.2f} дБ")
    m3.metric("σ_max теор.", f"{rcs_max_m2:.3g} м²")
    m4.metric("Время обработки", f"{elapsed * 1000:.0f} мс")

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
            radialaxis=dict(range=[-40, 5], ticksuffix=" дБ", tickfont=dict(size=10)),
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

    # ── Диагностический отчёт от VLM-сервиса ──────────────────────
    st.subheader("Диагностический отчёт")
    payload = {
        "chamber_label": chamber.label,
        "anechoic_quality": chamber.anechoic_quality,
        "cluster_ranges_m": list(chamber.clutter_ranges_m),
        "psr_db": float(result.psr_db),
        "cylinder_diameter_m": cyl.diameter_m,
        "cylinder_height_m": cyl.height_m,
        "cylinder_sealed": cyl.sealed_both_ends,
        "rcs_max_m2": rcs_max_m2,
    }
    with st.spinner("Запрос в VLM-сервис…"):
        report = vlm_client.analyze(payload)

    if report is None:
        st.warning(
            "VLM-сервис недоступен — диагностический отчёт пропущен. "
            "Проверь, что контейнер `vlm` поднят (см. `docker compose ps`)."
        )
    else:
        st.info(
            f"**Сводка:** {report.get('summary', '')}\n\n"
            f"**Рекомендация:** {report.get('recommendation', '')}\n\n"
            f"_Доверие модели: {report.get('confidence', 0):.0%}_"
        )
        sources = report.get("sources") or []
        if sources:
            st.write("**Идентифицированные источники помех:**")
            st.dataframe(sources, use_container_width=True, hide_index=True)

    # ── Экспорт результата ────────────────────────────────────────
    st.subheader("Экспорт результата")
    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    base_name = f"rcs_{preset_choice}_{ts}"

    csv_buf = io.StringIO()
    csv_buf.write("angle_deg,rcs_raw_db,rcs_classic_db,rcs_hybrid_db,rcs_theoretical_m2\n")
    for a, r0, rc, rh, rt in zip(
        sim.angles_deg,
        result.rcs_raw_db,
        result.rcs_classic_db,
        result.rcs_cleaned_db,
        sim.target_rcs_pattern_m2,
    ):
        csv_buf.write(f"{a:.2f},{r0:.4f},{rc:.4f},{rh:.4f},{rt:.6e}\n")

    summary_json = {
        "timestamp_utc": ts,
        "preset": preset_choice,
        "chamber": {
            "label": chamber.label,
            "anechoic_quality": chamber.anechoic_quality,
            "clutter_level_db": chamber.clutter_level_db,
            "clutter_ranges_m": list(chamber.clutter_ranges_m),
            "noise_floor_db": chamber.noise_floor_db,
        },
        "cylinder": {
            "diameter_m": cyl.diameter_m,
            "height_m": cyl.height_m,
            "sealed_both_ends": cyl.sealed_both_ends,
            "material": cyl.material,
        },
        "measurement": {
            "f_start_hz": measurement.f_start_hz,
            "f_stop_hz": measurement.f_stop_hz,
            "n_freq": measurement.n_freq,
            "n_angles": measurement.n_angles,
            "target_range_m": measurement.target_range_m,
        },
        "metrics": {
            "psr_db": float(result.psr_db),
            "rcs_peak_hybrid_db": rcs_peak_db,
            "rcs_max_theoretical_m2": rcs_max_m2,
            "elapsed_ms": int(elapsed * 1000),
            "gate_low_m": result.gate_low_m,
            "gate_high_m": result.gate_high_m,
        },
        "vlm_report": report,
    }

    e1, e2 = st.columns(2)
    with e1:
        st.download_button(
            "Скачать ДОР (CSV)",
            data=csv_buf.getvalue().encode("utf-8"),
            file_name=f"{base_name}.csv",
            mime="text/csv",
            use_container_width=True,
        )
    with e2:
        st.download_button(
            "Скачать сводку (JSON)",
            data=json.dumps(summary_json, ensure_ascii=False, indent=2).encode("utf-8"),
            file_name=f"{base_name}.json",
            mime="application/json",
            use_container_width=True,
        )
else:
    st.info("Нажмите «Обработать» в панели слева, чтобы запустить демонстрацию.")

render_footer()
