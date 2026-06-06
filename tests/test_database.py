from __future__ import annotations

from datetime import datetime, timedelta

from database.repositories import CVERepo, MonitorStateRepo, RepositoryRepo
from database.session import get_session


def test_repository_repo_daily_limit(db_session_factory):
    _, session_factory = db_session_factory

    with get_session(session_factory) as session:
        repo_repo = RepositoryRepo(session)
        assert repo_repo.check_daily_limit("owner/repo", now=datetime(2026, 2, 24, 10, 0, 0)) is True
        assert repo_repo.check_daily_limit("owner/repo", now=datetime(2026, 2, 24, 12, 0, 0)) is False
        assert repo_repo.check_daily_limit("owner/repo", now=datetime(2026, 2, 25, 9, 0, 0)) is True


def test_cve_repo_crud_and_needs_analysis(db_session_factory):
    _, session_factory = db_session_factory
    cve_id = "CVE-2026-1234"
    now = datetime.now()

    with get_session(session_factory) as session:
        cve_repo = CVERepo(session)
        cve_repo.create(
            {
                "cve_id": cve_id,
                "description": "test",
                "published_date": now,
                "last_modified": now,
                "severity": "Unknown",
            }
        )
        assert cve_repo.get_by_id(cve_id) is not None
        assert cve_repo.needs_analysis(cve_id, latest_modified=now, interval_hours=24) is True

        cve_repo.update(
            cve_id,
            {
                "last_analyzed": now,
                "last_modified": now,
            },
        )
        assert cve_repo.needs_analysis(cve_id, latest_modified=now, interval_hours=24) is False
        assert cve_repo.needs_analysis(
            cve_id,
            latest_modified=now + timedelta(hours=1),
            interval_hours=24,
        ) is True


def test_monitor_state_repo(db_session_factory):
    _, session_factory = db_session_factory

    with get_session(session_factory) as session:
        state_repo = MonitorStateRepo(session)
        state_repo.update_state("github", status="running", success=False)
        state = state_repo.get_state("github")
        assert state is not None
        assert state.status == "running"

        state_repo.update_state("github", status="success", success=True)
        state = state_repo.get_state("github")
        assert state is not None
        assert state.status == "success"
        assert state.last_success is not None
