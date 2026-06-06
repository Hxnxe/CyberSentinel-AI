from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy.orm import Session

from database.models import CVERecord, MonitorState, Repository


class CVERepo:
    """CVE 相关数据访问封装。"""

    def __init__(self, session: Session) -> None:
        self.session = session

    def get_by_id(self, cve_id: str) -> CVERecord | None:
        return self.session.query(CVERecord).filter_by(cve_id=cve_id).first()

    def create(self, data: dict[str, Any]) -> CVERecord:
        record = CVERecord(**data)
        self.session.add(record)
        self.session.flush()
        return record

    def update(self, cve_id: str, data: dict[str, Any]) -> CVERecord | None:
        record = self.get_by_id(cve_id)
        if not record:
            return None
        for key, value in data.items():
            if hasattr(record, key):
                setattr(record, key, value)
        self.session.flush()
        return record

    def needs_analysis(
        self,
        cve_id: str,
        latest_modified: datetime | None = None,
        interval_hours: int = 24,
    ) -> bool:
        record = self.get_by_id(cve_id)
        if not record:
            return True
        if record.last_analyzed is None:
            return True
        if latest_modified and record.last_modified != latest_modified:
            return True
        elapsed = datetime.now() - record.last_analyzed
        return elapsed.total_seconds() >= interval_hours * 3600


class RepositoryRepo:
    """仓库相关数据访问封装。"""

    def __init__(self, session: Session) -> None:
        self.session = session

    def get_by_name(self, name: str) -> Repository | None:
        return self.session.query(Repository).filter_by(name=name).first()

    def create(self, data: dict[str, Any]) -> Repository:
        record = Repository(**data)
        self.session.add(record)
        self.session.flush()
        return record

    def update_analysis(self, name: str, data: dict[str, Any]) -> Repository | None:
        record = self.get_by_name(name)
        if not record:
            return None
        for key, value in data.items():
            if hasattr(record, key):
                setattr(record, key, value)
        if "last_analyzed" not in data:
            record.last_analyzed = datetime.now()
        self.session.flush()
        return record

    def check_daily_limit(self, repo_name: str, now: datetime | None = None) -> bool:
        if not repo_name:
            return True

        current_time = now or datetime.now()
        record = self.get_by_name(repo_name)

        if not record:
            self.create(
                {
                    "name": repo_name,
                    "last_fetched": current_time,
                    "push_count": 1,
                }
            )
            return True

        if record.last_fetched and record.last_fetched.date() == current_time.date():
            return False

        if record.last_fetched and record.last_fetched.date() != current_time.date():
            record.push_count = 0

        record.last_fetched = current_time
        record.push_count = (record.push_count or 0) + 1
        self.session.flush()
        return True


class MonitorStateRepo:
    """监控状态数据访问封装。"""

    def __init__(self, session: Session) -> None:
        self.session = session

    def get_state(self, monitor_type: str) -> MonitorState | None:
        return self.session.query(MonitorState).filter_by(monitor_type=monitor_type).first()

    def update_state(
        self,
        monitor_type: str,
        status: str,
        error_message: str | None = None,
        *,
        success: bool = False,
        last_run: datetime | None = None,
    ) -> MonitorState:
        record = self.get_state(monitor_type)
        if not record:
            record = MonitorState(monitor_type=monitor_type)
            self.session.add(record)

        record.status = status
        record.error_message = error_message
        record.last_run = last_run or datetime.now()
        if success:
            record.last_success = record.last_run
        self.session.flush()
        return record
