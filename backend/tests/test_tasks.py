import pytest

from tasks import (
    UnknownTaskError,
    build_prompt,
    parse_boxes,
    parse_output,
    parse_points,
)


def test_build_prompt_detect_joins_categories():
    p = build_prompt("detect", "person, car ,dog")
    expected = (
        "Locate all the instances that matches the following description: " "person</c>car</c>dog."
    )
    assert p == expected


def test_build_prompt_phrase():
    p = build_prompt("ground_multi", "people in red")
    assert p == "Locate all the instances that match the following description: people in red."


def test_build_prompt_detect_text_ignores_query():
    assert build_prompt("detect_text", "whatever") == "Detect all the text in box format."


def test_build_prompt_unknown_task():
    with pytest.raises(UnknownTaskError):
        build_prompt("nope", "x")


def test_parse_boxes_denormalizes():
    boxes = parse_boxes("<box><0><0><500><1000></box>", 200, 100)
    assert boxes == [{"x1": 0.0, "y1": 0.0, "x2": 100.0, "y2": 100.0, "label": None}]


def test_parse_boxes_multiple():
    raw = "<box><100><100><200><200></box> <box><300><300><400><400></box>"
    assert len(parse_boxes(raw, 1000, 1000)) == 2


def test_parse_points_ignores_boxes():
    raw = "<box><100><100><200><200></box> <box><500><500></box>"
    pts = parse_points(raw, 1000, 1000)
    assert pts == [{"x": 500.0, "y": 500.0, "label": None}]


def test_parse_output_routes_by_task():
    box_raw = "<box><100><100><200><200></box>"
    point_raw = "<box><500><500></box>"
    assert parse_output("detect", box_raw, 1000, 1000)["boxes"]
    assert parse_output("detect", box_raw, 1000, 1000)["points"] == []
    assert parse_output("point", point_raw, 1000, 1000)["points"]
    assert parse_output("point", point_raw, 1000, 1000)["boxes"] == []


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
