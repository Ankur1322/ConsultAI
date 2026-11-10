# Phase 11: Authentication and authorization

ConsultAI now supports an opt-in PostgreSQL-backed identity flow:

- Set `CONSULTAI_AUTH_ENABLED=true` and `CONSULTAI_STORAGE=postgres`.
- Register with `POST /api/auth/register`, then send `Authorization: Bearer <access_token>`.
- Passwords use PBKDF2-HMAC-SHA256; raw passwords are never persisted.
- Users belong to a tenant, and durable sessions carry tenant and owner identifiers.
- Authentication events are written to `consultai_audit`.
- The existing API-key mode remains available when authentication is disabled.

Registration is intentionally disabled without PostgreSQL so identities and tokens
are never silently kept only in process memory.
