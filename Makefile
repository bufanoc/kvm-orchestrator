# Default target when you just run `make`
.DEFAULT_GOAL := run

# Run the dev server
run:
	uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# (optional) Lint + format placeholders; add tools later if you want
fmt:
	@echo "Add ruff/black later (optional)."

# (optional) Test placeholder; we’ll add pytest later
test:
	@echo "No tests yet."
