from __future__ import annotations

import time
from typing import Any

from clients.github_client import GithubClient


class FakeResponse:
    def __init__(self, status_code: int, data: Any = None, headers: dict[str, str] | None = None):
        self.status_code = status_code
        self._data = data if data is not None else {}
        self.headers = headers or {}
        self.text = ""

    def json(self):
        return self._data


def test_token_rotation_on_403(monkeypatch):
    client = GithubClient(tokens=["t1", "t2"], max_retries=3)
    calls = []

    responses = iter(
        [
            FakeResponse(403, data={"message": "rate limited"}, headers={"X-RateLimit-Reset": str(int(time.time() + 10))}),
            FakeResponse(
                200,
                data={"items": [{"full_name": "owner/repo"}]},
                headers={"X-RateLimit-Remaining": "4999", "X-RateLimit-Reset": str(int(time.time() + 3600))},
            ),
        ]
    )

    def fake_get(url, headers=None, params=None, timeout=None):
        calls.append(headers.get("Authorization", ""))
        return next(responses)

    monkeypatch.setattr(client.session, "get", fake_get)
    data = client.search_repos("cve")
    assert data is not None
    assert data.get("items")
    assert len(calls) >= 2
    assert calls[0] != calls[1]


def test_401_cooldown_and_retry_with_second_token(monkeypatch):
    client = GithubClient(tokens=["bad-token", "good-token"], max_retries=3)

    responses = iter(
        [
            FakeResponse(401, data={"message": "bad credentials"}),
            FakeResponse(200, data={"resources": {"core": {"remaining": 1000}}}),
        ]
    )

    def fake_get(url, headers=None, params=None, timeout=None):
        return next(responses)

    monkeypatch.setattr(client.session, "get", fake_get)
    result = client.get_rate_limit()
    assert result is not None
