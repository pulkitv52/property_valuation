# AI Property Valuation PoC

This repository is organized so the ML/GIS pipeline stays easy to follow and the serving stack can be split cleanly later.

## Structure

```text
backend/        Python application code, API layer, and backend env files
frontend/       Vite + React dashboard
data/           Raw, interim, and processed datasets
models/         Trained model artifacts
reports/        Metrics, EDA, explainability, and zone outputs
notebooks/      Phase-wise exploration notebooks
logs/           Runtime logs
```

## Backend

- Source code: `backend/src/`
- API entrypoint: `backend.src.api:app`
- Backend env template: `backend/.env.example`
- Backend dependencies: `backend/requirements.txt`
- Helper scripts: `backend/scripts/`

Run the API:

```bash
conda activate valuation-poc
uvicorn backend.src.api:app --reload --host 127.0.0.1 --port 8000
```

## Frontend

- Frontend app: `frontend/`
- Frontend env template: `frontend/.env.example`

Run the dashboard:

```bash
cd frontend
npm install
npm run dev
```

## Shortcuts

You can use the root `Makefile` for common tasks:

```bash
make api
make frontend
make frontend-build
make smoke
make phase1
```

## Notes

- ML/GIS phases are implemented before the API and dashboard, following `AGENTS.md`.
- Backend application logs are written to `logs/backend/valuation_poc.log`.
- Backend console/server logs are written to `logs/backend/api-console.log`.
- Frontend dev/build logs are written to `logs/frontend/`.
- Shared artifacts stay at repo root so backend and frontend can consume the same outputs during the PoC stage.
