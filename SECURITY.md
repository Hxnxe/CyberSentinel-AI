# Security Policy

## Secret handling

CyberSentinel AI reads credentials from `.env` or environment variables. The public repository must never contain:

- GitHub tokens;
- OpenAI-compatible API keys;
- Gemini API keys;
- blog publishing tokens;
- private keys;
- generated SQLite databases;
- logs or runtime reports that may include operational data.

Before publishing changes, run:

```bash
python -m pytest -q
python main.py --check-config
```

Also inspect `git status --short` and confirm that `.env`, `logs/`, `results/`, `data/`, `*.db`, and virtual environments are not staged.

## Reporting issues

If you find a security issue, do not include real secrets in public issue text. Describe the affected component, expected behavior, and reproduction steps using placeholder credentials.
