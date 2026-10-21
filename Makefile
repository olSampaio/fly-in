PYTHON ?= python3
MAP ?=

.PHONY: install run debug clean lint lint-strict

install:
	$(PYTHON) -m pip install -r requirements.txt

run:
	@if [ -z "$(MAP)" ]; then \
		echo "Usage: make run MAP=<map_file>"; \
		exit 1; \
	fi
	$(PYTHON) main.py "$(MAP)"

debug:
	@if [ -z "$(MAP)" ]; then \
		echo "Usage: make debug MAP=<map_file>"; \
		exit 1; \
	fi
	$(PYTHON) -m pdb main.py "$(MAP)"

clean:
	find . -type d \( -name .git -o -name .venv -o -name venv \) -prune -o -type d \( -name __pycache__ -o -name .mypy_cache -o -name .pytest_cache \) -exec rm -rf {} +

lint:
	flake8 .
	mypy . --warn-return-any --warn-unused-ignores --ignore-missing-imports --disallow-untyped-defs --check-untyped-defs

lint-strict:
	flake8 .
	mypy . --strict
