"""VLM-сервис: диагностический отчёт по результатам измерения.

Режимы работы:
- если задан HF_TOKEN → запрос в HuggingFace Inference API
  (по умолчанию модель llava-hf/llava-v1.6-mistral-7b-hf);
- иначе → детерминированная заглушка по таксономии помех (для разработки).

При сбое HF API (timeout, parse error, недоступность) автоматически
fallback на заглушку, чтобы интерфейс не падал.
"""

from __future__ import annotations

import json
import os
import re
from typing import Optional

from fastapi import FastAPI
from pydantic import BaseModel, Field

app = FastAPI(title="VLM Diagnostic Service", version="0.2.0")

HF_TOKEN = os.getenv("HF_TOKEN", "").strip()
HF_MODEL = os.getenv("HF_MODEL", "llava-hf/llava-v1.6-mistral-7b-hf").strip()
HF_PROVIDER = os.getenv("HF_PROVIDER", "auto").strip()  # auto, together, replicate, fireworks-ai

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
    # PNG в base64 (range-профиль или ДОР), опционально — для multimodal-инференса
    image_b64: Optional[str] = None


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


def _build_prompt(req: AnalyzeRequest) -> str:
    sealed_str = "оба торца запаяны" if req.cylinder_sealed else "один торец открыт (полость)"
    quality_str = (
        "удовлетворительной"
        if req.anechoic_quality.startswith("satis")
        else "неудовлетворительной"
    )
    sources_block = (
        "\n".join(
            f"  - источник #{i + 1}: дальность {r:.2f} м"
            for i, r in enumerate(req.cluster_ranges_m)
        )
        or "  - помеховые источники не обнаружены"
    )
    taxonomy = "\n".join(f"  - {t}" for t in CLUTTER_TAXONOMY)
    return (
        "Ты — эксперт по радиолокационным измерениям ЭПР в безэховых камерах. "
        "Проанализируй параметры измерения и дай диагностический отчёт.\n\n"
        f"Сценарий: {req.chamber_label}\n"
        f"Качество безэховости: {quality_str}\n"
        f"Цель: металлический цилиндр Ø{req.cylinder_diameter_m * 100:.0f} см, "
        f"H {req.cylinder_height_m * 100:.0f} см, {sealed_str}\n"
        f"Теоретический максимум σ ≈ {req.rcs_max_m2:.3g} м²\n"
        f"PSR после подавления: {req.psr_db:.1f} дБ\n\n"
        f"Обнаруженные помеховые источники:\n{sources_block}\n\n"
        f"Классифицируй КАЖДЫЙ источник по таксономии:\n{taxonomy}\n\n"
        "Верни СТРОГО JSON без markdown-обрамления, в формате:\n"
        '{"summary": "...", "sources": [{"type": "...", "range_m": <float>, '
        '"confidence": <0..1>}], "recommendation": "...", "confidence": <0..1>}'
    )


def _try_hf(prompt: str, image_b64: Optional[str]) -> Optional[dict]:
    if not HF_TOKEN:
        return None
    try:
        from huggingface_hub import InferenceClient

        client = InferenceClient(
            provider=HF_PROVIDER if HF_PROVIDER != "auto" else None,
            api_key=HF_TOKEN,
            timeout=60,
        )
        content: list[dict] = [{"type": "text", "text": prompt}]
        if image_b64:
            content.insert(
                0,
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:image/png;base64,{image_b64}"},
                },
            )
        resp = client.chat.completions.create(
            model=HF_MODEL,
            messages=[{"role": "user", "content": content}],
            max_tokens=600,
            temperature=0.2,
        )
        text = (resp.choices[0].message.content or "").strip()
        m = re.search(r"\{.*\}", text, re.DOTALL)
        if not m:
            return None
        return json.loads(m.group(0))
    except Exception as e:
        print(f"HF API error: {e}")
        return None


def _stub(req: AnalyzeRequest) -> AnalyzeResponse:
    sources: list[SourceItem] = []
    for i, r in enumerate(req.cluster_ranges_m):
        kind = CLUTTER_TAXONOMY[i % len(CLUTTER_TAXONOMY)]
        conf = max(0.55, 0.92 - 0.04 * i - 0.01 * abs(r - 5.0))
        sources.append(SourceItem(type=kind, range_m=float(r), confidence=round(conf, 2)))

    sealed_str = "оба торца запаяны" if req.cylinder_sealed else "один торец открыт"
    quality_str = (
        "удовлетворительной"
        if req.anechoic_quality.startswith("satis")
        else "неудовлетворительной"
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
        + (
            "Метод применим как есть. "
            if req.psr_db >= 12.0
            else "Рекомендуется уточнить ширину селекции по дальности или "
            "включить вторую итерацию подавления. "
        )
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
        model_id="stub-v0",
    )


@app.get("/health")
def health() -> dict[str, str]:
    return {
        "status": "ok",
        "mode": "hf-api" if HF_TOKEN else "stub",
        "model": HF_MODEL if HF_TOKEN else "stub-v0",
        "provider": HF_PROVIDER if HF_TOKEN else "n/a",
    }


@app.post("/analyze", response_model=AnalyzeResponse)
def analyze(req: AnalyzeRequest) -> AnalyzeResponse:
    prompt = _build_prompt(req)
    parsed = _try_hf(prompt, req.image_b64)

    if parsed is not None:
        try:
            sources_raw = parsed.get("sources", []) or []
            sources = [
                SourceItem(
                    type=str(s.get("type", "?")),
                    range_m=float(s.get("range_m", 0.0)),
                    confidence=float(s.get("confidence", 0.5)),
                )
                for s in sources_raw
            ]
            return AnalyzeResponse(
                summary=str(parsed.get("summary", "")),
                sources=sources,
                recommendation=str(parsed.get("recommendation", "")),
                confidence=float(parsed.get("confidence", 0.5)),
                model_id=HF_MODEL,
            )
        except (KeyError, ValueError, TypeError) as e:
            print(f"HF response parse error: {e}; falling back to stub")

    return _stub(req)
