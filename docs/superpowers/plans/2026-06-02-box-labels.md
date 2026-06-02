# Box Labels Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Display the model-provided label (`<ref>…</ref>`) on each detection/grounding box and point, with the index number as a fallback.

**Architecture:** The model already emits a `<ref>label</ref>` tag before the box(es) it applies to. Replace the parser's two independent regexes with one ordered token scan that tracks the current label and tags each box/point with it. Surface the label through the API (`label` field on `Box`/`Point`), store it inside the existing `result_json` blob (no DB change), and render it in the overlay with truncation + hover.

**Tech Stack:** Python (FastAPI, Pydantic, `re`, pytest), TypeScript (React, Vitest, Tailwind).

**Spec:** `docs/superpowers/specs/2026-06-02-box-labels-design.md`
**Branch:** `feat/box-labels` (already created)

---

### Task 1: Label-aware parser

**Files:**
- Modify: `backend/tasks.py` (regexes near lines 13–16; `parse_boxes`/`parse_points`/`parse_output` near lines 127–168)
- Test: `backend/tests/test_tasks.py`

- [ ] **Step 1: Write/adjust the tests**

In `backend/tests/test_tasks.py`, **update** the two existing dict-equality tests to expect a `label` key:

```python
def test_parse_boxes_denormalizes():
    boxes = parse_boxes("<box><0><0><500><1000></box>", 200, 100)
    assert boxes == [{"x1": 0.0, "y1": 0.0, "x2": 100.0, "y2": 100.0, "label": None}]


def test_parse_points_ignores_boxes():
    raw = "<box><100><100><200><200></box> <box><500><500></box>"
    pts = parse_points(raw, 1000, 1000)
    assert pts == [{"x": 500.0, "y": 500.0, "label": None}]
```

Then **append** these new tests to the file:

