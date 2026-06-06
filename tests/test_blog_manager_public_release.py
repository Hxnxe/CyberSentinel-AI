from __future__ import annotations

from utils.blog_manager import BlogManager


def test_blog_manager_redacts_token_for_logging(tmp_path):
    manager = BlogManager(token="super-secret-token", data_dir=str(tmp_path))

    redacted_headers = manager._headers_for_log()

    assert redacted_headers["token"] == "<redacted>"
    assert manager.headers["token"] == "super-secret-token"


def test_blog_manager_skips_create_article_without_token(monkeypatch, tmp_path):
    manager = BlogManager(token="", data_dir=str(tmp_path))
    calls = []

    def fake_post(*args, **kwargs):
        calls.append((args, kwargs))
        raise AssertionError("network should not be called without BLOG_TOKEN")

    monkeypatch.setattr("utils.blog_manager.requests.post", fake_post)

    assert manager.create_article("2026-06-07") is None
    assert calls == []
