from __future__ import annotations

import main


def test_main_check_config_prints_diagnostics(monkeypatch, capsys, tmp_path):
    monkeypatch.chdir(tmp_path)

    exit_code = main.main(["--check-config"])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "CyberSentinel AI configuration check" in output
    assert "database" in output
    assert "github" in output
    assert "ai" in output
    assert "blog" in output


def test_main_version_prints_version(capsys):
    exit_code = main.main(["--version"])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "CyberSentinel AI" in output
