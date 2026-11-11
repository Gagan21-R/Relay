import os
import tempfile

# Tests always run in mock mode on a throwaway SQLite file, never against a developer database.
_tmp = tempfile.mkdtemp(prefix="relay-test-")
os.environ["DATABASE_URL"] = f"sqlite:///{_tmp}/test.db"
os.environ["RELAY_MOCK_MODE"] = "true"
os.environ["GEMINI_API_KEY"] = ""

import warnings  # noqa: E402

with warnings.catch_warnings():   # a third-party import-time notice (langgraph), not ours
    warnings.simplefilter("ignore")
    import langgraph.checkpoint.base  # noqa: E402,F401
    import langgraph.graph  # noqa: E402,F401

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402


@pytest.fixture(scope="session")
def client():
    with TestClient(app) as c:
        yield c
