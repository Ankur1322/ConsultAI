from fastapi.testclient import TestClient

from consultai.main import app

client = TestClient(app)


def test_health() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_create_and_run_session() -> None:
    created = client.post(
        "/api/sessions",
        json={"vertical": "invoice_to_pay", "process_description": "Invoices arrive by email."},
    )
    assert created.status_code == 201
    session_id = created.json()["session"]["id"]
    ran = client.post(f"/api/sessions/{session_id}/run")
    assert ran.status_code == 200
    assert ran.json()["session"]["status"] == "completed"


def test_discovery_and_requirements_endpoints() -> None:
    payload = {"vertical": "customer_support", "process_description": "Agents answer customer emails."}
    discovery = client.post("/api/discovery", json=payload)
    assert discovery.status_code == 200
    assert discovery.json()["questions"]
    requirements = client.post(
        "/api/requirements",
        json={"process_description": payload["process_description"], "discovery_answers": {}},
    )
    assert requirements.status_code == 200
    assert requirements.json()["functional"][0]["text"].startswith("The system shall")


def test_source_retrieval_and_citation_endpoints() -> None:
    created = client.post(
        "/api/sessions",
        json={"vertical": "invoice_to_pay", "process_description": "Invoices require approval."},
    )
    session_id = created.json()["session"]["id"]
    source = client.post(
        f"/api/sessions/{session_id}/sources",
        json={"title": "Invoice policy", "text": "Invoices require manager approval before payment."},
    )
    assert source.status_code == 201
    research = client.post(
        f"/api/sessions/{session_id}/research",
        json={"query": "Invoices require manager approval"},
    )
    assert research.status_code == 200
    assert research.json()["claims"][0]["support_status"] == "supported"


def test_quality_endpoints() -> None:
    payload = {"process_description": "Agents answer customer emails.", "discovery_answers": {}}
    evaluation = client.post("/api/evaluate", json=payload)
    assert evaluation.status_code == 200
    assert "overall" in evaluation.json()
    critic = client.post("/api/critic", json=payload)
    assert critic.status_code == 200
    assert critic.json()["max_retries"] == 2
    risk = client.post("/api/risk-check", json={"id": "AI-001", "risks": []})
    assert risk.status_code == 200


def test_session_and_source_pii_are_redacted() -> None:
    created = client.post(
        "/api/sessions",
        json={
            "vertical": "customer_support",
            "process_description": "Contact alice@example.com for support.",
        },
    )
    assert created.status_code == 201
    session_id = created.json()["session"]["id"]
    session = client.get(f"/api/sessions/{session_id}").json()
    assert "alice@example.com" not in session["result"]["process_description"]
    source = client.post(
        f"/api/sessions/{session_id}/sources",
        json={"title": "Contact", "text": "Email alice@example.com for approval."},
    )
    assert source.status_code == 201
    assert source.json()["redaction_count"] == 1
