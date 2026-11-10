import json
import os
from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from ..models import GraphState, Session, SourceDocument, SourceCreate, Vertical
from .auth import AuthenticatedUser


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
                    tenant_id UUID,
                    owner_id UUID,
                    vertical TEXT NOT NULL,
                    status TEXT NOT NULL,
                    created_at TIMESTAMPTZ NOT NULL,
                    updated_at TIMESTAMPTZ NOT NULL,
                    payload JSONB NOT NULL
                );
                ALTER TABLE consultai_sessions ADD COLUMN IF NOT EXISTS tenant_id UUID;
                ALTER TABLE consultai_sessions ADD COLUMN IF NOT EXISTS owner_id UUID;
                CREATE TABLE IF NOT EXISTS consultai_users (
                    id UUID PRIMARY KEY,
                    tenant_id UUID NOT NULL,
                    email TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    role TEXT NOT NULL DEFAULT 'owner',
                    created_at TIMESTAMPTZ NOT NULL
                );
                CREATE TABLE IF NOT EXISTS consultai_tokens (
                    token TEXT PRIMARY KEY,
                    user_id UUID NOT NULL REFERENCES consultai_users(id) ON DELETE CASCADE,
                    expires_at TIMESTAMPTZ NOT NULL
                );
                CREATE TABLE IF NOT EXISTS consultai_audit (
                    id BIGSERIAL PRIMARY KEY,
                    user_id UUID,
                    tenant_id UUID,
                    action TEXT NOT NULL,
                    resource_id UUID,
                    created_at TIMESTAMPTZ NOT NULL
                );
                CREATE TABLE IF NOT EXISTS consultai_sources (
                    source_id TEXT PRIMARY KEY,
                    session_id UUID NOT NULL REFERENCES consultai_sessions(id) ON DELETE CASCADE,
                    title TEXT NOT NULL,
                    text TEXT NOT NULL,
                    metadata JSONB NOT NULL
                );
                CREATE EXTENSION IF NOT EXISTS vector;
                ALTER TABLE consultai_sources ADD COLUMN IF NOT EXISTS embedding vector(768);
                CREATE INDEX IF NOT EXISTS consultai_sources_embedding_idx
                    ON consultai_sources USING hnsw (embedding vector_cosine_ops);
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

    def save_session(self, state: GraphState, user: AuthenticatedUser | None = None) -> None:
        self.connect()
        payload = state.model_dump(mode="json")
        with self._connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO consultai_sessions (id, tenant_id, owner_id, vertical, status, created_at, updated_at, payload)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (id) DO UPDATE SET
                    status = EXCLUDED.status,
                    updated_at = EXCLUDED.updated_at,
                    payload = EXCLUDED.payload
                """,
                (
                    state.session.id,
                    user.tenant_id if user else None,
                    user.id if user else None,
                    state.session.vertical.value,
                    state.session.status.value,
                    state.session.created_at,
                    datetime.now(timezone.utc),
                    json.dumps(payload),
                ),
            )

    def get_session(self, session_id: UUID, user: AuthenticatedUser | None = None) -> GraphState | None:
        self.connect()
        with self._connection.cursor() as cursor:
            if user:
                cursor.execute(
                    "SELECT payload FROM consultai_sessions WHERE id = %s AND tenant_id = %s",
                    (session_id, user.tenant_id),
                )
            else:
                cursor.execute("SELECT payload FROM consultai_sessions WHERE id = %s", (session_id,))
            row = cursor.fetchone()
        if row is None:
            return None
        return GraphState.model_validate(row[0])

    def create_user(self, user: AuthenticatedUser, password_hash: str) -> None:
        self.connect()
        with self._connection.cursor() as cursor:
            cursor.execute(
                "INSERT INTO consultai_users (id, tenant_id, email, password_hash, role, created_at) VALUES (%s,%s,%s,%s,%s,%s)",
                (user.id, user.tenant_id, user.email, password_hash, user.role, datetime.now(timezone.utc)),
            )

    def find_user(self, email: str) -> tuple[AuthenticatedUser, str] | None:
        self.connect()
        with self._connection.cursor() as cursor:
            cursor.execute("SELECT id, tenant_id, email, role, password_hash FROM consultai_users WHERE lower(email)=lower(%s)", (email,))
            row = cursor.fetchone()
        return None if row is None else (AuthenticatedUser(row[0], row[1], row[2], row[3]), row[4])

    def save_token(self, token: str, user_id: UUID, expires_at: datetime) -> None:
        self.connect()
        with self._connection.cursor() as cursor:
            cursor.execute("INSERT INTO consultai_tokens (token, user_id, expires_at) VALUES (%s,%s,%s)", (token, user_id, expires_at))

    def user_for_token(self, token: str) -> AuthenticatedUser | None:
        self.connect()
        with self._connection.cursor() as cursor:
            cursor.execute(
                "SELECT u.id, u.tenant_id, u.email, u.role FROM consultai_tokens t JOIN consultai_users u ON u.id=t.user_id WHERE t.token=%s AND t.expires_at > %s",
                (token, datetime.now(timezone.utc)),
            )
            row = cursor.fetchone()
        return None if row is None else AuthenticatedUser(row[0], row[1], row[2], row[3])

    def audit(self, user: AuthenticatedUser | None, action: str, resource_id: UUID | None = None) -> None:
        self.connect()
        with self._connection.cursor() as cursor:
            cursor.execute(
                "INSERT INTO consultai_audit (user_id, tenant_id, action, resource_id, created_at) VALUES (%s,%s,%s,%s,%s)",
                (user.id if user else None, user.tenant_id if user else None, action, resource_id, datetime.now(timezone.utc)),
            )

    def add_source(self, session_id: UUID, document: SourceDocument, embedding: list[float] | None = None) -> None:
        self.connect()
        with self._connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO consultai_sources (source_id, session_id, title, text, metadata, embedding)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (source_id) DO NOTHING
                """,
                (
                    document.source_id,
                    session_id,
                    document.title,
                    document.text,
                    json.dumps(document.metadata),
                    str(embedding) if embedding is not None else None,
                ),
            )

    def search_sources(
        self,
        session_id: UUID,
        query: str,
        limit: int = 20,
        query_embedding: list[float] | None = None,
    ) -> list[SourceDocument]:
        self.connect()
        with self._connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT source_id, session_id, title, text, metadata
                FROM consultai_sources
                WHERE session_id = %s
                  AND (
                    search_text @@ plainto_tsquery('simple', %s)
                    OR (%s IS NOT NULL AND embedding IS NOT NULL)
                  )
                ORDER BY
                    CASE WHEN %s IS NOT NULL AND embedding IS NOT NULL
                        THEN 1 - (embedding <=> %s::vector)
                        ELSE 0
                    END DESC,
                    ts_rank_cd(search_text, plainto_tsquery('simple', %s)) DESC
                LIMIT %s
                """,
                (
                    session_id,
                    query,
                    str(query_embedding) if query_embedding is not None else None,
                    str(query_embedding) if query_embedding is not None else None,
                    str(query_embedding) if query_embedding is not None else None,
                    query,
                    limit,
                ),
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
