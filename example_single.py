#!/usr/bin/env python3
"""Single-file JevCommunity client. Needs the server: ./scripts/serve_mac.sh"""
from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request

BASE_URL = os.environ.get("JECOMMUNITY_BASE_URL", "http://127.0.0.1:8008").rstrip("/")
API_KEY = os.environ.get("KEV_API_KEY", "").strip()

STATE = (
    "Our API integration started returning 500 errors on every request about "
    "20 minutes ago, and we cannot process any customer orders until this is fixed."
)

QUESTIONS = {
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
}


def system_one(state: str, questions: dict | None = None) -> dict:
    headers = {"content-type": "application/json"}
    if API_KEY:
        headers["authorization"] = f"Bearer {API_KEY}"
    payload = {
        "state": state,
        "model": "jev-latest",
        "questions": questions or QUESTIONS,
    }
    req = urllib.request.Request(
        f"{BASE_URL}/v1/systemone",
        data=json.dumps(payload).encode(),
        headers=headers,
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=180) as resp:
        return json.load(resp)


def main() -> None:
    state = " ".join(sys.argv[1:]).strip() or STATE
    try:
        body = system_one(state)
    except urllib.error.URLError as e:
        print(f"Cannot reach {BASE_URL}: {e}")
        print("Start the server with: ./scripts/serve_mac.sh")
        sys.exit(1)

    a = body["answers"]
    print("state:", state[:120] + ("…" if len(state) > 120 else ""))
    print("department:", a["department"]["choice"],
          f"(confidence {a['department']['confidence']})")
    print("  probs:", a["department"]["probabilities"])
    print("frustration: score", a["frustration"]["score"],
          f"(confidence {a['frustration']['confidence']})")
    print("is_urgent:", a["is_urgent"]["noul"])
    print("latency_ms:", body.get("latency_ms"),
          "| escalated:", body.get("escalated", False))


if __name__ == "__main__":
    main()
