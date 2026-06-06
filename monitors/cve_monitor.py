from __future__ import annotations

import base64
import os
import re
import time
from datetime import datetime, timedelta
from typing import Any

from sqlalchemy.engine import Engine

from clients.github_client import GithubClient
from database.repositories import CVERepo
from database.session import SessionFactory, get_engine, get_session
from utils.blacklist_manager import BlacklistManager
from utils.logger import get_logger

logger = get_logger("monitors.cve_monitor")


class CVEMonitor:
    """CVE 监控器。"""

    def __init__(
        self,
        engine: Engine | None = None,
        *,
        github_client: GithubClient | None = None,
        blacklist_manager: BlacklistManager | None = None,
        session_factory: Any | None = None,
        cve_quality_threshold: float = 0.25,
    ) -> None:
        self.engine = engine or get_engine()
        self.session_factory = session_factory or SessionFactory(self.engine)
        self.github_client = github_client or GithubClient()
        self.blacklist_manager = blacklist_manager or BlacklistManager()
        self.cve_quality_threshold = min(max(float(cve_quality_threshold), 0.0), 1.0)

        self.cve_pattern = re.compile(r"(?i)CVE[-_](\d{4})[-_](\d{4,7})")
        self.relevant_extensions = {
            ".py",
            ".sh",
            ".java",
            ".php",
            ".js",
            ".go",
            ".txt",
            ".md",
            ".yaml",
            ".yml",
            ".json",
            ".xml",
        }
        self.critical_patterns = {"poc", "exploit", "cve", "rce", "payload", "shell"}
        logger.info("初始化CVE监控器")
        logger.info("CVE质量阈值: %.2f", self.cve_quality_threshold)

    def _is_blacklisted(self, repo_name: str, owner_login: str) -> bool:
        if self.blacklist_manager.is_blacklisted(repo_name, "repository"):
            return True
        if owner_login and self.blacklist_manager.is_blacklisted(owner_login, "user"):
            return True
        return False

    def _validate_cve_year(self, year: str) -> bool:
        try:
            year_int = int(year)
            return 1999 <= year_int <= datetime.now().year
        except ValueError:
            return False

    def _extract_cve_ids(self, name: str, description: str) -> set[str]:
        matches = set()
        for text in [name or "", description or ""]:
            for year, number in self.cve_pattern.findall(text):
                if self._validate_cve_year(year):
                    matches.add(f"CVE-{year}-{number}")
        return matches

    def _decode_content(self, encoded: str) -> str:
        try:
            normalized = (encoded or "").replace("\n", "")
            if not normalized:
                return ""
            return base64.b64decode(normalized).decode("utf-8", errors="ignore")
        except Exception:
            return ""

    def _calculate_file_score(self, file_path: str, content: str) -> float:
        path_lower = file_path.lower()
        score = 0.0
        if os.path.basename(path_lower) == "readme.md":
            return 1.0

        ext = os.path.splitext(path_lower)[1]
        if ext in self.relevant_extensions:
            score += 0.4

        if any(pattern in path_lower for pattern in self.critical_patterns):
            score += 0.4

        if content:
            content_lower = content.lower()
            for pattern in self.critical_patterns:
                if pattern in content_lower:
                    score += 0.05
            if "cve-" in content_lower:
                score += 0.2

        return min(score, 1.0)

    def _analyze_repository_files(self, repo_url: str) -> dict[str, Any]:
        if "github.com/" not in repo_url:
            return {"relevant_files": [], "code_contents": [], "has_readme": False}

        repo_full_name = "/".join(repo_url.split("github.com/")[-1].split("/")[:2])
        contents = self.github_client.get_contents(repo_full_name) or []
        if not contents:
            return {"relevant_files": [], "code_contents": [], "has_readme": False}

        relevant_files: list[str] = []
        code_contents: list[dict[str, Any]] = []
        has_readme = False

        for item in contents[:40]:
            if item.get("type") != "file":
                continue
            file_name = item.get("name", "")
            file_path = item.get("path", file_name)
            item_url = item.get("url", "")
            if not file_name or not item_url:
                continue

            item_detail = self.github_client.get_json_by_url(item_url)
            if not isinstance(item_detail, dict):
                continue
            content = self._decode_content(str(item_detail.get("content", "")))
            if not content:
                continue

            if file_name.lower() == "readme.md":
                has_readme = True

            score = self._calculate_file_score(file_path, content)
            if score < 0.3:
                continue

            relevant_files.append(file_path)
            code_contents.append(
                {
                    "file_name": file_name,
                    "file_path": file_path,
                    "content": content[:3000],
                    "size": len(content),
                    "score": score,
                }
            )

        code_contents.sort(key=lambda x: x.get("score", 0), reverse=True)
        return {
            "relevant_files": relevant_files,
            "code_contents": code_contents[:20],
            "has_readme": has_readme,
        }

    def _fetch_latest_commits(self, repo_full_name: str, max_commits: int = 5) -> list[dict[str, Any]]:
        commits = self.github_client.get_commits(repo_full_name, per_page=max_commits) or []
        processed: list[dict[str, Any]] = []

        for commit in commits[:max_commits]:
            commit_url = str(commit.get("url", ""))
            sha = str(commit.get("sha", ""))
            if not commit_url and not sha:
                continue

            detail = self.github_client.get_commit_detail(repo_full_name, commit_url or sha)
            if not detail:
                continue

            files = []
            for changed_file in detail.get("files", []):
                if not isinstance(changed_file, dict):
                    continue
                files.append(
                    {
                        "path": changed_file.get("filename", ""),
                        "status": changed_file.get("status", "unknown"),
                        "additions": int(changed_file.get("additions", 0) or 0),
                        "deletions": int(changed_file.get("deletions", 0) or 0),
                        "changes": int(changed_file.get("changes", 0) or 0),
                        "patch": str(changed_file.get("patch", ""))[:1200],
                    }
                )

            commit_data = {
                "sha": detail.get("sha", sha),
                "message": detail.get("commit", {}).get("message", ""),
                "author": detail.get("commit", {}).get("author", {}).get("name", ""),
                "date": detail.get("commit", {}).get("author", {}).get("date", ""),
                "files": files,
            }
            processed.append(commit_data)

        return processed

    @staticmethod
    def _record_skip_reason(skip_stats: dict[str, int], reason: str) -> None:
        skip_stats[reason] = skip_stats.get(reason, 0) + 1

    @staticmethod
    def _build_fingerprint(cve_id: str, repo_name: str, last_modified: datetime) -> str:
        minute_key = last_modified.strftime("%Y%m%d%H%M")
        return f"{cve_id}:{repo_name}:{minute_key}"

    def _score_cve_candidate(
        self,
        *,
        repo_name: str,
        stars: int,
        repo_analysis: dict[str, Any],
        recent_commits: list[dict[str, Any]],
    ) -> tuple[float, list[str]]:
        score = 0.0
        reasons: list[str] = []

        repo_name_lower = repo_name.lower()
        name_hits = sum(1 for pattern in self.critical_patterns if pattern in repo_name_lower)
        if name_hits > 0:
            score += min(0.2, name_hits * 0.05)
            reasons.append("repo_name_signal")

        if stars >= 20:
            score += 0.15
            reasons.append("high_stars")
        elif stars >= 5:
            score += 0.08
            reasons.append("mid_stars")
        elif stars > 0:
            score += 0.03
            reasons.append("low_stars")

        relevant_files = repo_analysis.get("relevant_files", [])
        if isinstance(relevant_files, list) and relevant_files:
            score += min(0.35, len(relevant_files[:10]) * 0.05)
            reasons.append("relevant_files")

        if repo_analysis.get("has_readme"):
            score += 0.05
            reasons.append("has_readme")

        code_contents = repo_analysis.get("code_contents", [])
        if isinstance(code_contents, list):
            high_signal_files = sum(
                1
                for item in code_contents[:10]
                if isinstance(item, dict) and float(item.get("score", 0) or 0) >= 0.6
            )
            if high_signal_files > 0:
                score += min(0.2, high_signal_files * 0.05)
                reasons.append("high_signal_content")

        if recent_commits:
            score += 0.15
            reasons.append("recent_commits")
            patch_hits = 0
            for commit in recent_commits[:5]:
                if not isinstance(commit, dict):
                    continue
                for changed_file in commit.get("files", [])[:20]:
                    if not isinstance(changed_file, dict):
                        continue
                    patch = str(changed_file.get("patch", "")).lower()
                    if patch and any(pattern in patch for pattern in self.critical_patterns):
                        patch_hits += 1
            if patch_hits > 0:
                score += min(0.15, patch_hits * 0.03)
                reasons.append("patch_signal")
        else:
            reasons.append("no_recent_commits")

        return min(score, 1.0), reasons or ["insufficient_signal"]

    def _should_filter_low_signal(
        self,
        *,
        repo_name: str,
        stars: int,
        repo_analysis: dict[str, Any],
        quality_score: float,
    ) -> bool:
        relevant_files = repo_analysis.get("relevant_files", [])
        has_file_evidence = isinstance(relevant_files, list) and bool(relevant_files)
        if has_file_evidence:
            return False

        repo_name_lower = repo_name.lower()
        has_keyword_signal = any(pattern in repo_name_lower for pattern in self.critical_patterns)
        if has_keyword_signal:
            return False

        if stars >= 5:
            return False

        return quality_score < self.cve_quality_threshold

    def fetch_latest_cves(self) -> list[dict[str, Any]]:
        """从 GitHub 获取最新 CVE 相关仓库并提取结构化数据。"""
        logger.info("开始获取最新CVE信息...")
        start_date = (datetime.now() - timedelta(days=5)).strftime("%Y-%m-%d")
        query = f"CVE-202 pushed:>={start_date}"

        results: list[dict[str, Any]] = []
        processed_pairs: set[str] = set()
        stats = {"processed": 0, "skipped": 0, "new": 0, "updated": 0, "accepted": 0}
        skip_reasons: dict[str, int] = {}

        for page in range(1, 11):
            data = self.github_client.search_repos(query, page=page, per_page=50)
            if not data or not isinstance(data, dict):
                break

            items = data.get("items")
            if not isinstance(items, list) or not items:
                break

            with get_session(self.session_factory) as session:
                cve_repo = CVERepo(session)

                for item_idx, item in enumerate(items, 1):
                    if not isinstance(item, dict):
                        stats["skipped"] += 1
                        self._record_skip_reason(skip_reasons, "invalid_repo_payload")
                        continue

                    stats["processed"] += 1
                    owner_login = str(item.get("owner", {}).get("login", ""))
                    repo_name = str(item.get("full_name", ""))
                    if not repo_name or self._is_blacklisted(repo_name, owner_login):
                        stats["skipped"] += 1
                        self._record_skip_reason(skip_reasons, "blacklisted_or_invalid_repo")
                        continue

                    pushed_at = str(item.get("pushed_at", ""))
                    try:
                        last_modified = datetime.strptime(pushed_at, "%Y-%m-%dT%H:%M:%SZ")
                    except Exception:
                        stats["skipped"] += 1
                        self._record_skip_reason(skip_reasons, "invalid_pushed_at")
                        continue

                    cve_ids = self._extract_cve_ids(str(item.get("name", "")), str(item.get("description", "")))
                    if not cve_ids:
                        stats["skipped"] += 1
                        self._record_skip_reason(skip_reasons, "no_cve_id")
                        continue

                    repo_url = str(item.get("html_url", ""))
                    stars = int(item.get("stargazers_count", 0) or 0)
                    logger.info("处理仓库 [%s/%s] (页%s): %s, CVEs=%s", item_idx, len(items), page, repo_name, cve_ids)
                    repo_analysis = self._analyze_repository_files(repo_url) if repo_url else {}
                    recent_commits = self._fetch_latest_commits(repo_name)
                    quality_score, quality_reasons = self._score_cve_candidate(
                        repo_name=repo_name,
                        stars=stars,
                        repo_analysis=repo_analysis,
                        recent_commits=recent_commits,
                    )

                    for cve_id in cve_ids:
                        if self._should_filter_low_signal(
                            repo_name=repo_name,
                            stars=stars,
                            repo_analysis=repo_analysis,
                            quality_score=quality_score,
                        ):
                            stats["skipped"] += 1
                            self._record_skip_reason(skip_reasons, "low_signal_candidate")
                            continue

                        pair_key = f"{cve_id}:{repo_name}"
                        if pair_key in processed_pairs:
                            stats["skipped"] += 1
                            self._record_skip_reason(skip_reasons, "duplicate_pair")
                            continue
                        processed_pairs.add(pair_key)

                        existing = cve_repo.get_by_id(cve_id)
                        if existing and existing.last_modified and existing.last_modified >= last_modified:
                            stats["skipped"] += 1
                            self._record_skip_reason(skip_reasons, "not_modified")
                            continue

                        if existing:
                            stats["updated"] += 1
                        else:
                            stats["new"] += 1
                        stats["accepted"] += 1

                        results.append(
                            {
                                "cve_id": cve_id,
                                "description": str(item.get("description", "") or ""),
                                "published_date": datetime.strptime(pushed_at[:10], "%Y-%m-%d"),
                                "last_modified": last_modified,
                                "severity": "Unknown",
                                "repository_url": repo_url,
                                "stars": stars,
                                "recent_commits": recent_commits,
                                "repository_analysis": repo_analysis,
                                "quality_score": round(quality_score, 3),
                                "quality_reasons": quality_reasons,
                                "skip_reason": None,
                                "fingerprint": self._build_fingerprint(cve_id, repo_name, last_modified),
                            }
                        )

            if len(items) < 50:
                break
            time.sleep(0.2)

        top_skip_reasons = ", ".join(
            f"{reason}:{count}"
            for reason, count in sorted(skip_reasons.items(), key=lambda item: item[1], reverse=True)[:5]
        ) or "none"
        logger.info(
            "CVE处理统计: 总处理=%s, 新增=%s, 更新=%s, 接受=%s, 跳过=%s, 跳过原因=%s",
            stats["processed"],
            stats["new"],
            stats["updated"],
            stats["accepted"],
            stats["skipped"],
            top_skip_reasons,
        )
        return results

    def process_cve_data(self, cve_info_list: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """落库并返回需要分析的 CVE。"""
        if not cve_info_list:
            return []

        to_analyze: list[dict[str, Any]] = []
        created = 0
        updated = 0
        skipped = 0

        db_fields = {
            "cve_id",
            "description",
            "published_date",
            "last_modified",
            "repository_url",
            "severity",
            "ai_summary",
            "last_analyzed",
            "stars",
            "last_fetched",
            "created_at",
        }

        with get_session(self.session_factory) as session:
            cve_repo = CVERepo(session)
            now = datetime.now()

            for cve_info in cve_info_list:
                cve_id = str(cve_info.get("cve_id", ""))
                if not cve_id:
                    skipped += 1
                    continue

                latest_modified = cve_info.get("last_modified")
                existing = cve_repo.get_by_id(cve_id)

                if existing:
                    needs_analysis = cve_repo.needs_analysis(cve_id, latest_modified=latest_modified, interval_hours=1)
                    if not needs_analysis:
                        skipped += 1
                        continue

                    update_data = {
                        key: value
                        for key, value in cve_info.items()
                        if key in db_fields and key != "last_analyzed"
                    }
                    update_data["last_fetched"] = now
                    cve_repo.update(cve_id, update_data)
                    updated += 1
                else:
                    create_data = {
                        key: value
                        for key, value in cve_info.items()
                        if key in db_fields
                    }
                    create_data["last_fetched"] = now
                    cve_repo.create(create_data)
                    created += 1

                to_analyze.append(cve_info)

        logger.info(
            "CVE入库统计: 输入=%s, 新增=%s, 更新=%s, 跳过=%s, 待分析=%s",
            len(cve_info_list),
            created,
            updated,
            skipped,
            len(to_analyze),
        )
        return to_analyze

    def run(self, interval: int = 3600) -> None:
        logger.info("CVE监控器启动，监控间隔: %s秒", interval)
        while True:
            try:
                cve_info_list = self.fetch_latest_cves()
                if cve_info_list:
                    cves_to_analyze = self.process_cve_data(cve_info_list)
                    logger.info("本轮监控完成，处理了 %s 条待分析记录", len(cves_to_analyze))
                else:
                    logger.info("本轮未获取到新的CVE信息")
                time.sleep(interval)
            except Exception as exc:
                logger.error("CVE监控运行失败: %s", str(exc), exc_info=True)
                time.sleep(300)


if __name__ == "__main__":
    monitor = CVEMonitor()
    monitor.run()
