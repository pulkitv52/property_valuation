# Frontend

This is the standalone Vite + React dashboard for the valuation PoC.

## Expected backend

The frontend talks to the FastAPI backend through:

- `VITE_API_BASE_URL`
- default: `http://127.0.0.1:8000`

## Run locally

```bash
npm install
npm run dev
```

Or from repo root:

```bash
make frontend
```

## Logging

Frontend logs are separated into:

- dev server logs: `logs/frontend/vite-dev.log`
- production build logs: `logs/frontend/vite-build.log`

## Current pages

- Overview
- Model Performance
- AI Zones
- Property Lookup
- Explainability
- MVDB Status
