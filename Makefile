SHELL := /bin/bash

.PHONY: help \
	api api-start api-stop api-restart \
	frontend frontend-start frontend-stop frontend-restart frontend-build \
	start stop restart \
	smoke logs tail-log tail-backend-console tail-frontend-log \
	phase1 phase2 phase3 phase4 phase5 phase6 phase7 phase8 phase9 phase10 eda \
	inference

LOG_DIR := logs
BACKEND_PID := $(LOG_DIR)/backend/api.pid
FRONTEND_PID := $(LOG_DIR)/frontend/vite.pid

help:
	@echo "Available targets:"
	@echo "  make api             - Run FastAPI backend in foreground"
	@echo "  make api-start       - Start FastAPI backend in background"
	@echo "  make api-stop        - Stop FastAPI backend"
	@echo "  make api-restart     - Restart FastAPI backend"
	@echo "  make frontend        - Run Vite frontend in foreground"
	@echo "  make frontend-start  - Start Vite frontend in background"
	@echo "  make frontend-stop   - Stop Vite frontend"
	@echo "  make frontend-restart - Restart Vite frontend"
	@echo "  make start           - Start backend + frontend in background"
	@echo "  make stop            - Stop backend + frontend"
	@echo "  make restart         - Restart backend + frontend"
	@echo "  make frontend-build  - Build frontend for production"
	@echo "  make smoke           - Run lightweight backend smoke test"
	@echo "  make logs            - List log files"
	@echo "  make tail-log        - Tail backend log"
	@echo "  make tail-backend-console - Tail backend server console log"
	@echo "  make tail-frontend-log    - Tail frontend dev log"
	@echo "  make phase1          - Run Phase 1"
	@echo "  make phase2          - Run Phase 2"
	@echo "  make phase3          - Run Phase 3"
	@echo "  make phase4          - Run Phase 4"
	@echo "  make phase5          - Run Phase 5"
	@echo "  make phase6          - Run Phase 6"
	@echo "  make phase7          - Run Phase 7"
	@echo "  make phase8          - Run Phase 8"
	@echo "  make phase9          - Run Phase 9"
	@echo "  make phase10         - Run Phase 10 placeholder"
	@echo "  make eda             - Run EDA"
	@echo "  make inference       - Run batch inference (set INPUT=... optional OUTPUT=...)"

api:
	./backend/scripts/run_api.sh

api-start:
	@mkdir -p logs/backend
	@if [ -f "$(BACKEND_PID)" ] && kill -0 "$$(cat $(BACKEND_PID))" 2>/dev/null; then \
		echo "API already running (pid=$$(cat $(BACKEND_PID)))"; \
	else \
		echo "Starting API in background..."; \
		nohup ./backend/scripts/run_api.sh >/dev/null 2>&1 & echo $$! > "$(BACKEND_PID)"; \
		sleep 1; \
		if kill -0 "$$(cat $(BACKEND_PID))" 2>/dev/null; then \
			echo "API started (pid=$$(cat $(BACKEND_PID)))"; \
		else \
			echo "API failed to start. Check logs/backend/api-console.log"; \
			rm -f "$(BACKEND_PID)"; \
			exit 1; \
		fi; \
	fi

api-stop:
	@stopped=0; \
	if [ -f "$(BACKEND_PID)" ]; then \
		pid="$$(cat $(BACKEND_PID))"; \
		if kill -0 "$$pid" 2>/dev/null; then \
			kill "$$pid" 2>/dev/null || true; \
			sleep 1; \
			if kill -0 "$$pid" 2>/dev/null; then kill -9 "$$pid" 2>/dev/null || true; fi; \
			echo "Stopped API (pid=$$pid)"; \
			stopped=1; \
		fi; \
		rm -f "$(BACKEND_PID)"; \
	fi; \
	pkill -f "uvicorn backend.src.api:app" 2>/dev/null || true; \
	pkill -f "backend/scripts/run_api.sh" 2>/dev/null || true; \
	if [ $$stopped -eq 0 ]; then echo "API stop completed (no active tracked PID)."; fi

