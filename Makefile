.PHONY: install test run clean

install:
	python3 -m venv .venv
	. .venv/bin/activate && pip install -r requirements.txt

test:
	python -m pytest -q

run:
	python main.py

clean:
	rm -rf .pytest_cache __pycache__ */__pycache__ .coverage htmlcov build dist *.egg-info
