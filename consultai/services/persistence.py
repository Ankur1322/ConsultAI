import json
import os
from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from ..models import GraphState, Session, SourceDocument, SourceCreate, Vertical


class PersistenceError(RuntimeError):
    """Raised when durable storage is unavailable or rejects a write."""


class Repository:
    def __init__(self) -> None:
        self.database_url = os.getenv(
            "CONSULTAI_DATABASE_URL",
            "postgresql://consultai:consultai@localhost:5432/consultai",
        )
        self._connection = None

    def connect(self) -> None:
        if self._connection is not None:
            return
        try:
            import psycopg

            self._connection = psycopg.connect(self.database_url, autocommit=True)
            self._initialize()
        except Exception as exc:
            raise PersistenceError("Unable to connect to PostgreSQL") from exc

    def _initialize(self) -> None:
        if self._connection is None:
            raise PersistenceError("Repository is not connected")
        with self._connection.cursor() as cursor:
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS consultai_sessions (
                    id UUID PRIMARY KEY,
                    vertical TEXT NOT NULL,
                    status TEXT NOT NULL,
                    created_at TIMESTAMPTZ NOT NULL,
                    updated_at TIMESTAMPTZ NOT NULL,
                    payload JSONB NOT NULL
                );
                CREATE TABLE IF NOT EXISTS consultai_sources (
                    source_id TEXT PRIMARY KEY,
                    session_id UUID NOT NULL REFERENCES consultai_sessions(id) ON DELETE CASCADE,
                    title TEXT NOT NULL,
                    text TEXT NOT NULL,
                    metadata JSONB NOT NULL
                );
                ALTER TABLE consultai_sources ADD COLUMN IF NOT EXISTS search_text TSVECTOR
                    GENERATED ALWAYS AS (to_tsvector('simple', title || ' ' || text)) STORED;
                CREATE INDEX IF NOT EXISTS consultai_sources_search_idx
                    ON consultai_sources USING GIN (search_text);
                CREATE TABLE IF NOT EXISTS consultai_checkpoints (
                    session_id UUID NOT NULL REFERENCES consultai_sessions(id) ON DELETE CASCADE,
                    checkpoint_no BIGSERIAL,
                    created_at TIMESTAMPTZ NOT NULL,
                    state JSONB NOT NULL,
                    PRIMARY KEY (session_id, checkpoint_no)
                );
                """
            )

    def save_session(self, state: GraphState) -> None:
        self.connect()
        payload = state.model_dump(mode="json")
        with self._connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO consultai_sessions (id, vertical, status, created_at, updated_at, payload)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (id) DO UPDATE SET
                    status = EXCLUDED.status,
                    updated_at = EXCLUDED.updated_at,
                    payload = EXCLUDED.payload
                """,
                (
                    state.session.id,
                    state.session.vertical.value,
                    state.session.status.value,
                    state.session.created_at,
                    datetime.now(timezone.utc),
                    json.dumps(payload),
                ),
            )

    def get_session(self, session_id: UUID) -> GraphState | None:
        self.connect()
        with self._connection.cursor() as cursor:
            cursor.execute("SELECT payload FROM consultai_sessions WHERE id = %s", (session_id,))
            row = cursor.fetchone()
        if row is None:
            return None
        return GraphState.model_validate(row[0])

    def add_source(self, session_id: UUID, document: SourceDocument) -> None:
        self.connect()
        with self._connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO consultai_sources (source_id, session_id, title, text, metadata)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (source_id) DO NOTHING
                """,
                (document.source_id, session_id, document.title, document.text, json.dumps(document.metadata)),
            )

    def search_sources(self, session_id: UUID, query: str, limit: int = 20) -> list[SourceDocument]:
        self.connect()
        with self._connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT source_id, session_id, title, text, metadata
                FROM consultai_sources
                WHERE session_id = %s
                  AND search_text @@ plainto_tsquery('simple', %s)
                ORDER BY ts_rank_cd(search_text, plainto_tsquery('simple', %s)) DESC
                LIMIT %s
                """,
                (session_id, query, query, limit),
            )
            rows = cursor.fetchall()
        return [
            SourceDocument(
                source_id=row[0],
                session_id=row[1],
                title=row[2],
                text=row[3],
                metadata=row[4],
            )
            for row in rows
        ]

    def list_sources(self, session_id: UUID) -> list[SourceDocument]:
        self.connect()
        with self._connection.cursor() as cursor:
            cursor.execute(
                "SELECT source_id, session_id, title, text, metadata FROM consultai_sources WHERE session_id = %s",
                (session_id,),
            )
            rows = cursor.fetchall()
        return [
            SourceDocument(
                source_id=row[0],
                session_id=row[1],
                title=row[2],
                text=row[3],
                metadata=row[4],
            )
            for row in rows
        ]

    def checkpoint(self, state: GraphState) -> None:
        self.connect()
        with self._connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO consultai_checkpoints (session_id, created_at, state)
                VALUES (%s, %s, %s)
                """,
                (state.session.id, datetime.now(timezone.utc), json.dumps(state.model_dump(mode="json"))),
            )
