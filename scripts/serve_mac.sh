#!/usr/bin/env bash
# Local Mac entrypoint for JevCommunity.
# Default: Kev-0.8B on MLX (~50 ms) — fits 16 GB without swap thrash.
# Quality (slower, ~8x): JEVCOMMUNITY_QUALITY=1 ./scripts/serve_mac.sh
#   -> serves RoderickQiu/kev-4b-mlx-8bit alone (~400-500 ms warm)
# Optional cascade (NOT recommended on 16 GB): export JEVCOMMUNITY_ESCALATE_RUN=RoderickQiu/kev-4b-mlx-8bit
#   Dual-resident 0.8B+4B tends to swap and can make escalations tens of seconds.
# Env:
#   leave KEV_BACKEND unset (auto → MLX on Darwin)
#   optional KEV_API_KEY for bearer auth (unset = open local server)
set -euo pipefail
cd "$(dirname "$0")/.."
uv sync --extra serve
if [[ "${JEVCOMMUNITY_QUALITY:-}" == "1" ]]; then
  exec uv run --extra serve python -m kev.serve \
    --run RoderickQiu/kev-4b-mlx-8bit \
    --host 127.0.0.1 \
    --port 8008 \
    --device auto
fi
exec uv run --extra serve python -m kev.serve \
  --run jaredpalmer/kev-0.8b@v1.0 \
  --host 127.0.0.1 \
  --port 8008 \
  --device auto
