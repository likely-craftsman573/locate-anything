# locate-anything

A sleek, mobile-friendly web UI for **[NVIDIA LocateAnything-3B](https://huggingface.co/nvidia/LocateAnything-3B)** — point it at an image, type what you want to find in plain language, and get bounding boxes back. Object detection, phrase grounding, OCR/text localization, document layout, GUI element grounding, and pointing — all from one prompt box.

Run it on your own NVIDIA GPU with a single `docker compose up`.

> [!IMPORTANT]
> **Model license is non-commercial.** `LocateAnything-3B` is released under the [NVIDIA license](https://huggingface.co/nvidia/LocateAnything-3B) for **academic / research / non-commercial** use only. This UI is a convenience wrapper — using it does not grant any commercial rights to the model. The UI code itself is Apache-2.0 (see [LICENSE](./LICENSE)).

## Features

- **One prompt, many tasks** — detection, phrase grounding, text detection, document layout, GUI grounding, pointing.
- **Speed/quality toggle** — `fast` / `hybrid` / `slow` Parallel Box Decoding.
- **Search history** — every search (image + prompt + results) is saved and re-runnable.
- **Mobile-first** — works on your phone, including the camera.
- **GPU preflight** — tells you up front whether your card is supported.

## Requirements

- An NVIDIA GPU: **Ampere / Lovelace / Hopper / Blackwell** (RTX 30/40-series, A100, H100, Blackwell). ~**12GB+ VRAM** recommended.
- **Docker** with the NVIDIA Container Toolkit (`--gpus all`). Works on native Linux, **WSL2**, and Windows via Docker Desktop's WSL2 backend.
- Linux / WSL2 host (the model is Linux + CUDA + BF16 only).

## Quickstart

```bash
git clone git@github.com:gammahazard/locate-anything.git
cd locate-anything
cp .env.example .env
docker compose up
```

Then open <http://localhost:8080>. The first run downloads the ~6GB model into a cached volume; later runs are fast.

Not sure your card is supported? Run the preflight check first:

```bash
bash scripts/check-gpu.sh
```

### No GPU? Try the UI in mock mode

Run with the mock override — no GPU, no model download, deterministic fake boxes so you can explore the whole UI on any machine:

```bash
docker compose -f docker-compose.yml -f docker-compose.mock.yml up
```

### Remote GPU (use the UI from anywhere)

No compatible local card — or on a Mac? Run the **backend** on any Linux GPU box
(cloud instance, workstation) with `docker compose up`, expose its port, then open
the UI anywhere and set the backend URL under **System → backend url**. The frontend
talks to the backend over HTTP, so your phone or laptop drives a remote GPU.

## Development

See [CONTRIBUTING.md](./CONTRIBUTING.md) for local dev (without Docker), commit conventions, and the test suite.

## Acknowledgements

Built on NVIDIA's [LocateAnything-3B](https://research.nvidia.com/labs/lpr/locate-anything/). This project is not affiliated with or endorsed by NVIDIA.
