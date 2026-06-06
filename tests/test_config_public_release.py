from __future__ import annotations

import importlib
import re
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_env_example_documents_public_configuration_without_real_secrets():
    env_example = (PROJECT_ROOT / ".env.example").read_text(encoding="utf-8")

    required_keys = [
        "MONITOR_INTERVAL",
        "DATABASE_PATH",
        "PRIMARY_AI_KEY",
        "PRIMARY_AI_BASE",
        "PRIMARY_AI_MODEL",
        "BACKUP_AI_CONFIGS",
        "GEMINI_AI_KEY",
        "GEMINI_AI_MODEL",
        "GEMINI_AI_BASE_URL",
        "GITHUB_TOKENS",
        "GITHUB_TOKEN",
        "BLOG_BASE_URL",
        "BLOG_TOKEN",
    ]
    for key in required_keys:
        assert re.search(rf"^{key}=", env_example, flags=re.MULTILINE), f"{key} missing from .env.example"

    forbidden_patterns = [
        r"github_pat_[A-Za-z0-9_]+",
        r"ghp_[A-Za-z0-9_]+",
        r"sk-[A-Za-z0-9_-]{20,}",
        r"-----BEGIN [A-Z ]*PRIVATE KEY-----",
    ]
    for pattern in forbidden_patterns:
        assert not re.search(pattern, env_example), f"secret-shaped value found: {pattern}"


def test_gitignore_blocks_private_and_generated_release_artifacts():
    gitignore = (PROJECT_ROOT / ".gitignore").read_text(encoding="utf-8")

    required_patterns = [
        ".env",
        ".env.*",
        "!.env.example",
        "venv/",
        ".venv/",
        "__pycache__/",
        ".pytest_cache/",
        "*.pyc",
        "*.db",
        "*.sqlite",
        "logs/",
        "results/",
        "data/",
        "build/",
        "dist/",
    ]
    for pattern in required_patterns:
        assert pattern in gitignore, f"{pattern} missing from .gitignore"


def test_config_imports_with_empty_public_environment(monkeypatch, tmp_path):
    secret_env_keys = [
        "PRIMARY_AI_KEY",
        "BACKUP_AI_CONFIGS",
        "GEMINI_AI_KEY",
        "GITHUB_TOKENS",
        "GITHUB_TOKEN",
        "BLOG_TOKEN",
    ]
    for key in secret_env_keys:
        monkeypatch.delenv(key, raising=False)
    monkeypatch.chdir(tmp_path)

    import config

    reloaded = importlib.reload(config)

    assert reloaded.settings.github_tokens == []
    assert reloaded.settings.github_token == ""
    assert reloaded.settings.blog_token == ""
    assert reloaded.settings.blog_base_url == "http://127.0.0.1"
    assert reloaded.settings.primary_ai_key == ""
    assert reloaded.settings.gemini_ai_key == ""
    assert reloaded.settings.monitor_interval > 0
    assert Path(reloaded.settings.database_path).name == "cve_database.db"
