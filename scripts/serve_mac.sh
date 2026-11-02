#!/usr/bin/env bash
# Local Mac entrypoint for JevCommunity.
# Default: Kev-0.8B fast path + escalate uncertain answers to Kev-4B MLX 8-bit.
# Env:
#   leave KEV_BACKEND unset (auto → MLX on Darwin)
#   JEVCOMMUNITY_ESCALATE_RUN=RoderickQiu/kev-4b-mlx-8bit  (default below)
#   unset JEVCOMMUNITY_ESCALATE_RUN for pure 0.8B speed
#   --run RoderickQiu/kev-4b-mlx-8bit for always-on quality (~8x slower)
#   optional KEV_API_KEY for bearer auth (unset = open local server)
set -euo pipefail
cd "$(dirname "$0")/.."
uv sync --extra serve
export JEVCOMMUNITY_ESCALATE_RUN="${JEVCOMMUNITY_ESCALATE_RUN-RoderickQiu/kev-4b-mlx-8bit}"
exec uv run --extra serve python -m kev.serve \
  --run jaredpalmer/kev-0.8b@v1.0 \
  --host 127.0.0.1 \
  --port 8008 \
  --device auto
