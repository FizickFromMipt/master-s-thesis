"""
Пайплайн обработки сигналов: упрощённая реализация для демонстрации.

Реализовано:
- построение range-профиля (IFFT по частоте с оконной функцией);
- range-Doppler изображение (двумерный спектр);
- time-gating помех (простая маска по дальности);
- восстановление ДОР до и после обработки;
- расчёт метрики PSR.

Замена на полноценный ISAR-алгоритм — в рамках главы 3 ВКР.
"""

from dataclasses import dataclass
from typing import Optional

import numpy as np
from scipy.signal import windows

from .synthetic import C_LIGHT, SimulationResult


@dataclass
class ProcessingResult:
    ranges_m: np.ndarray
    range_profile: np.ndarray           # средний по углам |·|
    range_doppler_db: np.ndarray        # РЛИ в дБ
    rcs_raw_db: np.ndarray              # ДОР до обработки
    rcs_cleaned_db: np.ndarray          # ДОР после подавления помех
    rcs_classic_db: np.ndarray          # ДОР после классического time-gating
    psr_db: float                       # коэффициент подавления помех
    target_range_m: float
    gate_low_m: float
    gate_high_m: float


def _range_profile(iq: np.ndarray, freqs: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """IFFT по частоте → профиль по дальности."""
    n_freq = iq.shape[1]
    win = windows.hann(n_freq)
    iq_windowed = iq * win[None, :]
    profile = np.fft.ifft(iq_windowed, n=n_freq, axis=1)
    df = freqs[1] - freqs[0]
    dr = C_LIGHT / (2.0 * df * n_freq)
    ranges = np.arange(n_freq) * dr
    return ranges, profile


def _range_doppler(profile: np.ndarray) -> np.ndarray:
    """Range-Doppler: FFT по углу (медленное время)."""
    rd = np.fft.fftshift(np.fft.fft(profile, axis=0), axes=0)
    mag = np.abs(rd) + 1e-12
    mag_db = 20.0 * np.log10(mag / mag.max())
    return mag_db


def _rcs_from_iq(iq: np.ndarray, freqs: np.ndarray) -> np.ndarray:
    """Диаграмма обратного рассеяния: усреднение мощности по частоте."""
    power = np.mean(np.abs(iq) ** 2, axis=1)
    power_db = 10.0 * np.log10(power / np.max(power) + 1e-12)
    return power_db


def process(
    sim: SimulationResult,
    gate_width_m: float = 0.6,
    target_range_m: Optional[float] = None,
) -> ProcessingResult:
    freqs = sim.frequencies
    iq = sim.iq

    ranges, profile = _range_profile(iq, freqs)

    if target_range_m is None:
        mean_profile = np.mean(np.abs(profile), axis=0)
        target_range_m = float(ranges[np.argmax(mean_profile)])
    gate_low = max(0.0, target_range_m - gate_width_m)
    gate_high = target_range_m + gate_width_m
    mask = (ranges >= gate_low) & (ranges <= gate_high)

    # classic time-gating: жёсткая маска по дальности
    profile_classic = profile.copy()
    profile_classic[:, ~mask] = 0.0
    iq_classic = np.fft.fft(profile_classic, axis=1)

    # "гибридный" метод (заглушка): сглаженная маска + понижение хвостов
    smooth_mask = np.ones_like(ranges)
    smooth_mask[~mask] = 0.08
    edge = 0.3
    edge_len = max(3, int(edge / (ranges[1] - ranges[0])))
    for i in range(edge_len):
        w = 1.0 - i / edge_len
        if np.any(mask):
            idx_low = np.argmax(mask)
            idx_high = len(mask) - 1 - np.argmax(mask[::-1])
            if idx_low - 1 - i >= 0:
                smooth_mask[idx_low - 1 - i] = max(smooth_mask[idx_low - 1 - i], w)
            if idx_high + 1 + i < len(mask):
                smooth_mask[idx_high + 1 + i] = max(smooth_mask[idx_high + 1 + i], w)
    profile_hybrid = profile * smooth_mask[None, :]
    iq_hybrid = np.fft.fft(profile_hybrid, axis=1)

    rd_db = _range_doppler(profile)

    rcs_raw = _rcs_from_iq(iq, freqs)
    rcs_classic = _rcs_from_iq(iq_classic, freqs)
    rcs_hybrid = _rcs_from_iq(iq_hybrid, freqs)

    mean_profile_abs = np.mean(np.abs(profile), axis=0) ** 2
    p_clutter = float(np.sum(mean_profile_abs[~mask]) + 1e-12)
    mean_profile_hybrid_abs = np.mean(np.abs(profile_hybrid), axis=0) ** 2
    p_clutter_after = float(np.sum(mean_profile_hybrid_abs[~mask]) + 1e-12)
    psr = 10.0 * np.log10(p_clutter / p_clutter_after)

    return ProcessingResult(
        ranges_m=ranges,
        range_profile=np.mean(np.abs(profile), axis=0),
        range_doppler_db=rd_db,
        rcs_raw_db=rcs_raw,
        rcs_cleaned_db=rcs_hybrid,
        rcs_classic_db=rcs_classic,
        psr_db=psr,
        target_range_m=target_range_m,
        gate_low_m=gate_low,
        gate_high_m=gate_high,
    )
