# CyberSentinel AI

CyberSentinel AI is an automated security monitoring system for tracking CVE-related repositories, security-focused GitHub projects, and security articles. It can analyze collected data with AI providers, generate Markdown/HTML reports, and optionally publish daily reports to a blog service.

- 中文说明: [README_ZH.md](README_ZH.md)
- English guide: [README_EN.md](README_EN.md)

## What it does

- Monitors GitHub for CVE proof-of-concept repositories and security tools.
- Tracks configured high-priority repositories.
- Uses OpenAI-compatible providers and Gemini for AI-assisted triage.
- Stores monitor state in SQLite.
- Generates local Markdown and HTML reports.
- Optionally publishes reports to a blog API when `BLOG_TOKEN` is configured.
- Generates GitHub Actions Markdown report artifacts without committing runtime data.

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

The project imports and tests without private credentials. Real monitoring needs your own `.env` values.

You can also let the bootstrap script perform the setup:

```bash
bash scripts/bootstrap.sh
```

## Required configuration for real monitoring

Edit `.env` after copying `.env.example`:

```dotenv
GITHUB_TOKENS=["replace-with-your-github-token"]
PRIMARY_AI_KEY=replace-with-your-openai-compatible-key
PRIMARY_AI_BASE=https://api.openai.com/v1
PRIMARY_AI_MODEL=gpt-4.1-nano
```

Gemini and blog publishing are optional:

```dotenv
GEMINI_AI_KEY=
BLOG_BASE_URL=http://127.0.0.1
BLOG_TOKEN=
```

If `BLOG_TOKEN` is empty, the system keeps reports local and skips blog API calls.

## Generated files

Runtime files are intentionally ignored by git:

```text
.env
cve_database.db
logs/
results/
data/
venv/
.venv/
__pycache__/
.pytest_cache/
```

Do not commit generated databases, logs, reports, or private credentials.

## Development checks

```bash
python main.py --check-config
python -m pytest -q
```

The public release includes tests for:

- configuration loading without private credentials;
- `.env.example` completeness and sanitization;
- `.gitignore` protection for private/generated files;
- GitHub token rotation behavior;
- monitor quality filtering;
- database persistence;
- optional blog publishing behavior.

## Project layout

```text
ai/          AI client, prompts, schemas, result validation, analysis logic
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

## More documentation

- [GitHub Actions reports](docs/GITHUB_ACTIONS_REPORTS.md)
- [Configuration guide](docs/CONFIGURATION.md)
- [Deployment notes](docs/DEPLOYMENT.md)

## License

MIT. See [LICENSE](LICENSE).
