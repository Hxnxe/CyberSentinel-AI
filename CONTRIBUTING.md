# Contributing

## Local setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python -m pytest -q
```

## Development rules

- Do not commit `.env`, API keys, tokens, logs, generated databases, or runtime reports.
- Keep changes focused and covered by tests when behavior changes.
- Run `python -m pytest -q` before opening a pull request.
- Use `.env.example` for documentation of configuration keys, not real secrets.

## Useful commands

```bash
python main.py --check-config
python scripts/doctor.py
python -m pytest -q
```
