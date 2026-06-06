# Configuration Guide

CyberSentinel AI is configured through environment variables. The recommended local flow is:

```bash
cp .env.example .env
python main.py --check-config
```

## Runtime

| Variable | Default | Description |
| --- | --- | --- |
| `MONITOR_INTERVAL` | `7200` | Seconds between monitoring loops. |
| `DATABASE_PATH` | `cve_database.db` | SQLite database path. Relative paths are resolved from the project root. |

## GitHub

Use a token for real monitoring; unauthenticated requests are rate-limited.

```dotenv
GITHUB_TOKENS=["replace-with-token-1","replace-with-token-2"]
GITHUB_TOKEN=
```

`GITHUB_TOKENS` takes priority. `GITHUB_TOKEN` is a single-token fallback.

## AI providers

Primary OpenAI-compatible provider:

```dotenv
PRIMARY_AI_KEY=
PRIMARY_AI_BASE=https://api.openai.com/v1
PRIMARY_AI_MODEL=gpt-4.1-nano
```

Backup OpenAI-compatible providers:

```dotenv
BACKUP_AI_CONFIGS=[{"api_key":"replace-with-key","api_base":"https://api.example.com/v1","model":"model-name"}]
```

Gemini fallback:

```dotenv
GEMINI_AI_KEY=
GEMINI_AI_MODEL=gemini-2.5-flash
GEMINI_AI_BASE_URL=https://generativelanguage.googleapis.com
```

At least one AI provider key is needed for AI analysis. Tests and configuration checks can run without AI keys.

## Blog publishing

Blog publishing is optional:

```dotenv
BLOG_BASE_URL=http://127.0.0.1
BLOG_TOKEN=
```

If `BLOG_TOKEN` is empty, blog API calls are skipped and reports stay local.
