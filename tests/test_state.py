import os
import tempfile
import time
from uuid import uuid4

from edgecase.state import SessionStore


def _temp_store(ttl_seconds: int = 60) -> tuple[SessionStore, str]:
    path = tempfile.mktemp(suffix=".db")
    return SessionStore(path, ttl_seconds=ttl_seconds), path


def test_store_create_and_get():
    store, path = _temp_store(60)
    try:
        session = store.create()
        assert session == store.get(session.id)
    finally:
        os.unlink(path)


def test_store_get_missing():
    store, path = _temp_store(60)
    try:
        assert store.get(uuid4()) is None
    finally:
        os.unlink(path)


def test_store_save_persists_fields():
    store, path = _temp_store(60)
    try:
        session = store.create()
        session.repository = "pypa/packaging"
        store.save(session)
        loaded = store.get(session.id)
        assert loaded.repository == "pypa/packaging"
    finally:
        os.unlink(path)


def test_store_expiry():
    store, path = _temp_store(1)
    try:
        session = store.create()
        time.sleep(1.1)
        assert store.get(session.id) is None
    finally:
        os.unlink(path)


def test_store_cleanup():
    store, path = _temp_store(1)
    try:
        session = store.create()
        time.sleep(1.1)
        store._cleanup_expired()
        assert store.get(session.id) is None
    finally:
        os.unlink(path)
