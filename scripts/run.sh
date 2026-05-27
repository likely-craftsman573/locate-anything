#!/usr/bin/env bash
# Launch the stack, automatically picking a free host port for the web UI.
#
# Usage:
#   scripts/run.sh                 # build/run the dev stack
#   scripts/run.sh --ghcr          # run prebuilt images from GHCR
#   scripts/run.sh --mock          # no-GPU mock mode
# Extra args after the flags are passed through to `docker compose up`.
set -euo pipefail

cd "$(dirname "$0")/.."

FILES=(-f docker-compose.yml)
for arg in "$@"; do
  case "$arg" in
    --ghcr) FILES=(-f docker-compose.ghcr.yml); shift ;;
    --mock) FILES+=(-f docker-compose.mock.yml); shift ;;
  esac
done

# Preferred port: FRONTEND_PORT from the environment/.env, else 8080.
start_port="${FRONTEND_PORT:-8080}"
if [ -f .env ]; then
  env_port="$(grep -E '^FRONTEND_PORT=' .env | tail -1 | cut -d= -f2 | tr -d '[:space:]')"
  [ -n "${env_port:-}" ] && start_port="$env_port"
fi

is_free() { ! (exec 3<>"/dev/tcp/127.0.0.1/$1") 2>/dev/null; }

port="$start_port"
while ! is_free "$port"; do
  echo "port $port is in use, trying $((port + 1))…"
  port=$((port + 1))
  if [ "$port" -gt $((start_port + 50)) ]; then
    echo "no free port found near $start_port" >&2
    exit 1
  fi
done

echo "▸ web UI on http://localhost:$port"
FRONTEND_PORT="$port" docker compose "${FILES[@]}" up "$@"
