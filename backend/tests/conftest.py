import io
import os
import sys
import tempfile
from pathlib import Path

# Make backend modules importable when running pytest from the repo without install.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

# Force mock mode + an isolated data dir BEFORE any app import (settings are cached).
os.environ["LA_MOCK"] = "1"
os.environ.setdefault("LA_DATA_DIR", tempfile.mkdtemp(prefix="la-test-"))

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from PIL import Image  # noqa: E402

from app import app  # noqa: E402


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture
def png_bytes():
    buf = io.BytesIO()
    Image.new("RGB", (640, 480), (123, 123, 123)).save(buf, format="PNG")
    return buf.getvalue()
