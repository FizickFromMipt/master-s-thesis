"""HTTP-клиент для VLM-сервиса (FastAPI-контейнер vlm в docker-compose)."""

from __future__ import annotations

import os
from typing import Any

import requests

VLM_URL = os.getenv("VLM_URL", "http://vlm:8000")
TIMEOUT_S = 60.0  # HF API + LLaVA могут отвечать до 30 сек, плюс запас на cold-start


def analyze(payload: dict[str, Any]) -> dict[str, Any] | None:
    """Возвращает диагностический отчёт от VLM-сервиса либо None при ошибке."""
    try:
        r = requests.post(f"{VLM_URL}/analyze", json=payload, timeout=TIMEOUT_S)
        r.raise_for_status()
        return r.json()
    except requests.RequestException:
        return None


def health() -> bool:
    try:
        r = requests.get(f"{VLM_URL}/health", timeout=2.0)
        return r.status_code == 200
    except requests.RequestException:
        return False
