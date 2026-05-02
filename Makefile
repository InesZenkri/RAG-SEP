.PHONY: install install-dev test lint format smoke eval api ui clean

install:
	pip install -r requirements.txt
	pip install -e .

install-dev:
	pip install -r requirements-dev.txt
	pip install -e .

test:
	pytest -q

lint:
	ruff check src tests
	mypy src

format:
	ruff format src tests
	ruff check --fix src tests

smoke:
	python -m eval.run --suite smoke --config configs/baseline.yaml

eval:
	python -m eval.run --suite full --config configs/baseline.yaml

api:
	uvicorn api.main:app --reload --port 8000

ui:
	streamlit run src/ui/app.py

clean:
	rm -rf .pytest_cache .mypy_cache .ruff_cache .llm_cache
	find . -name __pycache__ -type d -exec rm -rf {} +
