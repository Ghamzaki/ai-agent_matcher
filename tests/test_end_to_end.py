import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_agent_manifest():
    """Check that the agent manifest endpoint returns valid metadata."""
    response = client.get("/.well-known/agent.json")
    assert response.status_code == 200
    data = response.json()
    assert "name" in data
    assert "skills" in data
    assert data["name"] == "TelexVerificationAgent"


def test_process_alert_success():
    """Test end-to-end alert processing with a realistic example."""
    email_text = (
        "Dear Customer, You made a purchase of $50.99 at AMAZONPRCH "
        "on 2025-11-03. If you did not authorize, contact support."
    )

    response = client.post("/process_alert", json={"email_content": email_text})
    assert response.status_code == 200, response.text

    artifact = response.json()
    # Expected schema keys
    for key in ["status", "match_found", "match_score", "alert_data", "message"]:
        assert key in artifact

    # Check logical conditions
    assert artifact["status"] == "COMPLETED"
    assert isinstance(artifact["match_score"], float)
    assert 0.0 <= artifact["match_score"] <= 1.0


def test_ledger_endpoints():
    """Ensure ledger diagnostics endpoints respond correctly."""
    r1 = client.get("/ledger")
    assert r1.status_code == 200
    assert isinstance(r1.json(), list)

    r2 = client.post("/ledger/re-poll")
    assert r2.status_code == 200
    assert "message" in r2.json()