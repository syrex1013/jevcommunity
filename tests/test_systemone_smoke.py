"""Live System One contract checks against a running local server."""
import os

import httpx
import pytest

BASE_URL = os.environ.get("JECOMMUNITY_BASE_URL", "http://127.0.0.1:8008")

TICKET_PAYLOAD = {
    "state": (
        "Our API integration started returning 500 errors on every request about "
        "20 minutes ago, and we cannot process any customer orders until this is fixed."
    ),
    "model": "jev-latest",
    "questions": {
        "department": {
            "type": "choice",
            "instructions": "Which team should handle this",
            "criteria": {
                "billing": "Payment or subscription issues",
                "technical": "Bugs or integration problems",
                "sales": "Pricing or account questions",
            },
        },
        "frustration": {
            "type": "score",
            "instructions": "How frustrated the customer appears",
            "criteria": [
                "Calm, just stating facts",
                "Frustrated but civil",
                "Very angry, strong language",
            ],
        },
        "is_urgent": {
            "type": "noul",
            "instructions": "The message conveys urgency or time-sensitivity",
        },
    },
}


@pytest.mark.server
def test_models_lists_local_aliases():
    r = httpx.get(f"{BASE_URL}/v1/models", timeout=30.0)
    assert r.status_code == 200
    names = {m["name"] for m in r.json()["models"]}
    assert "jev-latest" in names
    assert "jevcommunity-0.8b" in names


@pytest.mark.server
def test_systemone_ticket_shape():
    r = httpx.post(f"{BASE_URL}/v1/systemone", json=TICKET_PAYLOAD, timeout=120.0)
    assert r.status_code == 200, r.text
    body = r.json()
    answers = body["answers"]

    dept = answers["department"]
    assert dept["type"] == "choice"
    assert set(dept) >= {"choice", "confidence", "probabilities"}
    assert abs(sum(dept["probabilities"].values()) - 1.0) < 0.02

    frust = answers["frustration"]
    assert frust["type"] == "score"
    assert set(frust) >= {"score", "legend", "probabilities", "confidence"}
    assert abs(sum(frust["probabilities"].values()) - 1.0) < 0.02

    urgent = answers["is_urgent"]
    assert urgent["type"] == "noul"
    assert isinstance(urgent["noul"], (int, float))
    assert 0.0 <= float(urgent["noul"]) <= 1.0
