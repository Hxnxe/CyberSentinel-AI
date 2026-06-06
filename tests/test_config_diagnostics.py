from __future__ import annotations

from config import Settings
from utils.config_diagnostics import build_config_diagnostics, format_config_diagnostics


def test_config_diagnostics_warns_without_credentials(tmp_path):
    settings = Settings(
        database_path=str(tmp_path / "state" / "cve_database.db"),
        github_tokens=[],
        github_token="",
        primary_ai_key="",
        backup_ai_configs=[],
        gemini_ai_key="",
        blog_token="",
    )

    diagnostics = build_config_diagnostics(settings)
    formatted = format_config_diagnostics(diagnostics)

    statuses = {item["name"]: item["status"] for item in diagnostics}
    assert statuses["database"] == "OK"
    assert statuses["github"] == "WARN"
    assert statuses["ai"] == "WARN"
    assert statuses["blog"] == "SKIP"
    assert "cve_database.db" in formatted
    assert "github_pat_" not in formatted
    assert "BLOG_TOKEN" in formatted


def test_config_diagnostics_reports_configured_services(tmp_path):
    settings = Settings(
        database_path=str(tmp_path / "cve_database.db"),
        github_tokens=["ghp_example_placeholder"],
        primary_ai_key="primary-placeholder",
        primary_ai_base="https://api.example.com/v1",
        primary_ai_model="example-model",
        backup_ai_configs=[],
        gemini_ai_key="",
        blog_base_url="https://blog.example.com",
        blog_token="blog-placeholder",
    )

    diagnostics = build_config_diagnostics(settings)
    statuses = {item["name"]: item["status"] for item in diagnostics}

    assert statuses["github"] == "OK"
    assert statuses["ai"] == "OK"
    assert statuses["blog"] == "OK"
