from __future__ import annotations

from pathlib import Path
from typing import Any


Diagnostic = dict[str, str]


def _status_line(status: str, name: str, message: str) -> str:
    return f"[{status}] {name}: {message}"


def build_config_diagnostics(settings: Any) -> list[Diagnostic]:
    """Build a non-sensitive configuration report for new users."""
    diagnostics: list[Diagnostic] = []

    database_path = Path(str(settings.database_path)).expanduser()
    diagnostics.append(
        {
            "name": "database",
            "status": "OK",
            "message": f"SQLite database will be stored at {database_path}",
        }
    )

    github_tokens = list(getattr(settings, "github_tokens", []) or [])
    if github_tokens:
        diagnostics.append(
            {
                "name": "github",
                "status": "OK",
                "message": f"{len(github_tokens)} GitHub token(s) configured",
            }
        )
    else:
        diagnostics.append(
            {
                "name": "github",
                "status": "WARN",
                "message": "GITHUB_TOKENS or GITHUB_TOKEN is not configured; GitHub API rate limits will be low",
            }
        )

    has_primary_ai = bool(str(getattr(settings, "primary_ai_key", "")).strip())
    has_gemini = bool(str(getattr(settings, "gemini_ai_key", "")).strip())
    has_backup_ai = bool(getattr(settings, "backup_ai_configs", []) or [])
    if has_primary_ai or has_gemini or has_backup_ai:
        providers = []
        if has_primary_ai:
            providers.append("primary OpenAI-compatible")
        if has_backup_ai:
            providers.append("backup OpenAI-compatible")
        if has_gemini:
            providers.append("Gemini")
        diagnostics.append(
            {
                "name": "ai",
                "status": "OK",
                "message": "Configured provider(s): " + ", ".join(providers),
            }
        )
    else:
        diagnostics.append(
            {
                "name": "ai",
                "status": "WARN",
                "message": "No AI provider key configured; monitoring can start, but AI analysis calls will not produce results",
            }
        )

    if str(getattr(settings, "blog_token", "")).strip():
        diagnostics.append(
            {
                "name": "blog",
                "status": "OK",
                "message": f"Blog publishing enabled for {getattr(settings, 'blog_base_url', 'http://127.0.0.1')}",
            }
        )
    else:
        diagnostics.append(
            {
                "name": "blog",
                "status": "SKIP",
                "message": "BLOG_TOKEN is empty; blog publishing will be skipped and reports stay local",
            }
        )

    return diagnostics


def format_config_diagnostics(diagnostics: list[Diagnostic]) -> str:
    lines = ["CyberSentinel AI configuration check"]
    lines.extend(_status_line(item["status"], item["name"], item["message"]) for item in diagnostics)
    return "\n".join(lines) + "\n"
