SHELL := /bin/bash

.PHONY: help api frontend frontend-build smoke logs tail-log phase1 phase2 phase3 phase4 phase5 phase6 phase7 phase8 phase9 phase10 eda

help:
	@echo "Available targets:"
	@echo "  make api             - Run FastAPI backend"
	@echo "  make frontend        - Run Vite frontend"
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

api:
	./backend/scripts/run_api.sh

frontend:
	./frontend/scripts/run_frontend.sh

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
