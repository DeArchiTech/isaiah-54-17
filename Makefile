# isaiah-54-17 — an AI scripture-study app that verifies every citation.
.DEFAULT_GOAL := help
PY ?= python3
VENV := .venv
BIN  := $(VENV)/bin

help: ## show this help
	@grep -hE '^[a-z-]+:.*?## ' $(MAKEFILE_LIST) \
	 | awk -F':.*?## ' '{printf "  \033[36m%-12s\033[0m %s\n", $$1, $$2}'

setup: ## create the venv, install deps, install the pre-commit hook
	$(PY) -m venv $(VENV)
	$(BIN)/pip install -q --upgrade pip
	$(BIN)/pip install -q -r api/requirements.txt
	cd web && npm install --silent
	@$(MAKE) --no-print-directory hooks
	@test -f .env || (cp .env.example .env && echo "  created .env — put your key in it")
	@echo "setup done. next: make ingest"

ingest: ## download the public-domain corpus and build the index (~12 min once)
	cd api && ../$(BIN)/python -m berean.ingest

hooks: ## install the secret-scanning pre-commit hook
	@mkdir -p .git/hooks 2>/dev/null || true
	@if [ -d .git ]; then \
	  ln -sf ../../scripts/preflight.sh .git/hooks/pre-commit; \
	  echo "  pre-commit hook installed"; \
	else echo "  (no .git yet — run again after git init)"; fi

check: ## run the secret scan against what is staged
	@./scripts/preflight.sh

test: ## run the test suite
	cd api && ../$(BIN)/python -m pytest tests -q

api: ## run the backend on :8000
	cd api && ../$(BIN)/python -m uvicorn app:app --reload --port 8000

web: ## run the frontend on :5173
	cd web && npm run dev

.PHONY: help setup ingest hooks check test api web
