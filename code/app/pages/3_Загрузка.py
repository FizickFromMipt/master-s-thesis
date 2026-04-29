"""Загрузка реальных замеров из БЭК — пополнение датасета."""

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

import streamlit as st

APP_ROOT = Path(__file__).resolve().parents[1]
if str(APP_ROOT) not in sys.path:
    sys.path.insert(0, str(APP_ROOT))

from core.ui import init_page, render_footer  # noqa: E402

init_page("Загрузка", sidebar="collapsed")

UPLOAD_DIR = Path(os.getenv("UPLOAD_DIR", "/app/uploads"))
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

ALLOWED_EXT = {"csv", "txt", "npz", "npy", "mat", "h5", "hdf5", "json", "s2p", "s1p"}
MAX_BYTES = 200 * 1024 * 1024  # 200 МБ

st.title("Загрузка реальных замеров")
st.caption(
    "Файлы с измерениями из БЭК сохраняются в общий volume. "
    "В дальнейшем используются для дообучения VLM-модели."
)

with st.container(border=True):
    st.subheader("Метаданные замера")
    c1, c2 = st.columns(2)
    with c1:
        chamber_label = st.text_input(
            "Камера / стенд",
            placeholder="например, БЭК ПАО Радиофизика",
        )
        anechoic_quality = st.selectbox(
            "Безэховость",
            ["удовлетворительная", "неудовлетворительная"],
            index=1,
        )
        target_kind = st.selectbox(
            "Цель",
            ["цилиндр запаян", "цилиндр с одним открытым торцом", "иное"],
        )
    with c2:
        diameter_cm = st.number_input(
            "Диаметр Ø, см", min_value=0.0, value=20.0, step=0.5
        )
        height_cm = st.number_input(
            "Высота H, см", min_value=0.0, value=40.0, step=0.5
        )
        freq_band = st.text_input(
            "Диапазон частот",
            placeholder="например, 8–12 ГГц (X-band)",
        )

    notes = st.text_area(
        "Комментарии",
        placeholder="Условия съёмки, оснастка, замеченные особенности…",
        height=100,
    )

with st.container(border=True):
    st.subheader("Файлы измерений")
    files = st.file_uploader(
        "Выберите файлы (.csv, .npz, .mat, .s2p, и т.п.)",
        accept_multiple_files=True,
        type=list(ALLOWED_EXT),
    )
    submit = st.button(
        "Сохранить в датасет",
        type="primary",
        disabled=not files,
        use_container_width=False,
    )

if submit and files:
    if not chamber_label.strip():
        st.error("Заполни поле «Камера / стенд» — это обязательно.")
    else:
        ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        run_dir = UPLOAD_DIR / ts
        run_dir.mkdir(parents=True, exist_ok=True)

        saved = []
        too_big = []
        for f in files:
            data = f.getbuffer()
            if len(data) > MAX_BYTES:
                too_big.append(f.name)
                continue
            (run_dir / f.name).write_bytes(data)
            saved.append({"name": f.name, "size_bytes": len(data)})

        meta = {
            "uploaded_at_utc": ts,
            "chamber_label": chamber_label.strip(),
            "anechoic_quality": anechoic_quality,
            "target": {
                "kind": target_kind,
                "diameter_cm": diameter_cm,
                "height_cm": height_cm,
            },
            "freq_band": freq_band.strip() or None,
            "notes": notes.strip() or None,
            "files": saved,
        }
        (run_dir / "meta.json").write_text(
            json.dumps(meta, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

        st.success(f"Сохранено {len(saved)} файл(ов) в `{run_dir}`.")
        if too_big:
            st.warning(
                f"Превысили лимит {MAX_BYTES // (1024 * 1024)} МБ и не сохранены: "
                + ", ".join(too_big)
            )
        st.json(meta)

# ── Уже загруженные замеры ─────────────────────────────────────────
st.subheader("Уже в датасете")
existing = sorted(
    (p for p in UPLOAD_DIR.iterdir() if p.is_dir()),
    reverse=True,
)
if not existing:
    st.caption("Пока ничего не загружено.")
else:
    for run_dir in existing[:30]:
        meta_path = run_dir / "meta.json"
        if not meta_path.exists():
            continue
        try:
            meta = json.loads(meta_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        with st.expander(
            f"{run_dir.name} · {meta.get('chamber_label', '?')} · "
            f"{len(meta.get('files', []))} файл(ов)"
        ):
            st.json(meta)

render_footer()
