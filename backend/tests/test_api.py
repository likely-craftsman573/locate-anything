def _locate(client, png_bytes, **form):
    form.setdefault("task", "ground_multi")
    form.setdefault("prompt", "a cat")
    return client.post(
        "/api/locate",
        data=form,
        files={"image": ("t.png", png_bytes, "image/png")},
    )


def test_health_reports_mock(client):
    r = client.get("/api/health")
    assert r.status_code == 200
    body = r.json()
    assert body["mock"] is True
    assert body["model_loaded"] is False


def test_tasks_list(client):
    r = client.get("/api/tasks")
    assert r.status_code == 200
    names = {t["name"] for t in r.json()}
    assert {"detect", "ground_multi", "point", "detect_text"} <= names


def test_locate_returns_boxes_and_persists(client, png_bytes):
    r = _locate(client, png_bytes, generation_mode="fast")
    assert r.status_code == 200
    body = r.json()
    assert body["boxes"] and not body["points"]
    assert body["image_width"] == 640 and body["image_height"] == 480
    # boxes are within the image bounds
    for b in body["boxes"]:
        assert 0 <= b["x1"] <= b["x2"] <= 640
        assert 0 <= b["y1"] <= b["y2"] <= 480

    sid = body["id"]
    assert client.get(f"/api/history/{sid}").status_code == 200
    assert client.get(body["image_url"]).status_code == 200

    hist = client.get("/api/history").json()
    assert any(item["id"] == sid for item in hist["items"])


def test_locate_point_task_returns_points(client, png_bytes):
    r = _locate(client, png_bytes, task="point", prompt="the cat")
    assert r.status_code == 200
    body = r.json()
    assert body["points"] and not body["boxes"]


def test_locate_requires_prompt_for_phrase_task(client, png_bytes):
    r = _locate(client, png_bytes, task="ground_multi", prompt="   ")
    assert r.status_code == 400


def test_locate_rejects_bad_mode(client, png_bytes):
    r = _locate(client, png_bytes, generation_mode="turbo")
    assert r.status_code == 400


def test_devices_empty_in_mock(client):
    r = client.get("/api/devices")
    assert r.status_code == 200
    body = r.json()
    assert body["current"] is None
    assert body["devices"] == []


def test_switch_device_rejected_in_mock(client):
    r = client.post("/api/device", json={"index": 0})
    assert r.status_code == 400


def test_delete_history(client, png_bytes):
    sid = _locate(client, png_bytes).json()["id"]
    assert client.delete(f"/api/history/{sid}").status_code == 200
    assert client.get(f"/api/history/{sid}").status_code == 404
    assert client.delete(f"/api/history/{sid}").status_code == 404


def test_locate_returns_labels(client, png_bytes):
    body = _locate(client, png_bytes).json()
    assert body["boxes"]
    assert all(b.get("label") for b in body["boxes"])


def test_history_round_trips_labels(client, png_bytes):
    sid = _locate(client, png_bytes).json()["id"]
    item = client.get(f"/api/history/{sid}").json()
    assert all(b.get("label") for b in item["boxes"])
