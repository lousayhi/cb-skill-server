import os
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
os.environ.setdefault("SKILLS_DIR", str(ROOT / "skills"))
os.environ.setdefault("API_KEYS", "test-key")
sys.path.insert(0, str(ROOT))

from fastapi.testclient import TestClient  # noqa: E402
from app.main import app  # noqa: E402


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c
