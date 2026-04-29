"""
Синтетическая модель радиолокационного эксперимента в БЭК.

Цель — эталонный металлический цилиндр (PEC), вращающийся на поворотной
установке. Параметры: диаметр D, высота H, торцы запаяны/один открыт.

Помехи моделируются когерентными отражениями на фиксированных дальностях
(стенки камеры, оснастка) плюс тепловой шум приёмника.

Это упрощённая модель для демонстрации пайплайна, не претендующая на
физическую точность. Реальный численный расчёт рассеяния — следующий этап.
"""

from dataclasses import dataclass, field
from typing import Literal

import numpy as np

C_LIGHT = 299_792_458.0  # м/с


@dataclass
class CylinderConfig:
    """Эталонный цилиндр (вращается вокруг вертикальной оси на турельной установке)."""

    diameter_m: float = 0.20         # Ø, м
    height_m: float = 0.40           # H, м
    sealed_both_ends: bool = True    # True — оба торца запаяны; False — один открыт
    material: str = "PEC"            # идеально проводящий металл

    @property
    def description(self) -> str:
        ends = "оба торца запаяны" if self.sealed_both_ends else "один торец открыт"
        return (
            f"Ø {self.diameter_m * 100:.0f} см · H {self.height_m * 100:.0f} см · "
            f"{ends} · металл (PEC)"
        )


@dataclass
class ChamberConfig:
    """Параметры безэховости камеры."""

    label: str
    anechoic_quality: Literal["satisfactory", "unsatisfactory"] = "satisfactory"
    clutter_level_db: float = -30.0
    clutter_ranges_m: tuple = (3.5, 5.8, 7.2)
    noise_floor_db: float = -50.0


@dataclass
class MeasurementConfig:
    """Параметры измерения."""

    f_start_hz: float = 8.0e9
    f_stop_hz: float = 12.0e9
    n_freq: int = 201
    n_angles: int = 361
    target_range_m: float = 4.0
    cylinder: CylinderConfig = field(default_factory=CylinderConfig)


@dataclass
class SimulationResult:
    frequencies: np.ndarray
    angles_deg: np.ndarray
    iq: np.ndarray = field(repr=False)
    target_rcs_pattern_m2: np.ndarray = field(repr=False, default=None)
    meta: dict = field(default_factory=dict)


PRESETS = {
    "good_sealed": {
        "chamber": ChamberConfig(
            label="Удовлетворительная безэховость, цилиндр запаян",
            anechoic_quality="satisfactory",
            clutter_level_db=-45.0,
            clutter_ranges_m=(6.0,),
            noise_floor_db=-55.0,
        ),
        "measurement": MeasurementConfig(
            cylinder=CylinderConfig(diameter_m=0.20, height_m=0.40, sealed_both_ends=True),
        ),
    },
    "unsat_sealed": {
        "chamber": ChamberConfig(
            label="Неудовлетворительная безэховость, цилиндр запаян",
            anechoic_quality="unsatisfactory",
            clutter_level_db=-12.0,
            clutter_ranges_m=(3.2, 5.8, 7.1, 9.0),
            noise_floor_db=-40.0,
        ),
        "measurement": MeasurementConfig(
            cylinder=CylinderConfig(diameter_m=0.20, height_m=0.40, sealed_both_ends=True),
        ),
    },
    "unsat_open": {
        "chamber": ChamberConfig(
            label="Неудовлетворительная безэховость, цилиндр с открытым торцом",
            anechoic_quality="unsatisfactory",
            clutter_level_db=-14.0,
            clutter_ranges_m=(3.0, 4.5, 6.0, 7.8, 9.5),
            noise_floor_db=-42.0,
        ),
        "measurement": MeasurementConfig(
            cylinder=CylinderConfig(diameter_m=0.20, height_m=0.40, sealed_both_ends=False),
        ),
    },
    "unsat_small": {
        "chamber": ChamberConfig(
            label="Неудовлетворительная безэховость, малый цилиндр (стелс-уровни)",
            anechoic_quality="unsatisfactory",
            clutter_level_db=-10.0,
            clutter_ranges_m=(3.8, 6.1, 7.9),
            noise_floor_db=-38.0,
        ),
        "measurement": MeasurementConfig(
            cylinder=CylinderConfig(diameter_m=0.05, height_m=0.10, sealed_both_ends=True),
        ),
    },
}


