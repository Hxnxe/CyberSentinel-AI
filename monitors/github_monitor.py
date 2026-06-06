from __future__ import annotations

import os
import time
from datetime import datetime, timedelta
from typing import Any

from sqlalchemy.engine import Engine

from clients.github_client import GithubClient
from config import GITHUB_KEYWORDS, WATCHED_REPOSITORIES
from database.repositories import MonitorStateRepo, RepositoryRepo
from database.session import SessionFactory, get_engine, get_session
from utils.blacklist_manager import BlacklistManager
from utils.logger import get_logger

logger = get_logger("monitors.github_monitor")


class GithubMonitor:
    """GitHub 仓库监控器。"""

    RELEVANT_EXTENSIONS = {
        ".yaml",
        ".yml",
        ".json",
        ".md",
        ".txt",
        ".py",
        ".go",
        ".java",
        ".php",
        ".js",
        ".sh",
        ".rb",
    }
    SECURITY_KEYWORDS = {
        "cve",
        "rce",
        "exploit",
        "poc",
        "payload",
        "shell",
        "bypass",
        "inject",
        "漏洞",
        "利用",
        "安全",
    }

    def __init__(
        self,
        engine: Engine | None = None,
        *,
        github_client: GithubClient | None = None,
        blacklist_manager: BlacklistManager | None = None,
        session_factory: Any | None = None,
        keywords: list[str] | None = None,
        watched_repositories: list[str] | None = None,
        repo_quality_threshold: float = 0.35,
    ) -> None:
        self.engine = engine or get_engine()
        self.session_factory = session_factory or SessionFactory(self.engine)
        self.github_client = github_client or GithubClient()
        self.blacklist_manager = blacklist_manager or BlacklistManager()
        self.keywords = list(keywords or GITHUB_KEYWORDS)
        self.watched_repositories = list(watched_repositories or WATCHED_REPOSITORIES)
        self.repo_quality_threshold = min(max(float(repo_quality_threshold), 0.0), 1.0)

        logger.info("初始化GitHub监控器")
        logger.info("已加载 %s 个搜索关键词", len(self.keywords))
        logger.info("已加载 %s 个监控仓库", len(self.watched_repositories))
        logger.info("仓库质量阈值: %.2f", self.repo_quality_threshold)

    @staticmethod
    def _truncate_patch(patch: str, max_length: int = 1200) -> str:
        if not patch:
            return ""
        return patch if len(patch) <= max_length else patch[:max_length] + "..."

    @staticmethod
    def _record_skip_reason(skip_stats: dict[str, int] | None, reason: str) -> None:
        if skip_stats is None:
            return
        skip_stats[reason] = skip_stats.get(reason, 0) + 1

    @staticmethod
    def _build_fingerprint(repo_name: str, last_update: datetime | None) -> str:
        if not repo_name:
            return ""
        minute_key = (last_update or datetime.now()).strftime("%Y%m%d%H%M")
        return f"{repo_name}:{minute_key}"

    def _score_repository_metadata(self, repo: dict[str, Any]) -> tuple[float, list[str]]:
        score = 0.0
        reasons: list[str] = []

        stars = int(repo.get("stars", 0) or 0)
        if stars >= 100:
            score += 0.25
            reasons.append("high_stars")
        elif stars >= 30:
            score += 0.18
            reasons.append("mid_stars")
        elif stars >= 10:
            score += 0.12
            reasons.append("basic_stars")
        elif stars > 0:
            score += 0.05
            reasons.append("low_stars")

        repo_name = str(repo.get("name", "") or "").lower()
        description = str(repo.get("description", "") or "").lower()
        search_keyword = str(repo.get("search_keyword", "") or "").strip().lower()
        text = f"{repo_name} {description}".strip()

        if search_keyword:
            normalized_keyword = search_keyword.replace("+", " ").strip()
            tokens = [token for token in normalized_keyword.split() if len(token) >= 3]
            if normalized_keyword and normalized_keyword in text:
                score += 0.22
                reasons.append("keyword_exact_match")
            elif any(token in text for token in tokens):
                score += 0.12
                reasons.append("keyword_partial_match")

        keyword_hits = sum(1 for keyword in self.SECURITY_KEYWORDS if keyword in text)
        if keyword_hits > 0:
            score += min(0.20, keyword_hits * 0.05)
            reasons.append("security_context")

        if repo.get("is_update"):
            score += 0.08
            reasons.append("updated_repository")
        if repo.get("is_watched"):
            score += 0.08
            reasons.append("watched_repository")

        return min(score, 1.0), reasons

    def _score_repository_commits(self, commits: list[dict[str, Any]]) -> tuple[float, list[str]]:
        if not commits:
            return 0.0, ["no_recent_commits"]

        score = 0.15
        reasons = ["recent_commits"]
        file_signal = 0.0
        patch_signal_hits = 0

        for commit in commits[:5]:
            if not isinstance(commit, dict):
                continue
            for changed_file in commit.get("files", [])[:20]:
                if not isinstance(changed_file, dict):
                    continue
                path = str(changed_file.get("path", "")).lower()
                ext = os.path.splitext(path)[1]
                if ext in self.RELEVANT_EXTENSIONS:
                    file_signal += 0.02
                patch = str(changed_file.get("patch", "")).lower()
                if patch and any(keyword in patch for keyword in self.SECURITY_KEYWORDS):
                    patch_signal_hits += 1

        if file_signal > 0:
            score += min(0.18, file_signal)
            reasons.append("relevant_file_changes")
        if patch_signal_hits > 0:
            score += min(0.15, patch_signal_hits * 0.03)
            reasons.append("security_patch_signal")

        return min(score, 1.0), reasons

    def _enrich_quality_info(
        self,
        repo_data: dict[str, Any],
        *,
        last_update: datetime,
        recent_commits: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        metadata_score, metadata_reasons = self._score_repository_metadata(repo_data)
        commit_score, commit_reasons = self._score_repository_commits(recent_commits or [])

        result = dict(repo_data)
        result["quality_score"] = round(min(1.0, metadata_score + commit_score), 3)
        result["quality_reasons"] = [*metadata_reasons, *commit_reasons] or ["insufficient_signal"]
        result["fingerprint"] = self._build_fingerprint(str(result.get("name", "")), last_update)
        result["skip_reason"] = None
        return result

    def _passes_quality_gate(self, repo_data: dict[str, Any], skip_stats: dict[str, int] | None = None) -> bool:
        score = float(repo_data.get("quality_score", 0.0) or 0.0)
        if repo_data.get("is_watched"):
            if score < self.repo_quality_threshold:
                reasons = list(repo_data.get("quality_reasons", []))
                reasons.append("watched_repository_bypass")
                repo_data["quality_reasons"] = reasons
            return True

        if score < self.repo_quality_threshold:
            repo_data["skip_reason"] = "low_quality_score"
            self._record_skip_reason(skip_stats, "low_quality_score")
            return False
        return True

    def _is_blacklisted(self, repo_name: str, owner_login: str) -> bool:
        if self.blacklist_manager.is_blacklisted(repo_name, "repository"):
            return True
        if owner_login and self.blacklist_manager.is_blacklisted(owner_login, "user"):
            return True
        return False

    def _fetch_readme_content(self, repo_name: str) -> str:
        return self.github_client.get_readme(repo_name) or ""

    def _fetch_recent_commits(
        self,
        repo_name: str,
        since_time: datetime | None = None,
        max_commits: int = 10,
    ) -> list[dict[str, Any]]:
        commits = self.github_client.get_commits(repo_name, since=since_time, per_page=max_commits) or []
        processed: list[dict[str, Any]] = []

        for commit in commits[:max_commits]:
            commit_url = str(commit.get("url", ""))
            sha = str(commit.get("sha", ""))
            if not commit_url and not sha:
                continue

            detail = self.github_client.get_commit_detail(repo_name, commit_url or sha)
            if not isinstance(detail, dict):
                continue

            files: list[dict[str, Any]] = []
            for changed_file in detail.get("files", []):
                if not isinstance(changed_file, dict):
                    continue

                filename = str(changed_file.get("filename", ""))
                if not filename:
                    continue

                ext = os.path.splitext(filename)[1].lower()
                if ext not in self.RELEVANT_EXTENSIONS:
                    continue

                files.append(
                    {
                        "path": filename,
                        "status": changed_file.get("status", "unknown"),
                        "additions": int(changed_file.get("additions", 0) or 0),
                        "deletions": int(changed_file.get("deletions", 0) or 0),
                        "changes": int(changed_file.get("changes", 0) or 0),
                        "patch": self._truncate_patch(str(changed_file.get("patch", ""))),
                    }
                )

            processed.append(
                {
                    "sha": detail.get("sha", sha),
                    "message": str(detail.get("commit", {}).get("message", "")).strip(),
                    "author": str(detail.get("commit", {}).get("author", {}).get("name", "")).strip(),
                    "date": str(detail.get("commit", {}).get("author", {}).get("date", "")),
                    "files": files,
                }
            )

        return processed

    def search_repositories(
        self,
        keyword: str,
        *,
        seen_repo_names: set[str] | None = None,
        skip_stats: dict[str, int] | None = None,
    ) -> list[dict[str, Any]]:
        """按关键词搜索需要分析的仓库。"""
        repos: list[dict[str, Any]] = []
        per_page = 25
        max_pages = 2
        since_date = datetime.now().strftime("%Y-%m-%d")
        metadata_floor = max(0.15, self.repo_quality_threshold - 0.2)

        processed_keyword = keyword
        if " AND " in keyword or " OR " in keyword:
            processed_keyword = keyword.replace(" AND ", "+").replace(" OR ", "+OR+")
            processed_keyword = processed_keyword.replace("(", "").replace(")", "")

        with get_session(self.session_factory) as session:
            repo_repo = RepositoryRepo(session)

            for page in range(1, max_pages + 1):
                query = f"{processed_keyword} pushed:>={since_date}"
                data = self.github_client.search_repos(query, page=page, per_page=per_page)
                if not data or not isinstance(data, dict):
                    break

                items = data.get("items")
                if not isinstance(items, list) or not items:
                    break

                for item in items:
                    if not isinstance(item, dict):
                        continue

                    owner_login = str(item.get("owner", {}).get("login", ""))
                    repo_name = str(item.get("full_name", ""))
                    if not repo_name or self._is_blacklisted(repo_name, owner_login):
                        self._record_skip_reason(skip_stats, "blacklisted_or_invalid_repo")
                        continue

                    if seen_repo_names is not None and repo_name in seen_repo_names:
                        self._record_skip_reason(skip_stats, "duplicate_repo_name")
                        continue

                    pushed_at = str(item.get("pushed_at", ""))
                    try:
                        last_update = datetime.strptime(pushed_at, "%Y-%m-%dT%H:%M:%SZ")
                    except Exception:
                        self._record_skip_reason(skip_stats, "invalid_pushed_at")
                        continue

                    existing = repo_repo.get_by_name(repo_name)
                    if existing and existing.last_update:
                        time_diff = abs((last_update - existing.last_update).total_seconds())
                        if time_diff <= 60:
                            self._record_skip_reason(skip_stats, "stale_update")
                            continue

                    repo_info = {
                        "name": repo_name,
                        "url": item.get("html_url"),
                        "description": str(item.get("description", "") or "")[:500],
                        "last_update": last_update,
                        "stars": int(item.get("stargazers_count", 0) or 0),
                        "is_valuable": int(item.get("stargazers_count", 0) or 0) > 10,
                        "search_keyword": keyword,
                        "owner": owner_login,
                    }
                    lightweight_score, _ = self._score_repository_metadata(repo_info)
                    if lightweight_score < metadata_floor:
                        self._record_skip_reason(skip_stats, "low_metadata_signal")
                        continue

                    repos.append(repo_info)
                    if seen_repo_names is not None:
                        seen_repo_names.add(repo_name)

                if len(items) < per_page:
                    break
                time.sleep(0.2)

        return repos

    def check_watched_repositories(self) -> list[dict[str, Any]]:
        """检查固定监控仓库是否有更新。"""
        updates: list[dict[str, Any]] = []

        with get_session(self.session_factory) as session:
            repo_repo = RepositoryRepo(session)

            for repo_name in self.watched_repositories:
                try:
                    info = self.github_client.get_repository(repo_name)
                    if not info:
                        continue

                    pushed_at = str(info.get("pushed_at", ""))
                    last_update = datetime.strptime(pushed_at, "%Y-%m-%dT%H:%M:%SZ")

                    existing = repo_repo.get_by_name(repo_name)
                    if existing and existing.last_update and last_update <= existing.last_update:
                        continue

                    since_time = existing.last_update if existing and existing.last_update else datetime.now() - timedelta(days=1)
                    recent_commits = self._fetch_recent_commits(repo_name, since_time=since_time, max_commits=5)
                    if not recent_commits:
                        continue

                    if existing:
                        repo_repo.update_analysis(
                            repo_name,
                            {
                                "last_update": last_update,
                                "description": str(info.get("description", "") or ""),
                                "url": info.get("html_url"),
                            },
                        )
                    else:
                        repo_repo.create(
                            {
                                "name": repo_name,
                                "description": str(info.get("description", "") or ""),
                                "last_update": last_update,
                                "url": info.get("html_url"),
                            }
                        )

                    updates.append(
                        {
                            "name": repo_name,
                            "url": info.get("html_url"),
                            "description": str(info.get("description", "") or ""),
                            "stars": int(info.get("stargazers_count", 0) or 0),
                            "last_update": last_update,
                            "recent_commits": recent_commits,
                            "is_update": bool(existing),
                            "is_watched": True,
                        }
                    )
                except Exception as exc:
                    logger.warning("检查监控仓库失败 %s: %s", repo_name, str(exc))

        return updates

    def _process_watched_repository(
        self,
        repo: dict[str, Any],
        repo_name: str,
        repo_url: str,
        last_update: datetime,
        existing_repo: Any,
        repo_repo: RepositoryRepo,
        skip_stats: dict[str, int] | None = None,
    ) -> dict[str, Any] | None:
        if existing_repo and existing_repo.last_update and last_update <= existing_repo.last_update:
            self._record_skip_reason(skip_stats, "watched_no_new_update")
            return None

        since_time = existing_repo.last_update if existing_repo and existing_repo.last_update else None
        recent_commits = self._fetch_recent_commits(repo_name, since_time=since_time, max_commits=5)
        if not recent_commits:
            self._record_skip_reason(skip_stats, "watched_no_recent_commits")
            return None

        if existing_repo:
            repo_repo.update_analysis(
                repo_name,
                {
                    "last_update": last_update,
                    "description": str(repo.get("description", "") or ""),
                    "url": repo_url,
                },
            )
        else:
            repo_repo.create(
                {
                    "name": repo_name,
                    "description": str(repo.get("description", "") or ""),
                    "last_update": last_update,
                    "url": repo_url,
                }
            )

        repo_data = {
            "name": repo_name,
            "url": repo_url,
            "description": str(repo.get("description", "") or ""),
            "stars": int(repo.get("stars", 0) or 0),
            "last_update": last_update,
            "recent_commits": recent_commits,
            "is_update": bool(existing_repo),
            "is_watched": True,
        }
        enriched = self._enrich_quality_info(repo_data, last_update=last_update, recent_commits=recent_commits)
        if not self._passes_quality_gate(enriched, skip_stats):
            return None
        return enriched

    def _process_normal_repository(
        self,
        repo: dict[str, Any],
        repo_name: str,
        repo_url: str,
        last_update: datetime,
        existing_repo: Any,
        repo_repo: RepositoryRepo,
        skip_stats: dict[str, int] | None = None,
    ) -> dict[str, Any] | None:
        if repo_name in self.watched_repositories:
            self._record_skip_reason(skip_stats, "already_in_watched_list")
            return None

        if existing_repo:
            if existing_repo.last_update:
                try:
                    time_diff = (last_update - existing_repo.last_update).total_seconds()
                except Exception:
                    time_diff = float("inf")
                if time_diff < 60:
                    self._record_skip_reason(skip_stats, "stale_update")
                    return None

            recent_commits = self._fetch_recent_commits(
                repo_name,
                since_time=existing_repo.last_update,
                max_commits=5,
            )
            if not recent_commits:
                self._record_skip_reason(skip_stats, "no_recent_commits")
                return None

            repo_data = {
                "name": repo_name,
                "url": repo_url,
                "description": str(repo.get("description", "") or ""),
                "stars": int(repo.get("stars", 0) or 0),
                "last_update": last_update,
                "recent_commits": recent_commits,
                "search_keyword": repo.get("search_keyword"),
                "is_update": True,
                "is_watched": False,
            }
            enriched = self._enrich_quality_info(repo_data, last_update=last_update, recent_commits=recent_commits)
            if not self._passes_quality_gate(enriched, skip_stats):
                return None

            repo_repo.update_analysis(
                repo_name,
                {
                    "last_update": last_update,
                    "description": str(repo.get("description", "") or ""),
                    "url": repo_url,
                },
            )
            return enriched

        recent_commits = repo.get("recent_commits") or self._fetch_recent_commits(repo_name, max_commits=5)
        if not recent_commits:
            self._record_skip_reason(skip_stats, "no_recent_commits")
            return None

        repo_data = {
            "name": repo_name,
            "url": repo_url,
            "description": str(repo.get("description", "") or ""),
            "stars": int(repo.get("stars", 0) or 0),
            "recent_commits": recent_commits,
            "search_keyword": repo.get("search_keyword"),
            "is_update": False,
            "is_watched": False,
            "last_update": last_update,
        }
        enriched = self._enrich_quality_info(repo_data, last_update=last_update, recent_commits=recent_commits)
        if not self._passes_quality_gate(enriched, skip_stats):
            return None

        readme_content = self._fetch_readme_content(repo_name)
        enriched["readme"] = readme_content

        repo_repo.create(
            {
                "name": repo_name,
                "description": str(repo.get("description", "") or ""),
                "last_update": last_update,
                "url": repo_url,
            }
        )
        return enriched

    def process_repository_data(
        self,
        repos: list[dict[str, Any]],
        is_watched: bool = False,
        *,
        seen_fingerprints: set[str] | None = None,
        skip_stats: dict[str, int] | None = None,
    ) -> list[dict[str, Any]]:
        """处理并存储仓库数据。"""
        processed: list[dict[str, Any]] = []

        with get_session(self.session_factory) as session:
            repo_repo = RepositoryRepo(session)

            for repo in repos:
                if not isinstance(repo, dict):
                    self._record_skip_reason(skip_stats, "invalid_repo_payload")
                    continue

                repo_name = str(repo.get("full_name") or repo.get("name") or "")
                repo_url = str(repo.get("html_url") or repo.get("url") or "")
                if not repo_name or not repo_url:
                    self._record_skip_reason(skip_stats, "missing_repo_fields")
                    continue

                owner = repo.get("owner", {})
                owner_name = owner.get("login") if isinstance(owner, dict) else repo.get("owner")
                if self._is_blacklisted(repo_name, str(owner_name or "")):
                    self._record_skip_reason(skip_stats, "blacklisted_or_invalid_repo")
                    continue

                pushed_at = repo.get("pushed_at")
                if pushed_at:
                    try:
                        last_update = datetime.strptime(str(pushed_at), "%Y-%m-%dT%H:%M:%SZ")
                    except Exception:
                        self._record_skip_reason(skip_stats, "invalid_pushed_at")
                        last_update = datetime.now()
                else:
                    last_update = repo.get("last_update") if isinstance(repo.get("last_update"), datetime) else datetime.now()

                existing = repo_repo.get_by_name(repo_name)
                if is_watched:
                    repo_data = self._process_watched_repository(
                        repo,
                        repo_name,
                        repo_url,
                        last_update,
                        existing,
                        repo_repo,
                        skip_stats,
                    )
                else:
                    repo_data = self._process_normal_repository(
                        repo,
                        repo_name,
                        repo_url,
                        last_update,
                        existing,
                        repo_repo,
                        skip_stats,
                    )

                if repo_data:
                    if seen_fingerprints is not None:
                        fingerprint = str(repo_data.get("fingerprint", "") or "")
                        if not fingerprint:
                            self._record_skip_reason(skip_stats, "missing_fingerprint")
                            continue
                        if fingerprint in seen_fingerprints:
                            self._record_skip_reason(skip_stats, "duplicate_fingerprint")
                            continue
                        seen_fingerprints.add(fingerprint)
                    processed.append(repo_data)

        return processed

    def _update_state(self, status: str, error_message: str | None = None, success: bool = False) -> None:
        with get_session(self.session_factory) as session:
            state_repo = MonitorStateRepo(session)
            state_repo.update_state(
                "github",
                status=status,
                error_message=error_message,
                success=success,
            )

    def run(self, interval: int = 3600) -> list[dict[str, Any]]:
        """执行一轮 GitHub 监控并返回待分析仓库。"""
        logger.info("GitHub监控器启动")
        all_repos: list[dict[str, Any]] = []
        skip_stats: dict[str, int] = {}
        seen_repo_names: set[str] = set()
        seen_fingerprints: set[str] = set()

        try:
            self._update_state("running")

            watched_updates = self.check_watched_repositories()
            if watched_updates:
                accepted_watched = 0
                for repo in watched_updates:
                    if not isinstance(repo, dict):
                        self._record_skip_reason(skip_stats, "invalid_repo_payload")
                        continue

                    repo_name = str(repo.get("name", "") or "")
                    if not repo_name:
                        self._record_skip_reason(skip_stats, "missing_repo_fields")
                        continue
                    if repo_name in seen_repo_names:
                        self._record_skip_reason(skip_stats, "duplicate_repo_name")
                        continue
                    seen_repo_names.add(repo_name)

                    last_update = repo.get("last_update") if isinstance(repo.get("last_update"), datetime) else datetime.now()
                    recent_commits = repo.get("recent_commits") if isinstance(repo.get("recent_commits"), list) else []
                    enriched = self._enrich_quality_info(repo, last_update=last_update, recent_commits=recent_commits)
                    if not self._passes_quality_gate(enriched, skip_stats):
                        continue

                    fingerprint = str(enriched.get("fingerprint", "") or "")
                    if not fingerprint:
                        self._record_skip_reason(skip_stats, "missing_fingerprint")
                        continue
                    if fingerprint in seen_fingerprints:
                        self._record_skip_reason(skip_stats, "duplicate_fingerprint")
                        continue
                    seen_fingerprints.add(fingerprint)

                    all_repos.append(enriched)
                    accepted_watched += 1

                logger.info("发现 %s 个特定仓库更新，入队 %s 个", len(watched_updates), accepted_watched)
            else:
                logger.info("特定仓库无更新")

            for keyword in self.keywords:
                repos = self.search_repositories(
                    keyword,
                    seen_repo_names=seen_repo_names,
                    skip_stats=skip_stats,
                )
                if not repos:
                    continue

                repos_to_analyze = self.process_repository_data(
                    repos,
                    is_watched=False,
                    seen_fingerprints=seen_fingerprints,
                    skip_stats=skip_stats,
                )
                if repos_to_analyze:
                    all_repos.extend(repos_to_analyze)
                    logger.info("关键词 %s 发现 %s 个仓库", keyword, len(repos_to_analyze))

            total_skipped = sum(skip_stats.values())
            top_skip_reasons = ", ".join(
                f"{reason}:{count}"
                for reason, count in sorted(skip_stats.items(), key=lambda item: item[1], reverse=True)[:5]
            ) or "none"

            logger.info(
                "仓库筛选统计: accepted=%s, skipped=%s, top_skip_reasons=%s",
                len(all_repos),
                total_skipped,
                top_skip_reasons,
            )
            self._update_state("success", success=True)
            if all_repos:
                logger.info("本轮总计发现 %s 个需要分析的仓库", len(all_repos))
            else:
                logger.info("本轮未发现需要分析的仓库")
            return all_repos

        except Exception as exc:
            logger.error("GitHub监控失败: %s", str(exc), exc_info=True)
            self._update_state("failed", error_message=str(exc), success=False)
            time.sleep(min(interval, 300))
            return []


if __name__ == "__main__":
    monitor = GithubMonitor()
    monitor.run()
