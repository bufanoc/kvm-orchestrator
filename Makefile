# Default target
.DEFAULT_GOAL := run

VENV_BIN := .venv/bin
UVICORN  := $(VENV_BIN)/uvicorn

run:
	$(UVICORN) app.main:app --reload --host 0.0.0.0 --port 8000

up:
	nohup $(UVICORN) app.main:app --reload --host 0.0.0.0 --port 8000 > uvicorn.log 2>&1 & echo $$! > .uvicorn.pid; \
	echo "API started (PID $$(cat .uvicorn.pid)). Logs: uvicorn.log"

down:
	@if [ -f .uvicorn.pid ]; then \
		kill $$(cat .uvicorn.pid) && rm .uvicorn.pid && echo "API stopped"; \
	else \
		echo "No PID file (.uvicorn.pid). Is the API running via 'make up'?"; \
	fi

logs:
	@tail -f uvicorn.log

.PHONY: run up down logs
