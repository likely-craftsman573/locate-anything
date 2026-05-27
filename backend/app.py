"""FastAPI application for the LocateAnything-3B web UI."""

from __future__ import annotations

import io
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from PIL import Image

from config import VALID_MODES, get_settings
from schemas import (
    HealthResponse,
    HistoryItem,
    HistoryList,
    LocateResponse,
    TaskInfo,
)
from storage import Store
from tasks import DEFAULT_TASK, TASKS, build_prompt, parse_output

_EXT_BY_TYPE = {"image/jpeg": ".jpg", "image/png": ".png", "image/webp": ".webp"}


@asynccontextmanager
async def lifespan(app: FastAPI):
    from worker import create_engine

    settings = get_settings()
    app.state.settings = settings
    app.state.store = Store(settings.data_dir)
    app.state.engine = create_engine(settings)
    yield


app = FastAPI(title="LocateAnything UI", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


def _image_url(search_id: str) -> str:
    return f"/api/images/{search_id}"


def _to_history_item(row: dict) -> HistoryItem:
    result = row["result"]
    return HistoryItem(
        id=row["id"],
        task=row["task"],
        prompt=row["prompt"],
        generation_mode=row["generation_mode"],
        image_url=_image_url(row["id"]),
        box_count=len(result.get("boxes", [])),
        point_count=len(result.get("points", [])),
        created_at=row["created_at"],
    )


@app.get("/api/health", response_model=HealthResponse)
def health() -> HealthResponse:
    settings = app.state.settings
    info = app.state.engine.info()
    return HealthResponse(
        status="ok",
        mock=settings.mock,
        model_loaded=info.get("model_loaded", False),
        model_path=settings.model_path,
        device=info.get("device"),
        gpu_name=info.get("gpu_name"),
        vram_gb=info.get("vram_gb"),
        compatible=info.get("compatible"),
        note=info.get("note"),
    )


@app.get("/api/tasks", response_model=list[TaskInfo])
def list_tasks() -> list[TaskInfo]:
    return [
        TaskInfo(
            name=s.name,
            label=s.label,
            output_type=s.output_type,
            input_kind=s.input_kind,
            placeholder=s.placeholder,
        )
        for s in TASKS.values()
    ]


@app.post("/api/locate", response_model=LocateResponse)
async def locate(
    image: UploadFile = File(...),
    task: str = Form(DEFAULT_TASK),
    prompt: str = Form(""),
    generation_mode: str = Form(""),
) -> LocateResponse:
    spec = TASKS.get(task)
    if spec is None:
        raise HTTPException(status_code=400, detail=f"Unknown task: {task!r}")

    mode = (generation_mode or app.state.settings.default_mode).strip().lower()
    if mode not in VALID_MODES:
        raise HTTPException(status_code=400, detail=f"Invalid generation_mode: {mode!r}")

    if spec.input_kind != "none" and not prompt.strip():
        raise HTTPException(status_code=400, detail="A prompt is required for this task.")

    data = await image.read()
    try:
        pil = Image.open(io.BytesIO(data)).convert("RGB")
    except Exception:
        raise HTTPException(status_code=400, detail="Could not read image file.") from None
    width, height = pil.size

    full_prompt = build_prompt(task, prompt)

    started = time.perf_counter()
    out = app.state.engine.predict(pil, full_prompt, mode, output_type=spec.output_type)
    timing_ms = (time.perf_counter() - started) * 1000

    raw = out.get("raw", "")
    parsed = parse_output(task, raw, width, height)
    parsed["raw"] = raw

    store: Store = app.state.store
    search_id = store.new_id()
    suffix = _EXT_BY_TYPE.get(image.content_type or "", ".jpg")
    img_path = store.image_path_for(search_id, suffix)
    img_path.write_bytes(data)

    store.save(
        search_id=search_id,
        task=task,
        prompt=prompt,
        generation_mode=mode,
        image_path=img_path,
        image_width=width,
        image_height=height,
        result=parsed,
        stats=out.get("stats"),
        timing_ms=timing_ms,
    )

    return LocateResponse(
        id=search_id,
        task=task,
        prompt=prompt,
        generation_mode=mode,
        image_width=width,
        image_height=height,
        image_url=_image_url(search_id),
        boxes=parsed["boxes"],
        points=parsed["points"],
        raw=raw,
        stats=out.get("stats"),
        timing_ms=round(timing_ms, 1),
        created_at=store.get(search_id)["created_at"],
    )


@app.get("/api/history", response_model=HistoryList)
def history(limit: int = 50, offset: int = 0) -> HistoryList:
    limit = max(1, min(limit, 200))
    offset = max(0, offset)
    rows, total = app.state.store.list(limit=limit, offset=offset)
    return HistoryList(
        items=[_to_history_item(r) for r in rows],
        total=total,
        limit=limit,
        offset=offset,
    )


@app.get("/api/history/{search_id}", response_model=LocateResponse)
def history_item(search_id: str) -> LocateResponse:
    row = app.state.store.get(search_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Not found")
    result = row["result"]
    return LocateResponse(
        id=row["id"],
        task=row["task"],
        prompt=row["prompt"],
        generation_mode=row["generation_mode"],
        image_width=row["image_width"],
        image_height=row["image_height"],
        image_url=_image_url(row["id"]),
        boxes=result.get("boxes", []),
        points=result.get("points", []),
        raw=result.get("raw", ""),
        stats=row["stats"],
        timing_ms=round(row["timing_ms"], 1),
        created_at=row["created_at"],
    )


@app.delete("/api/history/{search_id}")
def delete_history(search_id: str) -> dict:
    if not app.state.store.delete(search_id):
        raise HTTPException(status_code=404, detail="Not found")
    return {"deleted": search_id}


@app.get("/api/images/{search_id}")
def get_image(search_id: str):
    row = app.state.store.get(search_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Not found")
    return FileResponse(row["image_path"])
