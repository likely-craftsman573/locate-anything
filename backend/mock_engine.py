"""Mock inference engine — deterministic fake output, no GPU/model needed.

Active when LA_MOCK=1. Lets the frontend, tests, and CI exercise the full
request/response path without downloading the 6GB model or owning a GPU.
"""

from __future__ import annotations

import hashlib


def _seed(prompt: str) -> int:
    return int(hashlib.sha256(prompt.encode("utf-8")).hexdigest(), 16)


class MockEngine:
    model_loaded = False

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
                parts.append(f"<box><{x}><{y}></box>")
        else:
            for i in range(count):
                x1 = 40 + (seed >> (i * 4)) % 400
                y1 = 40 + (seed >> (i * 6)) % 400
                x2 = min(x1 + 150 + (seed >> (i * 8)) % 350, 1000)
                y2 = min(y1 + 150 + (seed >> (i * 9)) % 350, 1000)
                parts.append(f"<box><{x1}><{y1}><{x2}><{y2}></box>")

        return {
            "raw": " ".join(parts),
            "stats": {"mode": generation_mode, "mock": True},
        }

    def info(self) -> dict:
        return {
            "model_loaded": False,
            "device": "cpu",
            "gpu_name": None,
            "vram_gb": None,
            "compatible": True,
            "device_index": None,
            "note": "Mock mode — deterministic fake boxes, no model loaded.",
        }

    def list_devices(self) -> dict:
        return {"current": None, "devices": []}

    def switch_device(self, index: int) -> dict:  # noqa: ARG002
        raise RuntimeError("GPU switching is not available in mock mode.")