```python
def test_parse_boxes_attaches_ref_labels():
    raw = (
        "<ref>box</ref><box><0><0><500><1000></box>"
        "<ref>circle</ref><box><500><0><1000><1000></box>"
    )
    boxes = parse_boxes(raw, 1000, 1000)
    assert [b["label"] for b in boxes] == ["box", "circle"]


def test_parse_boxes_shares_one_ref_across_boxes():
    raw = "<ref>/api/health</ref><box><0><0><10><10></box><box><20><20><30><30></box>"
    boxes = parse_boxes(raw, 1000, 1000)
    assert len(boxes) == 2
    assert all(b["label"] == "/api/health" for b in boxes)


def test_parse_boxes_label_none_without_ref():
    boxes = parse_boxes("<box><0><0><10><10></box>", 1000, 1000)
    assert boxes[0]["label"] is None


def test_parse_skips_null_padded_box():
    raw = "<ref>x</ref><box><null><null><null><null><null><124><753><188><645></box>"
    assert parse_boxes(raw, 1000, 1000) == []


def test_parse_points_attaches_label():
    pts = parse_points("<ref>traffic light</ref><box><100><200></box>", 1000, 1000)
    assert pts == [{"x": 100.0, "y": 200.0, "label": "traffic light"}]


def test_parse_output_point_task_keeps_labels():
    out = parse_output("point", "<ref>cat</ref><box><500><500></box>", 1000, 1000)
    assert out["boxes"] == []
    assert out["points"][0]["label"] == "cat"
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `cd backend && LA_MOCK=1 python -m pytest tests/test_tasks.py -q`
Expected: FAIL — the new label keys are absent (e.g. `KeyError: 'label'` / assertion mismatches).

- [ ] **Step 3: Rewrite the parser**

In `backend/tasks.py`, **replace** the two regexes (lines ~13–16):

```python
# Boxes:  <box><x1><y1><x2><y2></box>   Points: <box><x><y></box>
# Labels: <ref>text</ref> precedes the box(es) it applies to.
# Coordinates are integers normalized to [0, 1000].
_BOX_RE = re.compile(r"<box><(\d+)><(\d+)><(\d+)><(\d+)></box>")
_POINT_RE = re.compile(r"<box><(\d+)><(\d+)></box>")
```

with:

```python
# Boxes:  <box><x1><y1><x2><y2></box>   Points: <box><x><y></box>
# Labels: <ref>text</ref> precedes the box(es)/point(s) it applies to.
# Coordinates are integers normalized to [0, 1000]. <null>-padded boxes the
# model emits match none of the strict patterns below and are skipped.
_TOKEN_RE = re.compile(
    r"<ref>(.*?)</ref>"  # 1: label text
    r"|<box><(\d+)><(\d+)><(\d+)><(\d+)></box>"  # 2-5: box (strict 4-int)
    r"|<box><(\d+)><(\d+)></box>"  # 6-7: point (strict 2-int)
)
```

Then **replace** the three functions `parse_boxes`, `parse_points`, `parse_output`
(lines ~131–168) with:

```python
def _scan(answer: str, image_width: int, image_height: int) -> tuple[list[dict], list[dict]]:
    """Ordered scan of model output → (boxes, points).

    Walks `<ref>`, box, and point tokens left-to-right, tagging each box/point
    with the most recent preceding `<ref>` label (None if there was none). A box
    matched before a 4-int box pattern can't also be read as a 2-int point, so
    boxes are never mis-read as points.
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
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `cd backend && LA_MOCK=1 python -m pytest tests/test_tasks.py -q`
Expected: PASS (all task tests, old and new).

- [ ] **Step 5: Lint and commit**

```bash
cd backend && ruff check tasks.py tests/test_tasks.py && black tasks.py tests/test_tasks.py
git add backend/tasks.py backend/tests/test_tasks.py
git commit -m "feat(backend): parse <ref> labels and attach them to boxes/points"
```

---

### Task 2: Add `label` to the API models

**Files:**
- Modify: `backend/schemas.py` (`Box` lines ~8–12, `Point` lines ~15–17)

- [ ] **Step 1: Add the fields**

In `backend/schemas.py`, update `Box` and `Point`:

```python
class Box(BaseModel):
    x1: float
    y1: float
    x2: float
    y2: float
    label: str | None = None


class Point(BaseModel):
    x: float
    y: float
    label: str | None = None
```

- [ ] **Step 2: Verify the API serializes labels**

Run: `cd backend && LA_MOCK=1 python -m pytest tests/test_api.py -q`
Expected: PASS (existing API tests still green; the new field is optional and present in responses).

- [ ] **Step 3: Commit**

```bash
git add backend/schemas.py
git commit -m "feat(backend): add optional label field to Box and Point schemas"
```

---

### Task 3: Mock engine emits `<ref>` labels

**Files:**
- Modify: `backend/mock_engine.py` (`predict` lines ~19–46)

- [ ] **Step 1: Add `<ref>` tags to the fake output**

In `backend/mock_engine.py`, replace the body of `predict` with:

```python
    def predict(
        self,
        image,  # noqa: ANN001 - PIL image, unused in mock
        prompt: str,
        generation_mode: str,
        output_type: str = "box",
    ) -> dict:
        seed = _seed(prompt)
        count = 1 + seed % 3
        parts: list[str] = []

        if output_type == "point":
            for i in range(count):
                x = 100 + (seed >> (i * 5)) % 800
                y = 100 + (seed >> (i * 7)) % 800
                parts.append(f"<ref>mock {i + 1}</ref><box><{x}><{y}></box>")
        else:
            for i in range(count):
                x1 = 40 + (seed >> (i * 4)) % 400
                y1 = 40 + (seed >> (i * 6)) % 400
                x2 = min(x1 + 150 + (seed >> (i * 8)) % 350, 1000)
                y2 = min(y1 + 150 + (seed >> (i * 9)) % 350, 1000)
                parts.append(f"<ref>mock {i + 1}</ref><box><{x1}><{y1}><{x2}><{y2}></box>")

        return {
            "raw": " ".join(parts),
            "stats": {"mode": generation_mode, "mock": True},
        }
```

- [ ] **Step 2: Verify parsing still produces boxes/points (now labeled)**

Run: `cd backend && LA_MOCK=1 python -m pytest -q`
Expected: PASS (full suite; existing `test_locate_*` still produce boxes/points).

- [ ] **Step 3: Lint and commit**

```bash
cd backend && ruff check mock_engine.py && black mock_engine.py
git add backend/mock_engine.py
git commit -m "feat(backend): emit <ref> labels from the mock engine"
```

---

### Task 4: API + history label tests

**Files:**
- Test: `backend/tests/test_api.py`

- [ ] **Step 1: Write the failing tests**

Append to `backend/tests/test_api.py`:

```python
def test_locate_returns_labels(client, png_bytes):
    body = _locate(client, png_bytes).json()
    assert body["boxes"]
    assert all(b.get("label") for b in body["boxes"])


def test_history_round_trips_labels(client, png_bytes):
    sid = _locate(client, png_bytes).json()["id"]
    item = client.get(f"/api/history/{sid}").json()
    assert all(b.get("label") for b in item["boxes"])
```

- [ ] **Step 2: Run the tests**

Run: `cd backend && LA_MOCK=1 python -m pytest tests/test_api.py -q`
Expected: PASS (mock now emits labels; the API surfaces and round-trips them).

> Note: these pass immediately because Tasks 1–3 already wired the behavior end
> to end. They lock the API contract in place so a regression is caught.

- [ ] **Step 3: Commit**

```bash
git add backend/tests/test_api.py
git commit -m "test(backend): assert locate + history expose box labels"
```

---

### Task 5: Frontend types

**Files:**
- Modify: `frontend/src/api/types.ts` (`Box` lines ~3–8, `Point` lines ~10–13)

- [ ] **Step 1: Add the optional label field**

In `frontend/src/api/types.ts`:

```typescript
export interface Box {
  x1: number;
  y1: number;
  x2: number;
  y2: number;
  label?: string | null;
}

export interface Point {
  x: number;
  y: number;
  label?: string | null;
}
```

- [ ] **Step 2: Typecheck**

Run: `cd frontend && npm run typecheck`
Expected: PASS (no type errors).

- [ ] **Step 3: Commit**

```bash
git add frontend/src/api/types.ts
git commit -m "feat(frontend): add optional label to Box and Point types"
```

---

### Task 6: Render labels in the overlay

**Files:**
- Modify: `frontend/src/components/BoxOverlay.tsx` (label block lines ~75–87)
- Test: `frontend/src/components/BoxOverlay.test.tsx`

- [ ] **Step 1: Write the failing tests**

Append to `frontend/src/components/BoxOverlay.test.tsx` (inside the `describe`):

```typescript
  it("renders the ref label when present, index as fallback", () => {
    render(
      <BoxOverlay
        width={100}
        height={100}
        boxes={[
          { x1: 0, y1: 0, x2: 10, y2: 10, label: "person" },
          { x1: 20, y1: 20, x2: 30, y2: 30 },
        ]}
        points={[]}
      />,
    );
    expect(screen.getByText("person")).toBeInTheDocument();
    expect(screen.getByText("02")).toBeInTheDocument();
  });

  it("sets a title attribute carrying the full label text", () => {
    render(
      <BoxOverlay
        width={100}
        height={100}
        boxes={[{ x1: 0, y1: 0, x2: 10, y2: 10, label: "people wearing red shirts" }]}
        points={[]}
      />,
    );
    expect(screen.getByText("people wearing red shirts")).toHaveAttribute(
      "title",
      "people wearing red shirts",
    );
  });

  it("labels a point with its ref text", () => {
    render(
      <BoxOverlay width={100} height={100} boxes={[]} points={[{ x: 50, y: 50, label: "cat" }]} />,
    );
    expect(screen.getByText("cat")).toBeInTheDocument();
  });
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `cd frontend && npm test -- --run src/components/BoxOverlay.test.tsx`
Expected: FAIL — `person`, the `title` attribute, and the point label aren't rendered yet (current code shows only the index number on boxes and no label on points).

- [ ] **Step 3: Implement the rendering**

In `frontend/src/components/BoxOverlay.tsx`, **replace** the existing labels block
(the `{showLabels && boxes.map(...)}` span block near lines 75–87) with:

```tsx
      {showLabels &&
        boxes.map((b, i) => {
          const text = b.label ?? String(i + 1).padStart(2, "0");
          return (
            <span
              key={`l${i}`}
              title={text}
              className="absolute -translate-y-full max-w-[45%] truncate bg-lime px-1.5 py-0.5 font-mono text-[10px] font-semibold leading-none text-ink"
              style={{
                left: `${(Math.min(b.x1, b.x2) / width) * 100}%`,
                top: `${(Math.min(b.y1, b.y2) / height) * 100}%`,
              }}
            >
              {text}
            </span>
          );
        })}

      {showLabels &&
        points.map((p, i) =>
          p.label ? (
            <span
              key={`pl${i}`}
              title={p.label}
              className="absolute max-w-[45%] -translate-y-1/2 translate-x-3 truncate bg-amber px-1.5 py-0.5 font-mono text-[10px] font-semibold leading-none text-ink"
              style={{ left: `${(p.x / width) * 100}%`, top: `${(p.y / height) * 100}%` }}
            >
              {p.label}
            </span>
          ) : null,
        )}
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `cd frontend && npm test -- --run src/components/BoxOverlay.test.tsx`
Expected: PASS (including the existing "renders index labels when enabled" test, since a label-less box still falls back to `01`).

- [ ] **Step 5: Lint and commit**

```bash
cd frontend && npm run lint
git add frontend/src/components/BoxOverlay.tsx frontend/src/components/BoxOverlay.test.tsx
git commit -m "feat(frontend): show box/point labels in the overlay with index fallback"
```

---

### Task 7: Changelog + full verification

**Files:**
- Modify: `CHANGELOG.md` (`[Unreleased]` section)

- [ ] **Step 1: Add the changelog entry**

In `CHANGELOG.md`, under `## [Unreleased]` and **above** the existing
`### Documentation` heading, insert:

```markdown
### Added
- Detection and grounding boxes (and points) now display the detected object's label, parsed from the model's `<ref>` tags. The label falls back to the box index when the model returns none, and long labels are truncated with the full text shown on hover.

```

- [ ] **Step 2: Run the full backend suite + lint**

Run:
```bash
cd backend && LA_MOCK=1 python -m pytest -q && ruff check . && black --check .
```
Expected: PASS — all tests pass, no lint/format errors.

- [ ] **Step 3: Run the full frontend suite + build**

Run:
```bash
cd frontend && npm run lint && npm run typecheck && npm test -- --run && npm run build
```
Expected: PASS — lint clean, types clean, all tests pass, build succeeds.

- [ ] **Step 4: Commit**

```bash
git add CHANGELOG.md
git commit -m "docs: changelog entry for box labels"
```

- [ ] **Step 5 (optional): Real-model sanity check**

Stop the released GHCR stack (frees port 9080 + VRAM), then run the source build
and confirm labels render on a real multi-category detection:

```bash
# In Docker Desktop, stop the running locate-anything containers first, then:
docker compose -f docker-compose.yml up --build
# open http://localhost:9080 → detect "person, car" on a photo → boxes show labels
```

---

## Self-Review

- **Spec coverage:**
  - Parsing `<ref>` uniformly, ordered scan, label fallback, `<null>` skip → Task 1. ✓
  - `label` on `Box`/`Point` schema + types → Tasks 2, 5. ✓
  - No DB change (label rides in `result_json`) → confirmed; history round-trip tested in Task 4. ✓
  - Overlay rendering: label text, index fallback, truncation + `title`, points → Task 6. ✓
  - Mock engine emits `<ref>` for GPU-free testing → Task 3. ✓
  - Tests (backend parse + API/history, frontend overlay) → Tasks 1, 4, 6. ✓
  - Changelog → Task 7. ✓
  - Scene-text deferral (no special-casing) → honored; parser is uniform. ✓
- **Placeholder scan:** none — every code step has complete code.
- **Type consistency:** `parse_output`/`parse_boxes`/`parse_points` signatures unchanged; `_scan` returns `(boxes, points)`; `label` is `str | None` (Python) / `string | null` (TS); `b.label ?? index` handles both null and undefined.
