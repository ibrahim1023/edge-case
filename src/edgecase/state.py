import sqlite3
from datetime import UTC, datetime
from pathlib import Path
from uuid import UUID

from edgecase.config import settings
from edgecase.models import Session


class SessionStore:
    def __init__(self, db_path: Path | str | None = None, ttl_seconds: int | None = None):
        self._db_path = str(db_path or settings.session_db_path)
        self._ttl_seconds = ttl_seconds or settings.session_ttl_seconds
        self._init_db()

    def _init_db(self) -> None:
        Path(self._db_path).parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(self._db_path) as conn:
            conn.execute(
                "CREATE TABLE IF NOT EXISTS sessions ("
                "id TEXT PRIMARY KEY, data TEXT NOT NULL, expires_at REAL NOT NULL)"
            )
            conn.execute("CREATE INDEX IF NOT EXISTS idx_expires ON sessions(expires_at)")

    def _now(self) -> float:
        return datetime.now(UTC).timestamp()

    def _expiry(self) -> float:
        return self._now() + self._ttl_seconds

    def _expires_at(self) -> datetime:
        return datetime.fromtimestamp(self._expiry(), tz=UTC)

    def create(self) -> Session:
        session = Session()
        session.expires_at = self._expires_at()
        self.save(session)
        return session

    def get(self, session_id: UUID) -> Session | None:
        self._cleanup_expired()
        with sqlite3.connect(self._db_path) as conn:
            row = conn.execute(
                "SELECT data FROM sessions WHERE id = ? AND expires_at > ?",
                (str(session_id), self._now()),
            ).fetchone()
        if not row:
            return None
        return Session.model_validate_json(row[0])

    def save(self, session: Session) -> None:
        session.expires_at = self._expires_at()
        data = session.model_dump_json()
        with sqlite3.connect(self._db_path) as conn:
            conn.execute(
                "INSERT OR REPLACE INTO sessions (id, data, expires_at) VALUES (?, ?, ?)",
                (str(session.id), data, self._expiry()),
            )

    def delete(self, session_id: UUID) -> None:
        with sqlite3.connect(self._db_path) as conn:
            conn.execute("DELETE FROM sessions WHERE id = ?", (str(session_id),))

    def _cleanup_expired(self) -> None:
        with sqlite3.connect(self._db_path) as conn:
            conn.execute("DELETE FROM sessions WHERE expires_at <= ?", (self._now(),))

    def configure(self, db_path: Path | str, ttl_seconds: int | None = None) -> None:
        self._db_path = str(db_path)
        if ttl_seconds is not None:
            self._ttl_seconds = ttl_seconds
        self._init_db()

    def clear(self) -> None:
        with sqlite3.connect(self._db_path) as conn:
            conn.execute("DELETE FROM sessions")


store = SessionStore()


def get_store() -> SessionStore:
    return store
