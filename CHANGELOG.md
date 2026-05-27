# Changelog

All notable changes to this project are documented here.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.0] - 2026-05-27

### Added
- Initial project scaffold: repository structure, engineering conventions, CI skeleton, licenses, and documentation.
- FastAPI backend wrapping NVIDIA LocateAnything-3B with all task presets (detection, phrase grounding, text grounding, scene-text detection, GUI grounding, pointing), `fast`/`hybrid`/`slow` decode modes, box/point parsing, and a no-GPU mock mode (`LA_MOCK=1`).
- SQLite-backed search history with image storage and list/get/delete endpoints.
- React + Vite + Tailwind web UI: machine-vision HUD aesthetic, image upload (drag/drop + mobile camera), reticle box/crosshair overlay, search log, mobile-responsive layout, GPU/health readout, and a runtime-configurable backend URL for remote-GPU use.
- Docker Compose deployment with NVIDIA GPU passthrough, model/HF cache volumes, a no-GPU mock override, and a `scripts/check-gpu.sh` preflight check.
- Native support for the full GPU range incl. Blackwell (RTX 50-series, `sm_120`) via a CUDA 12.8 PyTorch build, with a supported-GPU table in the README.
- Non-blocking model load: the server starts immediately and loads the model in the background; `/api/health` reports a `loading` status so the UI shows "loading model…" instead of appearing offline.
- GPU picker: enumerate all visible GPUs and choose which one runs the model from the System page (`GET /api/devices`, `POST /api/device`, `LA_DEVICE` for the startup default), with a VRAM guard, an inference lock, and the active card reflected in the status badge.
- Info tooltips (ⓘ) on each task chip and the decode-mode control, with task descriptions served from the backend.
- Distribution: release workflow builds and pushes backend/frontend images to GHCR on version tags; an end-user `docker-compose.ghcr.yml` runs prebuilt images with no source checkout. The backend port is no longer published by default (frontend-only), with `docker-compose.expose-backend.yml` to opt in, and `scripts/run.sh` auto-selects a free UI port.

[Unreleased]: https://github.com/gammahazard/locate-anything/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/gammahazard/locate-anything/releases/tag/v0.1.0
