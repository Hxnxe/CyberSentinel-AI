from __future__ import annotations

import json
import threading
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from config import BLACKLIST_DIR, BLACKLIST_REPOSITORIES, BLACKLIST_USERS
from utils.logger import get_logger

logger = get_logger("utils.blacklist_manager")


@dataclass
class _DynamicBlacklist:
    users: set[str]
    repositories: set[str]
    user_records: list[dict[str, Any]]
    repository_records: list[dict[str, Any]]


class BlacklistManager:
    """统一管理静态和动态黑名单。"""

    def __init__(
        self,
        *,
        static_users: list[str] | set[str] | None = None,
        static_repositories: list[str] | set[str] | None = None,
        base_dir: str | Path = BLACKLIST_DIR,
        reload_interval_seconds: int = 3600,
    ) -> None:
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)

        self.user_file = self.base_dir / "user_blacklist.json"
        self.repository_file = self.base_dir / "repository_blacklist.json"
        self.reload_interval_seconds = max(60, int(reload_interval_seconds))

        self.static_users = {self._normalize(x) for x in (static_users or BLACKLIST_USERS)}
        self.static_repositories = {self._normalize(x) for x in (static_repositories or BLACKLIST_REPOSITORIES)}

        self._lock = threading.Lock()
        self._last_loaded_at: datetime | None = None
        self._user_mtime = 0.0
        self._repo_mtime = 0.0
        self._dynamic = _DynamicBlacklist(set(), set(), [], [])
        self.reload_if_needed(force=True)

    @staticmethod
    def _normalize(name: str | None) -> str:
        if not name:
            return ""
        return str(name).strip().lower()

    def _read_records(self, path: Path) -> list[dict[str, Any]]:
        if not path.exists():
            path.write_text("[]", encoding="utf-8")
            return []
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(data, list):
                return [item for item in data if isinstance(item, dict)]
        except Exception as exc:
            logger.warning("读取黑名单文件失败 %s: %s", path, str(exc))
        return []

    def _write_records(self, path: Path, records: list[dict[str, Any]]) -> None:
        path.write_text(json.dumps(records, ensure_ascii=False, indent=2), encoding="utf-8")

    def reload_if_needed(self, *, force: bool = False) -> None:
        with self._lock:
            now = datetime.now()
            should_reload = force
            if self._last_loaded_at is None:
                should_reload = True
            else:
                age = (now - self._last_loaded_at).total_seconds()
                if age >= self.reload_interval_seconds:
                    should_reload = True

            user_mtime = self.user_file.stat().st_mtime if self.user_file.exists() else 0.0
            repo_mtime = self.repository_file.stat().st_mtime if self.repository_file.exists() else 0.0
            if user_mtime != self._user_mtime or repo_mtime != self._repo_mtime:
                should_reload = True

            if not should_reload:
                return

            user_records = self._read_records(self.user_file)
            repo_records = self._read_records(self.repository_file)

            users = {self._normalize(item.get("name")) for item in user_records if item.get("name")}
            repos = {self._normalize(item.get("name")) for item in repo_records if item.get("name")}

            for item in repo_records:
                owner = self._normalize(item.get("owner"))
                if owner:
                    users.add(owner)

            self._dynamic = _DynamicBlacklist(users, repos, user_records, repo_records)
            self._last_loaded_at = now
            self._user_mtime = self.user_file.stat().st_mtime if self.user_file.exists() else 0.0
            self._repo_mtime = self.repository_file.stat().st_mtime if self.repository_file.exists() else 0.0

    def is_blacklisted(self, name: str, entry_type: str) -> bool:
        self.reload_if_needed()
        normalized = self._normalize(name)
        if not normalized:
            return False
        if entry_type == "user":
            return normalized in self.static_users or normalized in self._dynamic.users
        if entry_type == "repository":
            return normalized in self.static_repositories or normalized in self._dynamic.repositories
        raise ValueError("entry_type 必须是 'user' 或 'repository'")

    def add_to_blacklist(self, name: str, entry_type: str, reason: str) -> bool:
        normalized = self._normalize(name)
        if not normalized:
            return False

        self.reload_if_needed()
        if self.is_blacklisted(normalized, entry_type):
            return False

        with self._lock:
            record = {
                "name": name.strip(),
                "added_at": datetime.now().isoformat(),
                "reason": reason.strip() if reason else "无说明",
            }

            if entry_type == "user":
                records = list(self._dynamic.user_records)
                records.append(record)
                self._write_records(self.user_file, records)
            elif entry_type == "repository":
                records = list(self._dynamic.repository_records)
                if "/" in name:
                    record["owner"] = name.split("/", 1)[0].strip()
                records.append(record)
                self._write_records(self.repository_file, records)
            else:
                raise ValueError("entry_type 必须是 'user' 或 'repository'")

        self.reload_if_needed(force=True)
        logger.info("已加入黑名单: %s (%s)", name, entry_type)
        return True
