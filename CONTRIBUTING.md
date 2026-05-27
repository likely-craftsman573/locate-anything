# Contributing

Thanks for helping out! This guide covers local development, conventions, and tests.

## Branching & PRs

- `main` is protected — no direct pushes. Open a PR.
- Branch off `main` with a short-lived, descriptive branch: `feat/...`, `fix/...`, `chore/...`, `docs/...`.
- Keep PRs focused. Fill out the PR template. CI (lint + tests + docker build) must pass.

## Commit messages — Conventional Commits

Format: `<type>(<optional scope>): <description>`

Types: `feat`, `fix`, `docs`, `style`, `refactor`, `perf`, `test`, `build`, `ci`, `chore`.

Examples:

```
feat(backend): add /api/locate endpoint
fix(frontend): scale box overlay to displayed image size
docs: document mock mode
```

These messages drive the [CHANGELOG](./CHANGELOG.md) and [SemVer](https://semver.org/) version bumps.

## Local development (without Docker)

You almost never need a GPU to develop — use **mock mode**.

### Backend

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
LA_MOCK=1 uvicorn app:app --reload --port 8000
```

Run tests + lint:

```bash
pytest
ruff check . && black --check .
```

> Real inference (`LA_MOCK=0`) requires a compatible NVIDIA GPU and downloads the ~6GB model. The full dependency set in `requirements.txt` (torch, transformers, etc.) is only needed for real mode; the test suite runs in mock mode.

### Frontend

```bash
cd frontend
npm install
npm run dev          # http://localhost:5173, proxies /api to :8000
```

Run tests + lint:

```bash
npm test
npm run lint
npm run typecheck
```

## Project layout

```
backend/    FastAPI app — wraps the model, parses boxes, stores history
frontend/   React + Vite + Tailwind UI
scripts/    helpers (GPU preflight check)
.github/    CI workflows, PR template, CODEOWNERS
```

## License

By contributing you agree your contributions are licensed under [Apache-2.0](./LICENSE).
