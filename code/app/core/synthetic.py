"""
Синтетическая модель радиолокационного эксперимента в БЭК.

Генерирует IQ-данные с учётом:
- отклика целевой мишени (эталонная сфера с постоянной ЭПР);
- помеховых сигналов от переотражений стенок и оснастки;
- теплового шума приёмника.

Всё это — упрощённая модель для демонстрации пайплайна,
не претендующая на физическую точность. Реальный численный
расчёт рассеяния будет добавлен позже.
"""

from dataclasses import dataclass, field
from typing import Literal

import numpy as np

C_LIGHT = 299_792_458.0  # м/с


@dataclass
class ChamberConfig:
    """Параметры безэховой камеры."""

    label: str
    chamber_quality: Literal["good", "bad"] = "good"
    clutter_level_db: float = -30.0          # уровень помех относительно цели
    clutter_ranges_m: tuple = (3.5, 5.8, 7.2)  # дальности помеховых источников
    noise_floor_db: float = -50.0


@dataclass
class MeasurementConfig:
    """Параметры измерения."""

    f_start_hz: float = 8.0e9
    f_stop_hz: float = 12.0e9
    n_freq: int = 201
    n_angles: int = 361              # шаг 1 градус
    target_range_m: float = 4.0      # дальность цели
    target_rcs_dbsm: float = 0.0     # ЭПР цели, дБ·м²


@dataclass
class SimulationResult:
    """Результат синтетической съёмки."""

    frequencies: np.ndarray
    angles_deg: np.ndarray
    iq: np.ndarray = field(repr=False)  # [n_angles, n_freq] complex
    meta: dict = field(default_factory=dict)


PRESETS = {
    "good_sphere": {
        "chamber": ChamberConfig(
            label="Идеальная БЭК, сфера",
            chamber_quality="good",
            clutter_level_db=-45.0,
            clutter_ranges_m=(6.0,),
            noise_floor_db=-55.0,
        ),
        "measurement": MeasurementConfig(target_rcs_dbsm=0.0),
    },
    "bad_sphere": {
        "chamber": ChamberConfig(
            label="Плохая БЭК, сфера",
            chamber_quality="bad",
            clutter_level_db=-12.0,
            clutter_ranges_m=(3.2, 5.8, 7.1, 9.0),
            noise_floor_db=-40.0,
        ),
        "measurement": MeasurementConfig(target_rcs_dbsm=0.0),
    },
    "bad_corner": {
        "chamber": ChamberConfig(
            label="Плохая БЭК, уголковый отражатель",
            chamber_quality="bad",
            clutter_level_db=-10.0,
            clutter_ranges_m=(3.8, 6.1, 7.9),
            noise_floor_db=-38.0,
        ),
        "measurement": MeasurementConfig(target_rcs_dbsm=10.0),
    },
    "bad_object": {
        "chamber": ChamberConfig(
            label="Плохая БЭК, реальный объект",
            chamber_quality="bad",
            clutter_level_db=-14.0,
            clutter_ranges_m=(3.0, 4.5, 6.0, 7.8, 9.5),
            noise_floor_db=-42.0,
        ),
        "measurement": MeasurementConfig(target_rcs_dbsm=5.0),
    },
}


def simulate(
    chamber: ChamberConfig,
    measurement: MeasurementConfig,
    seed: int = 42,
) -> SimulationResult:
    rng = np.random.default_rng(seed)
    freqs = np.linspace(measurement.f_start_hz, measurement.f_stop_hz, measurement.n_freq)
    angles = np.linspace(0.0, 360.0, measurement.n_angles, endpoint=False)

    n_angles = len(angles)
    n_freq = len(freqs)
    iq = np.zeros((n_angles, n_freq), dtype=np.complex128)

    # --- отклик цели: постоянная амплитуда, зависит от угла (диаграмма) ---
    target_amp = 10 ** (measurement.target_rcs_dbsm / 20.0)
    target_pattern = target_amp * (1.0 + 0.3 * np.cos(np.deg2rad(angles)) ** 2)
    target_phase = 2 * np.pi * freqs * (2 * measurement.target_range_m) / C_LIGHT
    for i in range(n_angles):
        iq[i, :] += target_pattern[i] * np.exp(-1j * target_phase)

    # --- помехи от стенок: несколько когерентных отражений на фикс. дальностях ---
    for r_clutter in chamber.clutter_ranges_m:
        amp = 10 ** (chamber.clutter_level_db / 20.0)
        amp *= (1.0 + 0.5 * rng.standard_normal(n_angles))
        clutter_phase = 2 * np.pi * freqs * (2 * r_clutter) / C_LIGHT
        phase_jitter = rng.uniform(0, 2 * np.pi)
        for i in range(n_angles):
            iq[i, :] += amp[i] * np.exp(-1j * (clutter_phase + phase_jitter))

    # --- тепловой шум ---
    noise_amp = 10 ** (chamber.noise_floor_db / 20.0)
    iq += noise_amp * (
        rng.standard_normal(iq.shape) + 1j * rng.standard_normal(iq.shape)
    ) / np.sqrt(2)

    return SimulationResult(
        frequencies=freqs,
        angles_deg=angles,
        iq=iq,
        meta={
            "chamber": chamber.label,
            "target_rcs_dbsm": measurement.target_rcs_dbsm,
            "target_range_m": measurement.target_range_m,
        },
    )
