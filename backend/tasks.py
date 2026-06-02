"""Task presets, prompt templates, and output parsing.

Pure functions only — no torch/transformers imports — so this module is fully
unit-testable without a GPU. Prompt templates and the 0-1000 normalized box
format come from the LocateAnything-3B model card.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

# Boxes:  <box><x1><y1><x2><y2></box>   Points: <box><x><y></box>
# Labels: <ref>text</ref> precedes the box(es)/point(s) it applies to.
# Coordinates are integers normalized to [0, 1000]. <null>-padded boxes the
# model emits match none of the strict patterns below and are skipped.
_TOKEN_RE = re.compile(
    r"<ref>(.*?)</ref>"  # 1: label text
    r"|<box><(\d+)><(\d+)><(\d+)><(\d+)></box>"  # 2-5: box (strict 4-int)
    r"|<box><(\d+)><(\d+)></box>"  # 6-7: point (strict 2-int)
)


@dataclass(frozen=True)
class TaskSpec:
    name: str
    label: str
    output_type: str  # "box" | "point"
    template: str  # uses "{q}" placeholder, or none for input_kind == "none"
    input_kind: str  # "categories" | "phrase" | "none"
    placeholder: str  # UI hint for the prompt field
    description: str  # short explanation of what the task does (for tooltips)


TASKS: dict[str, TaskSpec] = {
    "detect": TaskSpec(
        name="detect",
        label="Object detection",
        output_type="box",
        template="Locate all the instances that matches the following description: {q}.",
        input_kind="categories",
        placeholder="comma-separated categories, e.g. person, car, dog",
        description="Find every instance of the categories you list. Give one or more "
        "comma-separated class names.",
    ),
    "ground_multi": TaskSpec(
        name="ground_multi",
        label="Phrase grounding (all)",
        output_type="box",
        template="Locate all the instances that match the following description: {q}.",
        input_kind="phrase",
        placeholder="e.g. people wearing red shirts",
        description="Find every region matching a free-form description, e.g. "
        '"people wearing red shirts".',
    ),
    "ground_single": TaskSpec(
        name="ground_single",
        label="Phrase grounding (single)",
        output_type="box",
        template="Locate a single instance that matches the following description: {q}.",
        input_kind="phrase",
        placeholder="e.g. the tallest building",
        description="Find the single best region matching a description — use when you "
        "expect exactly one match.",
    ),
    "ground_text": TaskSpec(
        name="ground_text",
        label="Text grounding",
        output_type="box",
        template="Please locate the text referred as {q}.",
        input_kind="phrase",
        placeholder="e.g. the price tag",
        description="Locate a specific piece of text you describe, e.g. a price tag or a "
        "heading.",
    ),
    "detect_text": TaskSpec(
        name="detect_text",
        label="Scene text detection",
        output_type="box",
        template="Detect all the text in box format.",
        input_kind="none",
        placeholder="(no prompt needed — detects all text)",
        description="Detect all text regions in the image (OCR-style boxes). No prompt " "needed.",
    ),
    "ground_gui": TaskSpec(
        name="ground_gui",
        label="GUI grounding",
        output_type="box",
        template="Locate the region that matches the following description: {q}.",
        input_kind="phrase",
        placeholder="e.g. the search button",
        description="Locate a UI element by description — buttons, fields, icons in app or "
        "web screenshots.",
    ),
    "point": TaskSpec(
        name="point",
        label="Pointing",
        output_type="point",
        template="Point to: {q}.",
        input_kind="phrase",
        placeholder="e.g. the traffic light",
        description="Return a point (crosshair) at the thing you describe, instead of a " "box.",
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


def _scan(answer: str, image_width: int, image_height: int) -> tuple[list[dict], list[dict]]:
    """Ordered scan of model output → (boxes, points).

    Walks `<ref>`, box, and point tokens left-to-right, tagging each box/point
    with the most recent preceding `<ref>` label (None if there was none). The
    4-int box pattern is tried before the 2-int point pattern, so a box is never
    mis-read as a point.
    """
    boxes: list[dict] = []
    points: list[dict] = []
    label: str | None = None
    for m in _TOKEN_RE.finditer(answer or ""):
        if m.group(1) is not None:
            label = m.group(1).strip() or None
        elif m.group(2) is not None:
            x1, y1, x2, y2 = (int(m.group(i)) for i in (2, 3, 4, 5))
            boxes.append(
                {
                    "x1": _denorm(x1, image_width),
                    "y1": _denorm(y1, image_height),
                    "x2": _denorm(x2, image_width),
                    "y2": _denorm(y2, image_height),
                    "label": label,
                }
            )
        else:
            x, y = int(m.group(6)), int(m.group(7))
            points.append(
                {"x": _denorm(x, image_width), "y": _denorm(y, image_height), "label": label}
            )
    return boxes, points


def parse_boxes(answer: str, image_width: int, image_height: int) -> list[dict]:
    """Parse `<box>` 4-tuples into pixel-coordinate boxes, each with its `<ref>` label."""
    return _scan(answer, image_width, image_height)[0]


def parse_points(answer: str, image_width: int, image_height: int) -> list[dict]:
    """Parse `<box>` 2-tuples into pixel-coordinate points, each with its `<ref>` label."""
    return _scan(answer, image_width, image_height)[1]


def parse_output(task: str, answer: str, image_width: int, image_height: int) -> dict:
    """Parse model output according to the task's output type."""
    spec = TASKS.get(task)
    if spec is None:
        raise UnknownTaskError(f"Unknown task: {task!r}")
    boxes, points = _scan(answer, image_width, image_height)
    if spec.output_type == "point":
        return {"boxes": [], "points": points}
    return {"boxes": boxes, "points": []}
