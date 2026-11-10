# ConsultAI

ConsultAI is a local-first multi-agent platform for turning business-process descriptions into requirements, process maps, cited research, and ranked AI opportunities.

## Phase 2 status

This repository currently contains the Docker and CI scaffold, typed Pydantic contracts, a FastAPI session API, a streaming endpoint, a React/Vite shell, and a complete stub graph. Agent intelligence, persistence, redaction, retrieval, and evaluation are intentionally staged for later phases.

## Run locally

```powershell
py -3.11 -m pip install -e ".[dev]"
py -3.11 -m pytest
py -3.11 -m uvicorn consultai.main:app --reload
```

Open `http://localhost:8000/docs` for the API explorer.

Run each command separately. Do not paste `Copy-Item` or another command directly after `--reload`.

## Run with Docker

```powershell
Copy-Item .env.example .env
docker compose up --build
```

Docker Desktop must be installed and running before the Docker command.
If PowerShell says `docker` is not recognized, install Docker Desktop from
https://www.docker.com/products/docker-desktop/ or run
`winget install --id Docker.DockerDesktop --exact`. After installation, start
Docker Desktop and open a new PowerShell window so `docker` is added to PATH.
If an existing PowerShell window still cannot find it, use
`C:\Program Files\Docker\Docker\resources\bin\docker.exe` once or restart
PowerShell. If `docker version` shows a client but cannot connect to
`dockerDesktopLinuxEngine`, Docker Desktop is still starting or needs to be
opened manually.

For a PowerShell window whose PATH has not refreshed, use the included
launcher instead:

```powershell
.\docker-compose.ps1 up --build
```

PowerShell syntax note: the call operator `&` must start a new command on a
new line. Do not paste it directly after `docker compose up --build`.

The current phase does not yet connect the API to Postgres or Ollama; those services are reserved in the compose topology for later phases.

## Phase 3 API smoke tests

With Docker running, the discovery and requirements endpoints are available:

```powershell
$body = '{"vertical":"invoice_to_pay","process_description":"Agents copy invoices from email into the accounting system."}'
Invoke-RestMethod http://localhost:8000/api/discovery -Method Post -ContentType "application/json" -Body $body

$requirements = '{"process_description":"Agents copy invoices from email into the accounting system.","discovery_answers":{}}'
Invoke-RestMethod http://localhost:8000/api/requirements -Method Post -ContentType "application/json" -Body $requirements
```

## Phase 4 evidence flow

The API now supports session-scoped source ingestion and claim-level citation checks:

```powershell
$session = Invoke-RestMethod http://localhost:8000/api/sessions -Method Post -ContentType "application/json" -Body '{"vertical":"invoice_to_pay","process_description":"Invoices require approval."}'
$id = $session.session.id
Invoke-RestMethod "http://localhost:8000/api/sessions/$id/sources" -Method Post -ContentType "application/json" -Body '{"title":"Invoice policy","text":"Invoices require manager approval before payment."}'
Invoke-RestMethod "http://localhost:8000/api/sessions/$id/research" -Method Post -ContentType "application/json" -Body '{"query":"Invoices require manager approval"}'
```

## Test

```powershell
py -3.11 -m pytest
Set-Location .\frontend
npm install
npm test
npm run build
```

See [phase 1 requirements](docs/phase-1/requirements.md) and [phase 1 data models](docs/phase-1/data-models.md) for the approved contracts.
