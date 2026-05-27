"""Task presets, prompt templates, and output parsing.

Pure functions only — no torch/transformers imports — so this module is fully
unit-testable without a GPU. Prompt templates and the 0-1000 normalized box
format come from the LocateAnything-3B model card.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

# Boxes:  <box><x1><y1><x2><y2></box>   Points: <box><x><y></box>
# Coordinates are integers normalized to [0, 1000].
_BOX_RE = re.compile(r"<box><(\d+)><(\d+)><(\d+)><(\d+)></box>")
_POINT_RE = re.compile(r"<box><(\d+)><(\d+)></box>")


@dataclass(frozen=True)
class TaskSpec:
    name: str
    label: str
    output_type: str  # "box" | "point"
    template: str  # uses "{q}" placeholder, or none for input_kind == "none"
    input_kind: str  # "categories" | "phrase" | "none"
    placeholder: str  # UI hint for the prompt field


TASKS: dict[str, TaskSpec] = {
    "detect": TaskSpec(
        name="detect",
        label="Object detection",
        output_type="box",
        template="Locate all the instances that matches the following description: {q}.",
        input_kind="categories",
        placeholder="comma-separated categories, e.g. person, car, dog",
    ),
    "ground_multi": TaskSpec(
        name="ground_multi",
        label="Phrase grounding (all)",
        output_type="box",
        template="Locate all the instances that match the following description: {q}.",
        input_kind="phrase",
        placeholder="e.g. people wearing red shirts",
    ),
    "ground_single": TaskSpec(
        name="ground_single",
        label="Phrase grounding (single)",
        output_type="box",
        template="Locate a single instance that matches the following description: {q}.",
        input_kind="phrase",
        placeholder="e.g. the tallest building",
    ),
    "ground_text": TaskSpec(
        name="ground_text",
        label="Text grounding",
        output_type="box",
        template="Please locate the text referred as {q}.",
        input_kind="phrase",
        placeholder="e.g. the price tag",
    ),
    "detect_text": TaskSpec(
        name="detect_text",
        label="Scene text detection",
        output_type="box",
        template="Detect all the text in box format.",
        input_kind="none",
        placeholder="(no prompt needed — detects all text)",
    ),
    "ground_gui": TaskSpec(
        name="ground_gui",
        label="GUI grounding",
        output_type="box",
        template="Locate the region that matches the following description: {q}.",
        input_kind="phrase",
        placeholder="e.g. the search button",
    ),
    "point": TaskSpec(
        name="point",
        label="Pointing",
        output_type="point",
        template="Point to: {q}.",
        input_kind="phrase",
        placeholder="e.g. the traffic light",
    ),
}

DEFAULT_TASK = "ground_multi"


class UnknownTaskError(ValueError):
    pass


def build_prompt(task: str, query: str) -> str:
    """Build the model prompt for a task from the user's query text."""
    spec = TASKS.get(task)
    if spec is None:
        raise UnknownTaskError(f"Unknown task: {task!r}")

    if spec.input_kind == "none":
        return spec.template

    query = (query or "").strip()
    if spec.input_kind == "categories":
        cats = [c.strip() for c in query.split(",") if c.strip()]
        q = "</c>".join(cats)
    else:
        q = query

    return spec.template.format(q=q)


def _denorm(value: int, size: int) -> float:
    return value / 1000 * size


def parse_boxes(answer: str, image_width: int, image_height: int) -> list[dict]:
    """Parse `<box>` 4-tuples into pixel-coordinate boxes."""
    boxes = []
    for m in _BOX_RE.finditer(answer or ""):
        x1, y1, x2, y2 = (int(g) for g in m.groups())
        boxes.append(
            {
                "x1": _denorm(x1, image_width),
                "y1": _denorm(y1, image_height),
                "x2": _denorm(x2, image_width),
                "y2": _denorm(y2, image_height),
            }
        )
    return boxes


def parse_points(answer: str, image_width: int, image_height: int) -> list[dict]:
    """Parse `<box>` 2-tuples into pixel-coordinate points.

    Runs on text with the 4-tuple boxes stripped first, so a box is never
    mis-read as a point.
    """
    stripped = _BOX_RE.sub("", answer or "")
    points = []
    for m in _POINT_RE.finditer(stripped):
        x, y = int(m.group(1)), int(m.group(2))
        points.append({"x": _denorm(x, image_width), "y": _denorm(y, image_height)})
    return points


def parse_output(task: str, answer: str, image_width: int, image_height: int) -> dict:
    """Parse model output according to the task's output type."""
    spec = TASKS.get(task)
    if spec is None:
        raise UnknownTaskError(f"Unknown task: {task!r}")
    if spec.output_type == "point":
        return {"boxes": [], "points": parse_points(answer, image_width, image_height)}
    return {"boxes": parse_boxes(answer, image_width, image_height), "points": []}
