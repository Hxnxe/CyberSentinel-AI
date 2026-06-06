from __future__ import annotations

from ai.llm_client import LLMClient
from ai.result_validator import validate_cve_result


def test_llm_client_fallback_to_backup(monkeypatch):
    llm_client = LLMClient(
        gemini_config={},
        primary_openai_config={"api_key": "k1", "api_base": "https://example1.com/v1", "model": "primary-model"},
        backup_openai_configs=[
            {"api_key": "k2", "api_base": "https://example2.com/v1", "model": "backup-model"},
        ],
    )

    monkeypatch.setattr(llm_client, "_call_gemini", lambda **kwargs: None)

    def fake_openai_call(client, config, **kwargs):
        if config["model"] == "primary-model":
            return None
        llm_client._set_last_used_info(
            provider="openai",
            model=config["model"],
            api_base=config["api_base"],
            is_backup=True,
        )
        return {"ok": True}

    monkeypatch.setattr(llm_client, "_call_openai_client", fake_openai_call)
    result = llm_client.generate_json(system_prompt="sys", user_prompt="user")
    assert result == {"ok": True}
    assert llm_client.last_used_info["is_backup"] is True
    assert llm_client.last_used_info["model"] == "backup-model"


def test_validate_cve_result_normalization():
    raw_result = {
        "summary": "test",
        "risk_level": "high",
        "key_points": ["a"],
        "technical_details": ["b"],
        "affected_components": ["c"],
        "is_valuable": True,
        "value_reason": "ok",
        "exploit_status": "POC可用",
    }
    cve_data = {
        "cve_id": "CVE-2026-1000",
        "repository_url": "https://github.com/owner/repo",
        "published_date": "2026-02-24",
        "last_modified": "2026-02-24",
        "stars": 10,
    }
    result = validate_cve_result(raw_result, cve_data)
    assert result is not None
    assert result["risk_level"] == "HIGH"
    assert result["cve_id"] == "CVE-2026-1000"
