# Backend

This folder owns the Python side of the PoC:

- ML/GIS pipeline modules in `src/`
- FastAPI application in `src/api.py`
- backend-specific environment template in `.env.example`
- operational helper scripts in `scripts/`

## Run the API

```bash
conda activate valuation-poc
uvicorn backend.src.api:app --reload --host 127.0.0.1 --port 8000
```

Or use:

```bash
make api
```

## Run a phase script

Example:

```bash
python -m backend.src.run_phase_1_data_understanding
```

Or use:

```bash
./backend/scripts/run_phase.sh run_phase_1_data_understanding
```

## Logging

Logs are separated for easier debugging:

- application logs: `logs/backend/valuation_poc.log`
- server console logs: `logs/backend/api-console.log`
