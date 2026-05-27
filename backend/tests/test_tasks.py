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
    assert boxes == [{"x1": 0.0, "y1": 0.0, "x2": 100.0, "y2": 100.0}]


def test_parse_boxes_multiple():
    raw = "<box><100><100><200><200></box> <box><300><300><400><400></box>"
    assert len(parse_boxes(raw, 1000, 1000)) == 2


def test_parse_points_ignores_boxes():
    raw = "<box><100><100><200><200></box> <box><500><500></box>"
    pts = parse_points(raw, 1000, 1000)
    assert pts == [{"x": 500.0, "y": 500.0}]


def test_parse_output_routes_by_task():
    box_raw = "<box><100><100><200><200></box>"
    point_raw = "<box><500><500></box>"
    assert parse_output("detect", box_raw, 1000, 1000)["boxes"]
    assert parse_output("detect", box_raw, 1000, 1000)["points"] == []
    assert parse_output("point", point_raw, 1000, 1000)["points"]
    assert parse_output("point", point_raw, 1000, 1000)["boxes"] == []
