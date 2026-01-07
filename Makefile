# ============================================================
# FraudShield Enterprise — Makefile
# - Self-documenting (`make help`)
# - uv-first workflow (reproducible)
# - Offline-friendly: does NOT download Python toolchains
# - Starts/stops API + React frontend with PID management
# ============================================================

.DEFAULT_GOAL := help
SHELL := /bin/bash

# ---- Tools ----
UV            ?= uv
PYTHON_BIN    ?= python3.11
NPM           ?= npm

# ---- Project ----
BACKEND_DIR   ?= backend
FRONTEND_DIR  ?= frontend
PKG           ?= fraudshield

# ---- Runtime ----
HOST          ?= 0.0.0.0
API_PORT      ?= 8000
FRONTEND_PORT ?= 5173

# ---- Local env ----
VENV_DIR      ?= .venv

# ---- Run management ----
RUN_DIR       ?= .run
API_PID       := $(RUN_DIR)/api.pid
FE_PID        := $(RUN_DIR)/frontend.pid
API_LOG       := $(RUN_DIR)/api.log
FE_LOG        := $(RUN_DIR)/frontend.log

# ============================================================
# Help (self-documenting)
# Add "##" comments to targets to show in help output.
# ============================================================
.PHONY: help
help: ## Show this help (default)
	@echo ""
	@echo "FraudShield Enterprise — Commands"
	@echo "--------------------------------"
	@awk 'BEGIN {FS = ":.*##"} \
		/^[a-zA-Z0-9_.-]+:.*##/ {printf "  \033[36m%-22s\033[0m %s\n", $$1, $$2} \
	' $(MAKEFILE_LIST)
	@echo ""

# ============================================================
# Environment / Install
# ============================================================
.PHONY: uv-venv
uv-venv: ## Create uv virtualenv (offline-friendly)
	@$(UV) venv --python $(PYTHON_BIN)

.PHONY: install-backend
install-backend: uv-venv ## Install backend (core API + decisioning)
	@$(UV) pip install -e $(BACKEND_DIR)

.PHONY: install-ops
install-ops: uv-venv ## Install backend ops extras (agents)
	@$(UV) pip install -e "$(BACKEND_DIR)[ops]"

.PHONY: install-ml
install-ml: uv-venv ## Install backend ML extras (sklearn)
	@$(UV) pip install -e "$(BACKEND_DIR)[ml]"

.PHONY: dev
dev: uv-venv ## Install backend dev extras (tests + lint)
	@$(UV) pip install -e "$(BACKEND_DIR)[dev]"

.PHONY: install-frontend
install-frontend: ## Install frontend deps (npm)
	@cd $(FRONTEND_DIR) && $(NPM) install

.PHONY: install
install: install-backend install-frontend ## Install backend + frontend

# ============================================================
# Quality
# ============================================================
.PHONY: test
test: ## Run backend tests
	@PYTHONPATH=$(BACKEND_DIR)/src $(UV) run pytest -q

.PHONY: lint
lint: ## Lint backend (ruff) (requires dev)
	@$(UV) run ruff check $(BACKEND_DIR)

.PHONY: lint-fix
lint-fix: ## Lint + auto-fix backend (ruff) (requires dev)
	@$(UV) run ruff check --fix $(BACKEND_DIR)

# ============================================================
# Internal helpers
# ============================================================
.PHONY: _run-dir
_run-dir:
	@mkdir -p $(RUN_DIR)

.PHONY: _kill-pid
_kill-pid:
	@PID_FILE="$(PIDFILE)"; \
	if [ -f "$$PID_FILE" ]; then \
		PID="$$(cat $$PID_FILE 2>/dev/null || true)"; \
		if [ -n "$$PID" ] && kill -0 "$$PID" >/dev/null 2>&1; then \
			echo "Stopping $$PID_FILE (pid=$$PID) ..."; \
			kill "$$PID" >/dev/null 2>&1 || true; \
			sleep 1; \
			kill -9 "$$PID" >/dev/null 2>&1 || true; \
		fi; \
		rm -f "$$PID_FILE"; \
	fi

.PHONY: _status-pid
_status-pid:
	@PID_FILE="$(PIDFILE)"; \
	NAME="$(NAME)"; \
	if [ -f "$$PID_FILE" ]; then \
		PID="$$(cat $$PID_FILE 2>/dev/null || true)"; \
		if [ -n "$$PID" ] && kill -0 "$$PID" >/dev/null 2>&1; then \
			echo "✅ $$NAME running (pid=$$PID)"; \
		else \
			echo "⚠️  $$NAME pid file exists but process not running"; \
		fi; \
	else \
		echo "⛔ $$NAME not running"; \
	fi

