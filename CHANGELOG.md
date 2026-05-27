# Changelog

All notable changes to this project are documented here.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Initial project scaffold: repository structure, engineering conventions, CI skeleton, licenses, and documentation.
- FastAPI backend wrapping NVIDIA LocateAnything-3B with all task presets (detection, phrase grounding, text grounding, scene-text detection, GUI grounding, pointing), `fast`/`hybrid`/`slow` decode modes, box/point parsing, and a no-GPU mock mode (`LA_MOCK=1`).
- SQLite-backed search history with image storage and list/get/delete endpoints.
- React + Vite + Tailwind web UI: machine-vision HUD aesthetic, image upload (drag/drop + mobile camera), reticle box/crosshair overlay, search log, mobile-responsive layout, GPU/health readout, and a runtime-configurable backend URL for remote-GPU use.
- Docker Compose deployment with NVIDIA GPU passthrough, model/HF cache volumes, a no-GPU mock override, and a `scripts/check-gpu.sh` preflight check.

[Unreleased]: https://github.com/gammahazard/locate-anything/commits/main
