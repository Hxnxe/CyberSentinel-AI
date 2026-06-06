from __future__ import annotations

from datetime import datetime, timezone

from reports.action_report import build_report_markdown, parse_keywords, trim_items


def test_parse_keywords_uses_user_values_with_limit():
    keywords = parse_keywords("rce, poc\ncloud security", defaults=["fallback"], limit=2)

    assert keywords == ["rce", "poc"]


def test_parse_keywords_falls_back_to_defaults():
    keywords = parse_keywords("", defaults=["cve", "security tool", "rce"], limit=2)

    assert keywords == ["cve", "security tool"]


def test_trim_items_handles_invalid_limit():
    items = [{"name": "a"}, {"name": "b"}]

    assert trim_items(items, 0) == []
    assert trim_items(items, -1) == []
    assert trim_items(items, 1) == [{"name": "a"}]


def test_build_report_markdown_redacts_operational_details():
    markdown = build_report_markdown(
        generated_at=datetime(2026, 6, 7, 1, 0, tzinfo=timezone.utc),
        cve_candidates=[
            {
                "cve_id": "CVE-2026-1111",
                "repository_url": "https://github.com/owner/cve-repo",
                "stars": 42,
                "quality_score": 0.8,
                "quality_reasons": ["readme", "poc"],
            }
        ],
        repository_candidates=[
            {
                "name": "owner/sec-repo",
                "url": "https://github.com/owner/sec-repo",
                "stars": 100,
                "quality_score": 0.7,
                "quality_reasons": ["security_context"],
                "search_keyword": "security tool",
            }
        ],
        keywords=["security tool"],
        errors=["GitHub API rate limited"],
    )

    assert "# CyberSentinel AI GitHub Actions Report" in markdown
    assert "2026-06-07T01:00:00+00:00" in markdown
    assert "[CVE-2026-1111](https://github.com/owner/cve-repo)" in markdown
    assert "[owner/sec-repo](https://github.com/owner/sec-repo)" in markdown
    assert "security tool" in markdown
    assert "GitHub API rate limited" in markdown
    assert "github_pat_" not in markdown
    assert "ghp_" not in markdown
