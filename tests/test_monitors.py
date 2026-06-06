from __future__ import annotations

from monitors.cve_monitor import CVEMonitor
from monitors.github_monitor import GithubMonitor
from utils.blacklist_manager import BlacklistManager


class FakeGithubClient:
    def __init__(self):
        self.repo_details = {
            "owner/watched-repo": {
                "html_url": "https://github.com/owner/watched-repo",
                "description": "watched",
                "pushed_at": "2026-02-24T10:00:00Z",
            }
        }

    def search_repos(self, query, sort="updated", order="desc", page=1, per_page=30):
        if "CVE-202" in query:
            return {
                "items": [
                    {
                        "name": "CVE-2026-1111-poc",
                        "full_name": "owner/cve-repo",
                        "description": "poc for cve",
                        "owner": {"login": "owner"},
                        "pushed_at": "2026-02-24T09:00:00Z",
                        "html_url": "https://github.com/owner/cve-repo",
                        "stargazers_count": 5,
                    }
                ]
            }
        return {
            "items": [
                {
                    "name": "sec-repo",
                    "full_name": "owner/sec-repo",
                    "description": "security tool",
                    "owner": {"login": "owner"},
                    "pushed_at": "2026-02-24T08:00:00Z",
                    "html_url": "https://github.com/owner/sec-repo",
                    "stargazers_count": 20,
                }
            ]
        }

    def get_commits(self, repo_full_name, since=None, per_page=10):
        return [{"sha": "abc123", "url": f"https://api.github.com/repos/{repo_full_name}/commits/abc123"}]

    def get_commit_detail(self, repo_full_name, sha_or_url):
        return {
            "sha": "abc123",
            "commit": {"message": "fix", "author": {"name": "dev", "date": "2026-02-24T10:00:00Z"}},
            "files": [
                {
                    "filename": "poc.py",
                    "status": "modified",
                    "additions": 10,
                    "deletions": 1,
                    "changes": 11,
                    "patch": "print('poc')",
                }
            ],
        }

    def get_contents(self, repo_full_name, path=""):
        return [
            {
                "type": "file",
                "name": "README.md",
                "path": "README.md",
                "url": "https://api.github.com/repos/owner/cve-repo/contents/README.md",
            }
        ]

    def get_json_by_url(self, url):
        import base64

        content = base64.b64encode("CVE-2026-1111 poc".encode("utf-8")).decode("utf-8")
        return {"content": content}

    def get_repository(self, repo_full_name):
        return self.repo_details.get(repo_full_name)

    def get_readme(self, repo_full_name):
        return "# README"


class DuplicateKeywordClient(FakeGithubClient):
    def search_repos(self, query, sort="updated", order="desc", page=1, per_page=30):
        if "CVE-202" in query:
            return super().search_repos(query, sort=sort, order=order, page=page, per_page=per_page)
        return {
            "items": [
                {
                    "name": "shared-repo",
                    "full_name": "owner/shared-repo",
                    "description": "security tool with poc",
                    "owner": {"login": "owner"},
                    "pushed_at": "2026-02-24T08:00:00Z",
                    "html_url": "https://github.com/owner/shared-repo",
                    "stargazers_count": 30,
                }
            ]
        }


class LowQualityClient(FakeGithubClient):
    def search_repos(self, query, sort="updated", order="desc", page=1, per_page=30):
        if "CVE-202" in query:
            return super().search_repos(query, sort=sort, order=order, page=page, per_page=per_page)
        return {
            "items": [
                {
                    "name": "demo",
                    "full_name": "owner/demo",
                    "description": "misc project",
                    "owner": {"login": "owner"},
                    "pushed_at": "2026-02-24T08:00:00Z",
                    "html_url": "https://github.com/owner/demo",
                    "stargazers_count": 0,
                }
            ]
        }

    def get_commit_detail(self, repo_full_name, sha_or_url):
        return {
            "sha": "abc123",
            "commit": {"message": "update", "author": {"name": "dev", "date": "2026-02-24T10:00:00Z"}},
            "files": [
                {
                    "filename": "image.png",
                    "status": "modified",
                    "additions": 1,
                    "deletions": 0,
                    "changes": 1,
                    "patch": "",
                }
            ],
        }


