# Box labels — design

**Date:** 2026-06-02
**Issue:** [#39](https://github.com/gammahazard/locate-anything/issues/39) — "can a label be added to the image detection box?" (reporter: @dongxuecheng / Ethan)
**Branch:** `feat/box-labels`

## Problem

Detection/grounding boxes in the UI currently show only a zero-padded **index**
(`01`, `02`, …). A user asked for the *detected object's label* on each box.

## Key finding

LocateAnything-3B already returns a human-readable label for every box, inside
`<ref>…</ref>` tags emitted immediately before the box(es) they apply to. Our
parser (`backend/tasks.py`) currently discards them — it only regexes the `<box>`
coordinate tuples. Verified empirically against real outputs in the `la-data`
history DB:

- **Multi-category detect** (`box, circle`):
  `<ref>box</ref><box><147><233><455><703></box><ref>circle</ref><box><572><298><880><704></box>`
  — one `<ref>` per category.
- **Phrase grounding** (`/api/health`): one `<ref>/api/health</ref>` followed by
  12 `<box>` tuples that all share that label.
- **Scene-text detect**: the `<ref>` is the recognized OCR text per box
  (e.g. `<ref>d-1</ref>`) — noisy.
- **Point** task: `<ref>phrase</ref>` then point tuples.
- **`<null>`-padded boxes** occur (e.g. `<box><null><null><null><null><null><124>…`)
  and are skipped by the current strict regex.

So per-class labels are recoverable from a **single inference** — no per-category
passes needed.

## Decisions (from brainstorming)

1. **Scope:** parse `<ref>` **uniformly** for all task types (no per-task branching
   in the parser); display the label whenever present. Scene-text will show its
   noisy OCR refs — we eyeball it during testing and decide later whether to tone
   it down. (No special-casing in this change.)
2. **Display:** show the model's **label text**; fall back to the **index number**
   when a box has no clean label.
3. **Long labels:** truncate the tag with an ellipsis; reveal the full text on
   hover/tap via a `title` attribute.

## Design

### 1. Parsing — `backend/tasks.py`

Replace the two independent regexes (`parse_boxes`, `parse_points`) with a single
**ordered scan** that walks `<ref>` and `<box>` tokens left-to-right, tracking the
current label:

- Regex alternation matches, in document order: `<ref>(.*?)</ref>` | a **strict**
  4-int box `<box><d><d><d><d></box>` | a **strict** 2-int point
  `<box><d><d></box>`.
- On `<ref>` → set `current_label = text.strip() or None`.
- On a box (when task `output_type == "box"`) → append a box dict tagged with
  `current_label`.
- On a point (when `output_type == "point"`) → append a point dict tagged with
  `current_label`.
- A box/point with no preceding `<ref>` → `label = None`.
- Because the box/point patterns are strict, `<null>`-padded blocks match none of
  the alternatives and are skipped — **identical to current behavior**.
- Coordinate denormalization (`/1000 * size`) and `output_type` routing are
  unchanged.

The box/point dicts gain a `"label"` key (`str | None`). Existing pure-function
unit tests that assert exact dict equality will be updated to include `label`
(expected; TDD — new tests written first).

### 2. Data shape

- `backend/schemas.py`: add `label: str | None = None` to `Box` and `Point`.
- `frontend/src/api/types.ts`: add `label?: string | null` to `Box` and `Point`.
- **Storage** (`backend/storage.py`): no change. Labels live inside the existing
  `result_json` blob. Old history rows lack the key → deserialize to `undefined`
  → index fallback. Backward compatible; existing history still loads and replays.

### 3. Overlay rendering — `frontend/src/components/BoxOverlay.tsx`

- The existing top-left box tag renders `box.label` when present, else the
  zero-padded index (current behavior preserved as the fallback).
- Apply CSS truncation (max width + ellipsis, `whitespace-nowrap`) and set
  `title={label}` so the full text shows on hover.
- Points get the same label treatment rendered near the crosshair (small addition
  for "label everything" consistency).

### 4. Mock engine — `backend/mock_engine.py`

Emit `<ref>…</ref>` tags in the deterministic fake output (label derived from the
prompt / split categories) so the full feature is exercisable in **mock mode** —
label rendering can be verified in a browser with no GPU and without stopping the
released stack.

### 5. Tests

- **Backend `tests/test_tasks.py`:** multi-`<ref>` detect → distinct labels;
  one-`<ref>`-many-boxes grounding → shared label; box before any `<ref>` →
  `label is None`; `<null>`-padded box skipped; point task labels.
- **Backend `tests/test_api.py`:** `/api/locate` returns boxes with a `label`
  field (mock); `/api/history/{id}` round-trips the label.
- **Frontend `BoxOverlay.test.tsx`:** renders label text when present, index when
  absent; truncation + `title` attribute present.

### 6. Changelog

`CHANGELOG.md` under `[Unreleased] → Added`: detection/grounding boxes now show the
detected object's label (parsed from the model's `<ref>` tags), with the index as a
fallback.

## Out of scope

- Special handling / cleanup of noisy scene-text OCR labels (revisit after seeing
  it render).
- Per-category re-inference (unnecessary — labels come from one pass).
- DB schema migration (not needed).

## Testing / dev notes

- Primary dev loop is **mock mode** (no GPU): unit tests + browser check.
- A final real-model sanity check requires stopping the released GHCR stack (port
  9080 + VRAM collision) or running the source build on another port + `LA_DEVICE=1`.