# ============================================================
# Run (foreground helpers)
# ============================================================
.PHONY: run-api
run-api: ## Run FastAPI in foreground (hot reload)
	@$(UV) run uvicorn $(PKG).api.main:app --host $(HOST) --port $(API_PORT) --reload

.PHONY: run-frontend
run-frontend: ## Run React frontend in foreground (Vite)
	@cd $(FRONTEND_DIR) && $(NPM) run dev -- --host --port $(FRONTEND_PORT)

# typo-friendly alias (you hit this)
.PHONY: run-fronend
run-fronend: run-frontend ## Alias (typo): run frontend

# ============================================================
# Run (background, managed)
# ============================================================
.PHONY: start-api
start-api: _run-dir ## Start API in background (writes .run/api.pid + .run/api.log)
	@if [ -f "$(API_PID)" ] && kill -0 "$$(cat $(API_PID) 2>/dev/null)" >/dev/null 2>&1; then \
		echo "✅ API already running (pid=$$(cat $(API_PID)))"; \
	else \
		echo "Starting API on :$(API_PORT) ..."; \
		nohup $(UV) run uvicorn $(PKG).api.main:app --host $(HOST) --port $(API_PORT) --reload \
			> $(API_LOG) 2>&1 & echo $$! > $(API_PID); \
		echo "✅ API started (pid=$$(cat $(API_PID))) log=$(API_LOG)"; \
	fi

.PHONY: start-frontend
start-frontend: _run-dir ## Start frontend in background (writes .run/frontend.pid + .run/frontend.log)
	@if [ -f "$(FE_PID)" ] && kill -0 "$$(cat $(FE_PID) 2>/dev/null)" >/dev/null 2>&1; then \
		echo "✅ Frontend already running (pid=$$(cat $(FE_PID)))"; \
	else \
		echo "Starting frontend on :$(FRONTEND_PORT) ..."; \
		cd $(FRONTEND_DIR) && nohup $(NPM) run dev -- --host --port $(FRONTEND_PORT) \
			> ../$(FE_LOG) 2>&1 & echo $$! > ../$(FE_PID); \
		echo "✅ Frontend started (pid=$$(cat $(FE_PID))) log=$(FE_LOG)"; \
	fi

.PHONY: run
run: start-api start-frontend ## Start API + frontend (background)
	@echo ""
	@echo "✅ FraudShield is starting/running:"
	@echo "  API:      http://localhost:$(API_PORT)"
	@echo "  Frontend: http://localhost:$(FRONTEND_PORT)"
	@echo ""
	@echo "Use:"
	@echo "  make status"
	@echo "  make logs"
	@echo "  make stop"
	@echo ""

.PHONY: stop
stop: ## Stop API + frontend (kills PID processes)
	@$(MAKE) _kill-pid PIDFILE="$(API_PID)"
	@$(MAKE) _kill-pid PIDFILE="$(FE_PID)"
	@echo "✅ Stopped (if they were running)."

.PHONY: status
status: ## Show whether API/frontend are running
	@$(MAKE) _status-pid NAME="API" PIDFILE="$(API_PID)"
	@$(MAKE) _status-pid NAME="Frontend" PIDFILE="$(FE_PID)"
	@echo ""
	@echo "Ports:"
	@command -v lsof >/dev/null 2>&1 && (lsof -i :$(API_PORT) -sTCP:LISTEN 2>/dev/null || true) || true
	@command -v lsof >/dev/null 2>&1 && (lsof -i :$(FRONTEND_PORT) -sTCP:LISTEN 2>/dev/null || true) || true

.PHONY: logs
logs: ## Tail API + frontend logs
	@echo "Tailing logs (Ctrl+C to exit) ..."
	@touch $(API_LOG) $(FE_LOG)
	@tail -n 200 -f $(API_LOG) $(FE_LOG)

# ============================================================
# Build (frontend)
# ============================================================
.PHONY: build-frontend
build-frontend: ## Build React frontend (Vite)
	@cd $(FRONTEND_DIR) && $(NPM) run build

# ============================================================
# ML
# ============================================================
.PHONY: train
train: ## Train + register demo sklearn model (requires install-ml)
	@$(UV) run python -m $(PKG).modeling.train_supervised

# ============================================================
# Cleanup
# ============================================================
.PHONY: clean
clean: ## Remove virtualenv and build artifacts
	@rm -rf $(RUN_DIR) \
		$(VENV_DIR) venv \
		$(BACKEND_DIR)/*.egg-info dist build .pytest_cache .ruff_cache \
		$(FRONTEND_DIR)/node_modules $(FRONTEND_DIR)/dist \
		artifacts logs reports \
		*.db *.sqlite