class WatchedLowSignalClient(FakeGithubClient):
    def __init__(self):
        super().__init__()
        self.repo_details = {
            "owner/watched-repo": {
                "html_url": "https://github.com/owner/watched-repo",
                "description": "monitor target",
                "pushed_at": "2026-02-24T10:00:00Z",
                "stargazers_count": 0,
            }
        }

    def get_commit_detail(self, repo_full_name, sha_or_url):
        return {
            "sha": "abc123",
            "commit": {"message": "minor", "author": {"name": "dev", "date": "2026-02-24T10:00:00Z"}},
            "files": [
                {
                    "filename": "notes.bin",
                    "status": "modified",
                    "additions": 1,
                    "deletions": 0,
                    "changes": 1,
                    "patch": "",
                }
            ],
        }

    def search_repos(self, query, sort="updated", order="desc", page=1, per_page=30):
        if "CVE-202" in query:
            return super().search_repos(query, sort=sort, order=order, page=page, per_page=per_page)
        return {"items": []}


def test_cve_monitor_fetch_and_process(db_session_factory, tmp_path):
    engine, session_factory = db_session_factory
    blacklist = BlacklistManager(base_dir=tmp_path / "blacklist")
    monitor = CVEMonitor(
        engine,
        github_client=FakeGithubClient(),
        blacklist_manager=blacklist,
        session_factory=session_factory,
    )

    fetched = monitor.fetch_latest_cves()
    assert fetched
    assert fetched[0]["cve_id"].startswith("CVE-2026-")
    assert "quality_score" in fetched[0]
    assert "quality_reasons" in fetched[0]
    assert "fingerprint" in fetched[0]

    to_analyze = monitor.process_cve_data(fetched)
    assert to_analyze
    assert to_analyze[0]["repository_url"].startswith("https://github.com/")


def test_github_monitor_run(db_session_factory, tmp_path):
    engine, session_factory = db_session_factory
    blacklist = BlacklistManager(base_dir=tmp_path / "blacklist2")
    monitor = GithubMonitor(
        engine,
        github_client=FakeGithubClient(),
        blacklist_manager=blacklist,
        session_factory=session_factory,
        keywords=["security tool"],
        watched_repositories=["owner/watched-repo"],
    )

    repos = monitor.run(interval=1)
    assert isinstance(repos, list)
    assert repos
    names = {item.get("name") for item in repos}
    assert "owner/watched-repo" in names or "owner/sec-repo" in names
    for repo in repos:
        assert "quality_score" in repo
        assert "quality_reasons" in repo
        assert "fingerprint" in repo


def test_github_monitor_deduplicates_cross_keywords(db_session_factory, tmp_path):
    engine, session_factory = db_session_factory
    blacklist = BlacklistManager(base_dir=tmp_path / "blacklist3")
    monitor = GithubMonitor(
        engine,
        github_client=DuplicateKeywordClient(),
        blacklist_manager=blacklist,
        session_factory=session_factory,
        keywords=["security tool", "security tool duplicate"],
        watched_repositories=[],
    )

    repos = monitor.run(interval=1)
    names = [item.get("name") for item in repos]
    assert names.count("owner/shared-repo") == 1


def test_github_monitor_filters_low_quality_candidate(db_session_factory, tmp_path):
    engine, session_factory = db_session_factory
    blacklist = BlacklistManager(base_dir=tmp_path / "blacklist4")
    monitor = GithubMonitor(
        engine,
        github_client=LowQualityClient(),
        blacklist_manager=blacklist,
        session_factory=session_factory,
        keywords=["totallyrandom"],
        watched_repositories=[],
    )

    repos = monitor.run(interval=1)
    assert repos == []


def test_github_monitor_watched_repo_bypass_threshold(db_session_factory, tmp_path):
    engine, session_factory = db_session_factory
    blacklist = BlacklistManager(base_dir=tmp_path / "blacklist5")
    monitor = GithubMonitor(
        engine,
        github_client=WatchedLowSignalClient(),
        blacklist_manager=blacklist,
        session_factory=session_factory,
        keywords=[],
        watched_repositories=["owner/watched-repo"],
    )

    repos = monitor.run(interval=1)
    assert len(repos) == 1
    assert repos[0]["is_watched"] is True
    assert "watched_repository_bypass" in repos[0]["quality_reasons"]
