#!/usr/bin/env python3
"""Interactive local System One demo against JevCommunity.

Requires the server:
  ./scripts/serve_mac.sh

Then:
  uv run --extra serve python example.py
"""
from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request

BASE_URL = os.environ.get("JECOMMUNITY_BASE_URL", "http://127.0.0.1:8008").rstrip("/")
SAMPLE = (
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


def post_systemone(state: str) -> dict:
    payload = json.dumps(
        {"state": state, "model": "jev-latest", "questions": QUESTIONS}
    ).encode()
    req = urllib.request.Request(
        f"{BASE_URL}/v1/systemone",
        data=payload,
        headers={"content-type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=180) as resp:
        return json.load(resp)


def check_server() -> None:
    try:
        with urllib.request.urlopen(f"{BASE_URL}/v1/models", timeout=3) as resp:
            json.load(resp)
    except Exception as e:
        print(f"Server not reachable at {BASE_URL} ({e})")
        print("Start it with: ./scripts/serve_mac.sh")
        sys.exit(1)


def print_answers(body: dict) -> None:
    answers = body.get("answers") or {}
    dept = answers.get("department") or {}
    frus = answers.get("frustration") or {}
    urg = answers.get("is_urgent") or {}
    print()
    print(f"  department : {dept.get('choice')}  (confidence {dept.get('confidence')})")
    probs = dept.get("probabilities") or {}
    if probs:
        bits = " · ".join(f"{k} {v}" for k, v in probs.items())
        print(f"               {bits}")
    print(f"  frustration: score {frus.get('score')}  (confidence {frus.get('confidence')})")
    print(f"  is_urgent  : {urg.get('noul')}")
    lat = body.get("latency_ms")
    escalated = body.get("escalated")
    extra = []
    if lat is not None:
        extra.append(f"{lat} ms")
    if escalated is not None:
        extra.append("escalated" if escalated else "fast path")
    if extra:
        print(f"  ({', '.join(extra)})")
    print()


def read_state() -> str | None:
    print("Paste a support ticket / document state.")
    print("Empty line = sample ticket.  q = quit.")
    try:
        line = input("> ").strip()
    except (EOFError, KeyboardInterrupt):
        print()
        return None
    if line.lower() in {"q", "quit", "exit"}:
        return None
    if not line:
        print(f"(using sample)\n{SAMPLE}\n")
        return SAMPLE
    # allow multi-line: keep reading until a blank line
    lines = [line]
    print("(blank line to submit, or keep typing)")
    while True:
        try:
            nxt = input()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if nxt == "":
            break
        lines.append(nxt)
    return "\n".join(lines).strip() or SAMPLE


def main() -> None:
    check_server()
    print(f"JevCommunity interactive demo → {BASE_URL}")
    print("Questions: department (choice), frustration (score), is_urgent (noul)")
    print()
    while True:
        state = read_state()
        if state is None:
            break
        try:
            body = post_systemone(state)
        except urllib.error.HTTPError as e:
            detail = e.read().decode("utf-8", errors="replace")
            print(f"HTTP {e.code}: {detail}")
            continue
        except Exception as e:
            print(f"Request failed: {e}")
            continue
        print_answers(body)


if __name__ == "__main__":
    main()
