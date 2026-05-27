#!/usr/bin/env bash
# Preflight: is this machine ready to run LocateAnything-3B?
set -euo pipefail

green() { printf '\033[0;32m%s\033[0m\n' "$1"; }
red() { printf '\033[0;31m%s\033[0m\n' "$1"; }
yellow() { printf '\033[0;33m%s\033[0m\n' "$1"; }

echo "== LocateAnything GPU preflight =="
echo

# 1. NVIDIA driver / GPU
if ! command -v nvidia-smi >/dev/null 2>&1; then
  red "✗ nvidia-smi not found. Install the NVIDIA driver (and, on Windows, run inside WSL2)."
  exit 1
fi

nvidia-smi --query-gpu=name,memory.total,compute_cap --format=csv,noheader | while IFS=',' read -r name mem cc; do
  name=$(echo "$name" | xargs); mem=$(echo "$mem" | xargs); cc=$(echo "$cc" | xargs)
  echo "GPU:     $name"
  echo "VRAM:    $mem"
  echo "Compute: $cc"
  major=${cc%%.*}
  if [ "${major:-0}" -ge 8 ]; then
    green "✓ Architecture supported (Ampere or newer)."
  else
    red "✗ Compute capability < 8.0 — not supported (need Ampere/Lovelace/Hopper/Blackwell)."
  fi
done
echo

# 2. Docker + NVIDIA Container Toolkit
if ! command -v docker >/dev/null 2>&1; then
  yellow "! Docker not found. Install Docker (Desktop on Windows) to use the one-command setup."
  exit 0
fi

echo "Checking Docker GPU access..."
if docker run --rm --gpus all nvidia/cuda:12.4.1-base-ubuntu22.04 nvidia-smi >/dev/null 2>&1; then
  green "✓ Docker can access the GPU (NVIDIA Container Toolkit OK)."
else
  yellow "! Docker could not access the GPU. Install the NVIDIA Container Toolkit, or"
  yellow "  try the no-GPU mock: docker compose -f docker-compose.yml -f docker-compose.mock.yml up"
fi
