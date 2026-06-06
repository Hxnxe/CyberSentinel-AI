# CyberSentinel AI

CyberSentinel AI is an automated security monitoring and AI analysis system. It watches CVE-related repositories, security-focused GitHub repositories, and security articles, then produces local Markdown/HTML reports. Blog publishing is optional.

## Features

- Monitor GitHub for CVE/POC-related repositories.
- Search GitHub by security keywords.
- Track configured high-priority repositories.
- Analyze findings with OpenAI-compatible providers and Gemini.
- Store monitor state in SQLite.
- Generate Markdown and HTML reports.
- Publish reports to a blog API only when `BLOG_TOKEN` is configured.

## Quick start

```bash
git clone https://github.com/Hxnxe/CyberSentinel-AI.git
cd CyberSentinel-AI

python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env
python main.py --check-config
python -m pytest -q
python main.py
```

The project can be imported and tested without private credentials. Add your own `.env` values before real monitoring.

You can also use the bootstrap script:

```bash
bash scripts/bootstrap.sh
```

## Minimal production configuration

```dotenv
GITHUB_TOKENS=["replace-with-your-github-token"]
PRIMARY_AI_KEY=replace-with-your-openai-compatible-key
PRIMARY_AI_BASE=https://api.openai.com/v1
PRIMARY_AI_MODEL=gpt-4.1-nano
```

Optional providers and integrations:

```dotenv
BACKUP_AI_CONFIGS=[]
GEMINI_AI_KEY=
BLOG_BASE_URL=http://127.0.0.1
BLOG_TOKEN=
```

When `BLOG_TOKEN` is empty, the application skips blog API calls and keeps reports local.

## Commands

Run tests:

```bash
python main.py --check-config
python -m pytest -q
```

Start the monitor:

```bash
python main.py
```

Install as an editable package:

```bash
pip install -e .
cybersentinel-ai
```

## Project layout

```text
ai/          AI clients, prompts, schemas, validation, and analysis
clients/     GitHub API client
database/    SQLAlchemy models, sessions, repositories, initialization
monitors/    CVE and GitHub repository monitors
reports/     Markdown/HTML report generation
utils/       logging, article, blacklist, blog, CSV, and Markdown helpers
scripts/     bootstrap and configuration doctor helpers
docs/        configuration, quick-start, and deployment notes
tests/       pytest suite
main.py      runtime entrypoint
config.py    environment-backed configuration
```

More documentation:

- [Configuration guide](docs/CONFIGURATION.md)
- [Deployment notes](docs/DEPLOYMENT.md)

## Private and generated files

The release excludes local secrets and runtime artifacts:

```text
.env
.env.*
venv/
.venv/
logs/
results/
data/
cve_database.db
*.db
*.sqlite
__pycache__/
.pytest_cache/
```

Never commit real tokens, generated databases, logs, reports, runtime data, or virtual environments.

## Configuration reference

| Variable | Purpose |
| --- | --- |
| `MONITOR_INTERVAL` | Monitoring interval in seconds. Default: 7200 |
| `DATABASE_PATH` | SQLite database path. Default: `cve_database.db` |
| `GITHUB_TOKENS` | JSON array of GitHub tokens |
| `GITHUB_TOKEN` | Single fallback GitHub token |
| `PRIMARY_AI_KEY` | Primary AI provider API key |
| `PRIMARY_AI_BASE` | Primary AI provider base URL |
| `PRIMARY_AI_MODEL` | Primary AI model |
| `BACKUP_AI_CONFIGS` | JSON array of backup OpenAI-compatible providers |
| `GEMINI_AI_KEY` | Gemini API key |
| `BLOG_BASE_URL` | Blog API base URL |
| `BLOG_TOKEN` | Blog API token. Leave empty to disable blog publishing |

## License

MIT. See [LICENSE](LICENSE).