def cylinder_rcs_pattern(
    angles_deg: np.ndarray,
    cylinder: CylinderConfig,
    freq_center_hz: float,
) -> np.ndarray:
    """ЭПР цилиндра как функция угла поворота, м².

    Угол θ=0°/180° — широкая сторона (broadside, перпендикулярно оси цилиндра),
    максимум σ_b = 2π·a·H² / λ.
    Угол θ=90°/270° — торцом к антенне, σ_disc = 4π³·a⁴/λ².
    Если sealed_both_ends=False — один из торцов открытый, его пик подавлен.
    """
    a = cylinder.diameter_m / 2.0
    h = cylinder.height_m
    lam = C_LIGHT / freq_center_hz
    k = 2.0 * np.pi / lam

    sigma_broadside = 2.0 * np.pi * a * h * h / lam
    sigma_endcap = 4.0 * np.pi ** 3 * a ** 4 / (lam * lam)

    th = np.deg2rad(angles_deg)
    sin_t = np.sin(th)
    cos_t = np.cos(th)

    # Широкая сторона: пики на 0° и 180° (sin(θ)→0)
    side = sigma_broadside * np.sinc(k * h * sin_t / np.pi) ** 2

    # Торцы: пики на 90° и 270° (cos(θ)→0)
    cap = sigma_endcap * np.sinc(k * a * cos_t / np.pi) ** 2 * sin_t ** 2

    if cylinder.sealed_both_ends:
        return side + cap

    # Один торец (около θ=270°) открыт — подавим его на ±25°
    delta = np.abs(((angles_deg - 270.0 + 180.0) % 360.0) - 180.0)
    suppress = np.where(delta < 25.0, 0.12, 1.0)
    return side + cap * suppress


def simulate(
    chamber: ChamberConfig,
    measurement: MeasurementConfig,
    seed: int = 42,
) -> SimulationResult:
    rng = np.random.default_rng(seed)
    freqs = np.linspace(measurement.f_start_hz, measurement.f_stop_hz, measurement.n_freq)
    angles = np.linspace(0.0, 360.0, measurement.n_angles, endpoint=False)
    f0 = float(np.mean(freqs))

    n_angles = len(angles)
    n_freq = len(freqs)
    iq = np.zeros((n_angles, n_freq), dtype=np.complex128)

    rcs_pattern = cylinder_rcs_pattern(angles, measurement.cylinder, f0)
    target_amp = np.sqrt(np.maximum(rcs_pattern, 1e-12))
    target_phase = 2.0 * np.pi * freqs * (2.0 * measurement.target_range_m) / C_LIGHT
    for i in range(n_angles):
        iq[i, :] += target_amp[i] * np.exp(-1j * target_phase)

    # помехи: когерентные отражения на фикс. дальностях относительно медианной σ цели
    target_amp_ref = float(np.median(target_amp))
    for r_clutter in chamber.clutter_ranges_m:
        amp = target_amp_ref * 10 ** (chamber.clutter_level_db / 20.0)
        amp_per_angle = amp * (1.0 + 0.5 * rng.standard_normal(n_angles))
        clutter_phase = 2.0 * np.pi * freqs * (2.0 * r_clutter) / C_LIGHT
        phase_jitter = rng.uniform(0.0, 2.0 * np.pi)
        for i in range(n_angles):
            iq[i, :] += amp_per_angle[i] * np.exp(-1j * (clutter_phase + phase_jitter))

    # тепловой шум
    noise_amp = target_amp_ref * 10 ** (chamber.noise_floor_db / 20.0)
    iq += noise_amp * (
        rng.standard_normal(iq.shape) + 1j * rng.standard_normal(iq.shape)
    ) / np.sqrt(2.0)

    return SimulationResult(
        frequencies=freqs,
        angles_deg=angles,
        iq=iq,
        target_rcs_pattern_m2=rcs_pattern,
        meta={
            "chamber": chamber.label,
            "anechoic_quality": chamber.anechoic_quality,
            "cylinder": measurement.cylinder.description,
            "target_range_m": measurement.target_range_m,
            "rcs_max_m2": float(np.max(rcs_pattern)),
            "rcs_median_m2": float(np.median(rcs_pattern)),
        },
    )
