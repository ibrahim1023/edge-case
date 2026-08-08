from uuid import UUID

from edgecase.models import Session


class SessionStore:
    def __init__(self):
        self._sessions: dict[UUID, Session] = {}

    def create(self) -> Session:
        session = Session()
        self._sessions[session.id] = session
        return session

    def get(self, session_id: UUID) -> Session | None:
        return self._sessions.get(session_id)

    def save(self, session: Session) -> None:
        self._sessions[session.id] = session


store = SessionStore()


def get_store() -> SessionStore:
    return store
