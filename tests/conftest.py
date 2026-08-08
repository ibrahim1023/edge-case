import os
import tempfile

import pytest

from edgecase.state import store


@pytest.fixture(autouse=True)
def fresh_store():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        path = f.name
    store.configure(path, ttl_seconds=3600)
    try:
        yield
    finally:
        store.clear()
        os.unlink(path)
