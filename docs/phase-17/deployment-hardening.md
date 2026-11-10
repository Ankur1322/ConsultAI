# Phase 17: Deployment hardening

- `GET /health` is a liveness check.
- `GET /ready` verifies the configured PostgreSQL repository can connect.
- Compose waits for PostgreSQL readiness and uses a healthcheck.
- PostgreSQL credentials are supplied through `.env`; no password is embedded
  in the Compose file.
- CI runs Python dependency auditing and high-severity npm auditing.

For production, place the API behind a TLS reverse proxy, use a managed secret
store, and schedule encrypted PostgreSQL backups with restore drills.
