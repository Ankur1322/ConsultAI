# Local Deployment and Production Checklist

## Local Docker

```powershell
Copy-Item .env.example .env
.\docker-compose.ps1 up --build
```

The API is available at `http://localhost:8000`. Set `CONSULTAI_API_KEY` in
`.env` to require `X-API-Key` on non-health endpoints.

## Production checklist

- Use a managed PostgreSQL instance with TLS and backups.
- Store `CONSULTAI_API_KEY` and provider credentials in a secret manager.
- Put the API behind TLS and a reverse proxy with request-size and rate limits.
- Replace in-memory session and evidence stores.
- Restrict outbound model and connector access.
- Export structured logs and metrics without raw process text or PII.
- Add health, readiness, backup-restore, and dependency failure checks.