api-restart: api-stop api-start

frontend:
	./frontend/scripts/run_frontend.sh

frontend-start:
	@mkdir -p logs/frontend
	@if [ -f "$(FRONTEND_PID)" ] && kill -0 "$$(cat $(FRONTEND_PID))" 2>/dev/null; then \
		echo "Frontend already running (pid=$$(cat $(FRONTEND_PID)))"; \
	else \
		echo "Starting frontend in background..."; \
		nohup ./frontend/scripts/run_frontend.sh >/dev/null 2>&1 & echo $$! > "$(FRONTEND_PID)"; \
		sleep 1; \
		if kill -0 "$$(cat $(FRONTEND_PID))" 2>/dev/null; then \
			echo "Frontend started (pid=$$(cat $(FRONTEND_PID)))"; \
		else \
			echo "Frontend failed to start. Check logs/frontend/vite-dev.log"; \
			rm -f "$(FRONTEND_PID)"; \
			exit 1; \
		fi; \
	fi

frontend-stop:
	@stopped=0; \
	if [ -f "$(FRONTEND_PID)" ]; then \
		pid="$$(cat $(FRONTEND_PID))"; \
		if kill -0 "$$pid" 2>/dev/null; then \
			kill "$$pid" 2>/dev/null || true; \
			sleep 1; \
			if kill -0 "$$pid" 2>/dev/null; then kill -9 "$$pid" 2>/dev/null || true; fi; \
			echo "Stopped frontend (pid=$$pid)"; \
			stopped=1; \
		fi; \
		rm -f "$(FRONTEND_PID)"; \
	fi; \
	pkill -f "vite" 2>/dev/null || true; \
	pkill -f "frontend/scripts/run_frontend.sh" 2>/dev/null || true; \
	if [ $$stopped -eq 0 ]; then echo "Frontend stop completed (no active tracked PID)."; fi

frontend-restart: frontend-stop frontend-start

start: api-start frontend-start

stop: frontend-stop api-stop

restart: stop start

frontend-build:
	./frontend/scripts/build_frontend.sh

smoke:
	./backend/scripts/smoke_api.sh

logs:
	ls -la logs

tail-log:
	tail -n 50 -f logs/backend/valuation_poc.log

tail-backend-console:
	tail -n 50 -f logs/backend/api-console.log

tail-frontend-log:
	tail -n 50 -f logs/frontend/vite-dev.log

phase1:
	./backend/scripts/run_phase.sh run_phase_1_data_understanding

phase2:
	./backend/scripts/run_phase.sh run_phase_2_transaction_cleaning

phase3:
	./backend/scripts/run_phase.sh run_phase_3_gis_processing

phase4:
	./backend/scripts/run_phase.sh run_phase_4_data_merge

phase5:
	./backend/scripts/run_phase.sh run_phase_5_feature_engineering

phase6:
	./backend/scripts/run_phase.sh run_phase_6_model_training

phase7:
	./backend/scripts/run_phase.sh run_phase_7_evaluation

phase8:
	./backend/scripts/run_phase.sh run_phase_8_zone_clustering

phase9:
	./backend/scripts/run_phase.sh run_phase_9_explainability

phase10:
	./backend/scripts/run_phase.sh run_phase_10_mvdb_comparison

eda:
	./backend/scripts/run_phase.sh run_eda

inference:
	@if [ -z "$(INPUT)" ]; then \
		echo "Provide INPUT path. Example:"; \
		echo "make inference INPUT=data/sample_inference_input.csv OUTPUT=data/processed/inference_predictions.csv"; \
		exit 1; \
	fi
	@PYTHON_BIN=$${PYTHON_BIN:-/home/pulkitv52/miniconda3/envs/valuation-poc/bin/python}; \
	OUT=$${OUTPUT:-data/processed/inference_predictions.csv}; \
	SUMMARY_OUT=$${SUMMARY_OUTPUT:-reports/inference_summary.json}; \
	"$$PYTHON_BIN" -m backend.src.run_inference --input "$(INPUT)" --output "$$OUT" --summary-output "$$SUMMARY_OUT"
