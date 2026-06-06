from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """数据库模型基类。"""


class Repository(Base):
    """仓库监控记录。"""

    __tablename__ = "repositories"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    url: Mapped[str | None] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(Text)
    stars: Mapped[int | None] = mapped_column(Integer, default=0)
    last_update: Mapped[datetime | None] = mapped_column(DateTime)
    created_at: Mapped[datetime | None] = mapped_column(DateTime, default=datetime.now)
    is_valuable: Mapped[bool | None] = mapped_column(Boolean, default=True)
    ai_summary: Mapped[str | None] = mapped_column(Text)
    last_analyzed: Mapped[datetime | None] = mapped_column(DateTime)
    last_fetched: Mapped[datetime | None] = mapped_column(DateTime)
    push_count: Mapped[int | None] = mapped_column(Integer, default=0)

    def __repr__(self) -> str:
        return (
            f"Repository(id={self.id!r}, name={self.name!r}, "
            f"stars={self.stars!r}, last_update={self.last_update!r})"
        )


class CVERecord(Base):
    """CVE 监控记录。"""

    __tablename__ = "cve_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    cve_id: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    published_date: Mapped[datetime | None] = mapped_column(DateTime)
    last_modified: Mapped[datetime | None] = mapped_column(DateTime)
    repository_url: Mapped[str | None] = mapped_column(String(255))
    created_at: Mapped[datetime | None] = mapped_column(DateTime, default=datetime.now)
    severity: Mapped[str | None] = mapped_column(String(50))
    ai_summary: Mapped[str | None] = mapped_column(Text)
    last_analyzed: Mapped[datetime | None] = mapped_column(DateTime)
    stars: Mapped[int | None] = mapped_column(Integer, default=0)
    last_fetched: Mapped[datetime | None] = mapped_column(DateTime)

    def __repr__(self) -> str:
        return (
            f"CVERecord(id={self.id!r}, cve_id={self.cve_id!r}, "
            f"severity={self.severity!r}, last_modified={self.last_modified!r})"
        )


class MonitorState(Base):
    """监控器运行状态。"""

    __tablename__ = "monitor_state"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    monitor_type: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    last_run: Mapped[datetime | None] = mapped_column(DateTime)
    last_success: Mapped[datetime | None] = mapped_column(DateTime)
    status: Mapped[str | None] = mapped_column(String(50))
    error_message: Mapped[str | None] = mapped_column(Text)

    def __repr__(self) -> str:
        return (
            f"MonitorState(id={self.id!r}, monitor_type={self.monitor_type!r}, "
            f"status={self.status!r}, last_run={self.last_run!r})"
        )
