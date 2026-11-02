#!/usr/bin/env bash
# Local Mac entrypoint for JevCommunity (Kev-0.8B on Apple Silicon).
# Env defaults for M4 16GB:
#   leave KEV_BACKEND unset (auto → MLX for hybrid Qwen3.5 on Darwin)
#   do not set KEV_TRUNCATE_STATES unless needed
#   optional KEV_API_KEY for bearer auth (unset = open local server)
set -euo pipefail
cd "$(dirname "$0")/.."
uv sync --extra serve
exec uv run --extra serve python -m kev.serve \
  --run jaredpalmer/kev-0.8b@v1.0 \
  --host 127.0.0.1 \
  --port 8008 \
  --device auto
