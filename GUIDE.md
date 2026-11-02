# JevCommunity Guide

How to run the local System One decision server and call it from one Python file.

## What this is

JevCommunity serves a **Jev-compatible** decision API on your Mac:

- Input: one shared `state` (document / ticket) + typed questions
- Output: probability distributions + confidence
- Not a chat model — it does **not** generate text

Default stack on Apple Silicon (16 GB):

| Role | Model | When |
| --- | --- | --- |
| Fast path | `jaredpalmer/kev-0.8b@v1.0` | clear tickets (~50 ms) |
| Quality escalate | `AbstractFramework/kev-4b-mlx-4bit` | uncertain answers (~400–500 ms warm) |

## Prerequisites

- macOS Apple Silicon
- [uv](https://docs.astral.sh/uv/)
- Python 3.13 (repo pins this)
- Hugging Face network access on first run (downloads weights into `~/.cache/huggingface`)

```bash
git clone https://github.com/syrex1013/jevcommunity.git
cd jevcommunity
```

## Start the server

```bash
./scripts/serve_mac.sh
```

Listens on `http://127.0.0.1:8008`.

### Modes

| Goal | Command |
| --- | --- |
| Default (fast + accurate cascade) | `./scripts/serve_mac.sh` |
| Fast only (0.8B, no escalate) | `JEVCOMMUNITY_ESCALATE_RUN=off ./scripts/serve_mac.sh` |
| Quality only (4-bit 4B alone) | `JEVCOMMUNITY_QUALITY=1 ./scripts/serve_mac.sh` |

Optional auth:

```bash
export KEV_API_KEY=local-secret
./scripts/serve_mac.sh
# then send: Authorization: Bearer local-secret
```

Health check:

```bash
curl -sS http://127.0.0.1:8008/v1/models | python3 -m json.tool
```

## Question types

| Type | Meaning | Response fields |
| --- | --- | --- |
| `choice` | pick one named option | `choice`, `confidence`, `probabilities` |
| `score` | ordered levels → expected index | `score`, `legend`, `confidence`, `probabilities` |
| `noul` | P(statement is true) | `noul` (float in `[0,1]`) |

Accepted `model` names: `jev-latest`, `kev-latest`, `jevcommunity-0.8b`, `jevcommunity-4b-8bit`.

## curl example

```bash
curl -sS http://127.0.0.1:8008/v1/systemone \
  -H 'content-type: application/json' \
  -d '{
    "state": "Our API integration started returning 500 errors on every request about 20 minutes ago, and we cannot process any customer orders until this is fixed.",
    "model": "jev-latest",
    "questions": {
      "department": {
        "type": "choice",
        "instructions": "Which team should handle this",
        "criteria": {
          "billing": "Payment or subscription issues",
          "technical": "Bugs or integration problems",
          "sales": "Pricing or account questions"
        }
      },
      "frustration": {
        "type": "score",
        "instructions": "How frustrated the customer appears",
        "criteria": [
          "Calm, just stating facts",
          "Frustrated but civil",
          "Very angry, strong language"
        ]
      },
      "is_urgent": {
        "type": "noul",
        "instructions": "The message conveys urgency or time-sensitivity"
      }
    }
  }' | python3 -m json.tool
```

Typical clear-ticket result:

- `answers.department.choice` → `technical`
- `answers.department.confidence` → ~`0.98`
- `answers.is_urgent.noul` → ~`0.70`
- `escalated` → `false` on clear tickets

## Single-file example

Save as `guide_example.py` (or use the copy at [`example_single.py`](./example_single.py)), start the server, then:

```bash
python3 example_single.py
python3 example_single.py "Invoice looks wrong and pricing page is confusing"
```

```python
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
```

## Interactive demo

Loop over pasted tickets:

```bash
uv run --extra serve python example.py
```

## TypeSafe SDK

Same API via the official client:

```bash
uv run --extra serve python examples/route_ticket.py
```

## Tests

```bash
JECOMMUNITY_BASE_URL=http://127.0.0.1:8008 \
  uv run pytest -m server tests/test_systemone_smoke.py -q
```

## Tips for 16 GB Macs

1. Keep the **default cascade** (0.8B + 4-bit 4B). Clear work stays ~50 ms.
2. Avoid dual-loading **8-bit** Kev-4B with 0.8B — that thrashed swap in testing.
3. For max quality on hard tickets only, restart with `JEVCOMMUNITY_QUALITY=1`.
4. First request after boot can be slower (Metal compile / weight page-in); warm requests are the real number.

## Response shape (abbreviated)

```json
{
  "answers": {
    "department": {
      "type": "choice",
      "choice": "technical",
      "confidence": 0.9782,
      "probabilities": {
        "billing": 0.0099,
        "technical": 0.9854,
        "sales": 0.0046
      }
    },
    "frustration": {
      "type": "score",
      "score": 0.87,
      "confidence": 0.0,
      "legend": ["Calm, just stating facts", "Frustrated but civil", "Very angry, strong language"],
      "probabilities": [0.12, 0.71, 0.17]
    },
    "is_urgent": {
      "type": "noul",
      "noul": 0.6999
    }
  },
  "latency_ms": 54.2,
  "escalated": false
}
```

## Limits

- Text primitives only: `choice` / `score` / `noul` (no Box/images here)
- Local quality tracks open **Kev**, not hosted TypeSafe Jev accuracy
- Not affiliated with TypeSafe AI
