from __future__ import annotations

from datetime import datetime, timezone

from reports.action_report import ReportData
from scripts import generate_report


def test_generate_report_script_writes_artifact(monkeypatch, tmp_path):
    output = tmp_path / "artifact" / "report.md"

    def fake_collect_report_data(*, max_items, keyword_limit, keywords, include_cve, include_repositories, database_path):
        assert max_items == 3
        assert keyword_limit == 2
        assert keywords == "rce,poc"
        assert include_cve is True
        assert include_repositories is False
        assert database_path == str(tmp_path / "state.db")
        return ReportData(
            generated_at=datetime(2026, 6, 7, 1, 0, tzinfo=timezone.utc),
            keywords=["rce", "poc"],
            cve_candidates=[{"cve_id": "CVE-2026-2222", "repository_url": "https://github.com/o/r"}],
            repository_candidates=[],
            errors=[],
        )

    monkeypatch.setattr(generate_report, "collect_report_data", fake_collect_report_data)

    exit_code = generate_report.main(
        [
            "--output",
            str(output),
            "--max-items",
            "3",
            "--keyword-limit",
            "2",
            "--keywords",
            "rce,poc",
            "--skip-repositories",
            "--database-path",
            str(tmp_path / "state.db"),
        ]
    )

    assert exit_code == 0
    assert output.exists()
    assert "CVE-2026-2222" in output.read_text(encoding="utf-8")
