"""VLM-сервис: диагностический отчёт по результатам обработки.

MVP-заглушка: возвращает детерминированную классификацию помех на основе
переданных дальностей и параметров эксперимента. Реальная VL-модель
(llava / Llama-3-V через Ollama, либо Anthropic/OpenAI API) подключается
позднее — интерфейс /analyze останется тем же.
"""

from __future__ import annotations

from typing import Optional

from fastapi import FastAPI
from pydantic import BaseModel, Field

app = FastAPI(title="VLM Diagnostic Service", version="0.1.0")

CLUTTER_TAXONOMY = [
    "переотражение от боковой стенки",
    "переотражение от потолка/пола",
    "оснастка поворотной установки",
    "мультипут через пол",
    "паразитное отражение от калибровочной мишени",
]


class AnalyzeRequest(BaseModel):
    chamber_label: str
    anechoic_quality: str = "unsatisfactory"
    cluster_ranges_m: list[float] = Field(default_factory=list)
    psr_db: float = 0.0
    cylinder_diameter_m: float = 0.20
    cylinder_height_m: float = 0.40
    cylinder_sealed: bool = True
    rcs_max_m2: float = 1.0


class SourceItem(BaseModel):
    type: str
    range_m: float
    confidence: float


class AnalyzeResponse(BaseModel):
    summary: str
    sources: list[SourceItem]
    recommendation: str
    confidence: float
    model_id: str = "stub-v0"


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/analyze", response_model=AnalyzeResponse)
def analyze(req: AnalyzeRequest) -> AnalyzeResponse:
    sources: list[SourceItem] = []
    for i, r in enumerate(req.cluster_ranges_m):
        kind = CLUTTER_TAXONOMY[i % len(CLUTTER_TAXONOMY)]
        # «доверие» — простая эвристика: чем дальше источник, тем менее уверены
        conf = max(0.55, 0.92 - 0.04 * i - 0.01 * abs(r - 5.0))
        sources.append(SourceItem(type=kind, range_m=float(r), confidence=round(conf, 2)))

    sealed_str = "оба торца запаяны" if req.cylinder_sealed else "один торец открыт"
    quality_str = (
        "удовлетворительной" if req.anechoic_quality.startswith("satis") else
        "неудовлетворительной"
    )

    summary = (
        f"Сценарий «{req.chamber_label}». Безэховость камеры — {quality_str}. "
        f"Цель: цилиндр Ø{req.cylinder_diameter_m * 100:.0f} см, "
        f"H {req.cylinder_height_m * 100:.0f} см, {sealed_str}. "
        f"Теоретический максимум σ ≈ {req.rcs_max_m2:.3g} м². "
        f"Обнаружено {len(req.cluster_ranges_m)} помеховых источника."
    )

    if req.psr_db >= 12.0:
        rec_quality = "хорошее"
    elif req.psr_db >= 6.0:
        rec_quality = "приемлемое"
    else:
        rec_quality = "недостаточное"

    recommendation = (
        f"Подавление помех {rec_quality} (PSR={req.psr_db:.1f} дБ). "
        + ("Метод применим как есть. " if req.psr_db >= 12.0 else
           "Рекомендуется уточнить ширину селекции по дальности или "
           "включить вторую итерацию подавления. ")
        + (
            "На стелс-уровнях ЭПР (10⁻³ м²) текущая безэховость камеры "
            "не позволит получить достоверный результат — требуется доработка."
            if req.anechoic_quality.startswith("unsatis") and req.psr_db < 15.0
            else "Метод воспроизводится для серии измерений."
        )
    )

    overall_conf = max(0.5, min(0.95, 0.6 + 0.02 * req.psr_db))
    return AnalyzeResponse(
        summary=summary,
        sources=sources,
        recommendation=recommendation,
        confidence=round(overall_conf, 2),
    )
