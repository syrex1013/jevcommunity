#!/usr/bin/env bash
# Local Mac entrypoint for JevCommunity.
# Default: fast+accurate cascade
#   Kev-0.8B (~50 ms clear tickets) + AbstractFramework/kev-4b-mlx-4bit for uncertain ones
#   4-bit quality pack (~3 GB) is meant to co-reside with 0.8B on 16 GB without the 8-bit swap thrash.
# Quality-only: JEVCOMMUNITY_QUALITY=1 ./scripts/serve_mac.sh  -> 4-bit 4B alone
# Fast-only:    JEVCOMMUNITY_ESCALATE_RUN=off ./scripts/serve_mac.sh
# Env:
#   leave KEV_BACKEND unset (auto → MLX on Darwin)
#   optional KEV_API_KEY for bearer auth (unset = open local server)
set -euo pipefail
cd "$(dirname "$0")/.."
uv sync --extra serve
if [[ "${JEVCOMMUNITY_QUALITY:-}" == "1" ]]; then
  exec env JEVCOMMUNITY_ESCALATE_RUN=off uv run --extra serve python -m kev.serve \
    --run AbstractFramework/kev-4b-mlx-4bit \
    --host 127.0.0.1 \
    --port 8008 \
    --device auto
fi
export JEVCOMMUNITY_ESCALATE_RUN="${JEVCOMMUNITY_ESCALATE_RUN:-AbstractFramework/kev-4b-mlx-4bit}"
exec uv run --extra serve python -m kev.serve \
  --run jaredpalmer/kev-0.8b@v1.0 \
  --host 127.0.0.1 \
  --port 8008 \
  --device auto
