"""Pydantic response models for the API."""

from __future__ import annotations

from pydantic import BaseModel


class Box(BaseModel):
    x1: float
    y1: float
    x2: float
    y2: float


class Point(BaseModel):
    x: float
    y: float


class TaskInfo(BaseModel):
    name: str
    label: str
    output_type: str
    input_kind: str
    placeholder: str


class HealthResponse(BaseModel):
    status: str
    mock: bool
    model_loaded: bool
    model_path: str
    device: str | None = None
    device_index: int | None = None
    gpu_name: str | None = None
    vram_gb: float | None = None
    compatible: bool | None = None
    note: str | None = None


class DeviceInfo(BaseModel):
    index: int
    name: str
    vram_gb: float | None = None
    vram_free_gb: float | None = None
    compatible: bool


class DevicesResponse(BaseModel):
    current: int | None = None
    devices: list[DeviceInfo]


class DeviceRequest(BaseModel):
    index: int


class LocateResponse(BaseModel):
    id: str
    task: str
    prompt: str
    generation_mode: str
    image_width: int
    image_height: int
    image_url: str
    boxes: list[Box]
    points: list[Point]
    raw: str
    stats: dict | None = None
    timing_ms: float
    created_at: str


class HistoryItem(BaseModel):
    id: str
    task: str
    prompt: str
    generation_mode: str
    image_url: str
    box_count: int
    point_count: int
    created_at: str


class HistoryList(BaseModel):
    items: list[HistoryItem]
    total: int
    limit: int
    offset: int
