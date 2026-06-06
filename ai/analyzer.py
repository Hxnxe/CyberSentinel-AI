from __future__ import annotations

import json
import os
import re
from datetime import datetime
from typing import Any

from ai.llm_client import LLMClient
from ai.prompts import (
    build_repo_user_prompt,
    get_article_system_prompt,
    get_cve_system_prompt,
    get_cve_user_prompt,
    get_repo_system_prompt,
)
from ai.result_validator import validate_article_result, validate_cve_result, validate_repo_result
from ai.schemas import ArticleClassificationResult, SecurityAnalysisResult
from database.repositories import CVERepo, RepositoryRepo
from database.session import SessionFactory, get_engine, get_session
from utils.blacklist_manager import BlacklistManager
from utils.logger import get_logger

logger = get_logger("analyzer")
logger.propagate = False


class SecurityAnalyzer:
    """安全分析业务编排层。"""

    def __init__(
        self,
        *,
        llm_client: LLMClient | None = None,
        blacklist_manager: BlacklistManager | None = None,
        engine: Any | None = None,
        session_factory: Any | None = None,
    ) -> None:
        self.engine = engine or get_engine()
        self.session_factory = session_factory or SessionFactory(self.engine)
        self.llm_client = llm_client or LLMClient()
        self.blacklist_manager = blacklist_manager or BlacklistManager()

        self.report_dir = os.path.join("reports", "daily")
        self.analysis_history_dir = os.path.join("data", "analysis_history")
        self.ai_analysis_dir = os.path.join("results", "ai_analysis")

        os.makedirs(self.report_dir, exist_ok=True)
        os.makedirs(self.analysis_history_dir, exist_ok=True)
        os.makedirs(self.ai_analysis_dir, exist_ok=True)

    def _safe_json_dumps(self, data: Any, ensure_ascii: bool = False) -> str:
        def _default(obj: Any) -> str:
            if isinstance(obj, datetime):
                return obj.isoformat()
            return str(obj)

        try:
            return json.dumps(data, ensure_ascii=ensure_ascii, default=_default, indent=2)
        except Exception as exc:
            logger.warning("JSON序列化失败: %s", str(exc))
            return str(data)

    def _clean_title_for_analysis(self, title: str) -> str:
        if not title:
            return ""
        text = title.replace("\n", " ").replace("\r", " ").replace("\t", " ")
        text = re.sub(r"[\x00-\x1F\x7F-\x9F]", "", text)
        return " ".join(text.split())

    def _process_commits(
        self,
        commits: Any,
        max_commits: int = 5,
        max_file_changes: int = 1000,
    ) -> list[dict[str, Any]]:
        """统一清洗提交数据。"""
        if not commits:
            return []

        if isinstance(commits, str):
            try:
                commits = json.loads(commits)
            except json.JSONDecodeError:
                return []

        if not isinstance(commits, list):
            return []

        processed_commits: list[dict[str, Any]] = []
        for commit in commits[:max_commits]:
            if not isinstance(commit, dict):
                continue

            author = commit.get("author", "")
            if isinstance(author, dict):
                author_name = author.get("name", "")
            else:
                author_name = str(author or "")

            files: list[dict[str, Any]] = []
            for file_info in commit.get("files", []):
                if not isinstance(file_info, dict):
                    continue

                patch = str(file_info.get("patch", ""))
                if patch and len(patch) > max_file_changes:
                    patch = patch[:max_file_changes] + "..."

                files.append(
                    {
                        "path": str(file_info.get("path", "")),
                        "status": str(file_info.get("status", "")),
                        "changes": int(file_info.get("changes", 0) or 0),
                        "patch": patch,
                        "additions": int(file_info.get("additions", 0) or 0),
                        "deletions": int(file_info.get("deletions", 0) or 0),
                    }
                )

            processed_commits.append(
                {
                    "message": str(commit.get("message", "")),
                    "date": str(commit.get("date", "")),
                    "author": author_name,
                    "files": files,
                    "sha": str(commit.get("sha", "")),
                }
            )

        return processed_commits

    def _validate_repo_data(self, repo_data: Any) -> bool:
        """验证仓库输入数据格式。"""
        if not isinstance(repo_data, dict):
            return False
        if not repo_data.get("name"):
            return False

        commits = repo_data.get("recent_commits")
        if commits is None:
            repo_data["recent_commits"] = []
            return True

        if isinstance(commits, str):
            try:
                commits = json.loads(commits)
            except json.JSONDecodeError:
                repo_data["recent_commits"] = []
                return False

        if not isinstance(commits, list):
            repo_data["recent_commits"] = []
            return False

        normalized: list[dict[str, Any]] = []
        for commit in commits:
            if isinstance(commit, str):
                try:
                    commit = json.loads(commit)
                except json.JSONDecodeError:
                    continue
            if isinstance(commit, dict):
                normalized.append(commit)

        repo_data["recent_commits"] = normalized
        return True

    def _get_default_repo_result(self, repo_data: dict[str, Any]) -> dict[str, Any]:
        return {
            "repository_name": repo_data.get("name", "Unknown"),
            "is_valuable": False,
            "value_reason": "AI分析服务暂时不可用",
            "summary": "由于AI服务不可用，无法进行详细分析",
            "risk_level": "LOW",
            "key_points": ["AI服务暂时不可用"],
            "technical_details": ["无法获取技术细节"],
            "affected_components": ["未知"],
            "security_type": "未知",
            "update_type": "GENERAL_UPDATE",
            "search_keyword": repo_data.get("search_keyword", "N/A"),
            "relevance_score": "LOW",
        }

    def _get_default_cve_result(self, cve_data: dict[str, Any]) -> dict[str, Any]:
        return {
            "cve_id": cve_data.get("cve_id"),
            "is_valuable": False,
            "value_reason": "AI分析服务暂时不可用",
            "short_description": "AI服务不可用，无法分析",
            "summary": "由于AI服务不可用，无法进行详细的CVE分析",
            "risk_level": "LOW",
            "exploit_status": "未知",
            "key_points": ["AI服务暂时不可用"],
            "technical_details": ["无法获取技术细节"],
            "affected_components": ["未知"],
            "repository_url": cve_data.get("repository_url"),
            "published_date": cve_data.get("published_date"),
            "last_modified": cve_data.get("last_modified"),
            "stars": cve_data.get("stars", 0),
        }

    def analyze_repository(self, repo_data: dict[str, Any]) -> dict[str, Any] | None:
        """分析仓库数据。"""
        try:
            repo_name = str(repo_data.get("name", ""))
            owner = str(repo_data.get("owner", ""))

            self.blacklist_manager.reload_if_needed()
            if repo_name and self.blacklist_manager.is_blacklisted(repo_name, "repository"):
                logger.info("仓库 %s 在黑名单中，跳过分析", repo_name)
                return None
            if owner and self.blacklist_manager.is_blacklisted(owner, "user"):
                logger.info("作者 %s 在黑名单中，跳过分析", owner)
                return None

            if not self._validate_repo_data(repo_data):
                logger.error("仓库数据验证失败")
                return None

            processed_commits = self._process_commits(repo_data.get("recent_commits", []))
            repo_data["recent_commits"] = processed_commits

            if repo_data.get("is_watched"):
                prompt_type = "watched"
            elif repo_data.get("is_update"):
                prompt_type = "update"
            else:
                prompt_type = "normal"

            system_prompt = get_repo_system_prompt(prompt_type)
            user_prompt = build_repo_user_prompt(repo_data, processed_commits, prompt_type)
            raw_result = self.llm_client.generate_json(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                response_schema=SecurityAnalysisResult,
            )

            if raw_result is None:
                logger.error("仓库 %s 分析失败，返回默认结果", repo_name)
                result = self._get_default_repo_result(repo_data)
            else:
                result = validate_repo_result(raw_result, repo_data, processed_commits)
                if not result:
                    logger.error("仓库 %s 结果校验失败，返回默认结果", repo_name)
                    result = self._get_default_repo_result(repo_data)

            self._save_ai_response(result, "repository", repo_name or "unknown")

            with get_session(self.session_factory) as session:
                repo_repo = RepositoryRepo(session)
                existing = repo_repo.get_by_name(repo_name)
                if existing:
                    repo_repo.update_analysis(
                        repo_name,
                        {
                            "ai_summary": self._safe_json_dumps(result),
                            "is_valuable": bool(result.get("is_valuable", False)),
                            "last_analyzed": datetime.now(),
                        },
                    )

            if not result.get("is_valuable", False):
                self._record_worthless_repository(repo_name)

            return result
        except Exception as exc:
            logger.error("分析仓库 %s 失败: %s", repo_data.get("name", "Unknown"), str(exc), exc_info=True)
            return None

    def analyze_cve(self, cve_data: dict[str, Any]) -> dict[str, Any]:
        """分析 CVE 数据。"""
        try:
            system_prompt = get_cve_system_prompt()
            user_prompt = get_cve_user_prompt(cve_data)

            raw_result = self.llm_client.generate_json(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                response_schema=SecurityAnalysisResult,
            )
            if raw_result is None:
                logger.error("CVE %s 分析失败，返回默认结果", cve_data.get("cve_id"))
                result = self._get_default_cve_result(cve_data)
            else:
                result = validate_cve_result(raw_result, cve_data)
                if not result:
                    logger.error("CVE %s 结果校验失败，返回默认结果", cve_data.get("cve_id"))
                    result = self._get_default_cve_result(cve_data)

            self._save_ai_response(result, "cve", str(cve_data.get("cve_id", "unknown")))

            with get_session(self.session_factory) as session:
                cve_repo = CVERepo(session)
                cve_id = str(cve_data.get("cve_id", ""))
                if cve_id:
                    existing = cve_repo.get_by_id(cve_id)
                    if existing:
                        cve_repo.update(
                            cve_id,
                            {
                                "ai_summary": self._safe_json_dumps(result),
                                "severity": result.get("risk_level", "MEDIUM"),
                                "last_analyzed": datetime.now(),
                            },
                        )

            return result
        except Exception as exc:
            logger.error("分析CVE失败: %s", str(exc), exc_info=True)
            return {
                "cve_id": cve_data.get("cve_id"),
                "is_valuable": False,
                "value_reason": f"分析过程出错: {str(exc)}",
            }

    def _build_article_user_prompt(self, articles_batch: list[tuple[str, str]]) -> str:
        lines = ["请分析以下文章标题：", ""]
        for title, _ in articles_batch:
            lines.append(f"- {title}")
        return "\n".join(lines)

    def _default_classify_articles(self, articles_batch: list[tuple[str, str]]) -> list[dict[str, str]]:
        rules = {
            "漏洞分析": ["漏洞", "cve", "poc", "exploit", "复现", "注入", "rce", "xss", "提权"],
            "威胁情报": ["apt", "恶意软件", "勒索", "攻击", "入侵", "僵尸网络", "黑客组织"],
            "安全工具": ["工具", "扫描", "检测", "审计", "nmap", "burp", "metasploit"],
            "安全研究": ["研究", "分析", "技术", "原理", "方法", "框架"],
            "最佳实践": ["防护", "配置", "指南", "教程", "实践", "建设"],
            "吃瓜新闻": ["事件", "新闻", "企业", "泄露", "被黑", "入侵"],
        }

        classified = []
        for title, url in articles_batch:
            clean_title = self._clean_title_for_analysis(title).lower()
            category = "其他"
            max_matches = 0
            for current, keywords in rules.items():
                matches = sum(1 for keyword in keywords if keyword in clean_title)
                if matches > max_matches:
                    max_matches = matches
                    category = current
            classified.append({"title": title, "url": url, "category": category})
        return classified

    def analyze_article_titles(self, articles: list[tuple[str, str]]) -> dict[str, Any]:
        """分析文章标题并分类。"""
        if not articles:
            return {
                "filtered_articles": [],
                "categories": {},
                "stats": {"total": 0, "filtered": 0, "ad_count": 0},
            }

        total_articles = len(articles)
        batch_size = 100
        all_results: list[dict[str, str]] = []

        for start in range(0, total_articles, batch_size):
            batch = articles[start : start + batch_size]
            user_prompt = self._build_article_user_prompt(batch)
            title_to_url = {self._clean_title_for_analysis(title): url for title, url in batch}

            raw_result = self.llm_client.generate_json(
                system_prompt=get_article_system_prompt(),
                user_prompt=user_prompt,
                response_schema=ArticleClassificationResult,
            )
            validated = validate_article_result(raw_result if isinstance(raw_result, dict) else {})

            if not validated:
                all_results.extend(self._default_classify_articles(batch))
                continue

            for item in validated.get("articles", []):
                title = self._clean_title_for_analysis(str(item.get("title", "")))
                category = str(item.get("category", "其他")).strip() or "其他"
                if not title:
                    continue

                url = title_to_url.get(title)
                if not url:
                    for raw_title, raw_url in batch:
                        if self._clean_title_for_analysis(raw_title) == title:
                            url = raw_url
                            break
                if not url:
                    continue

                all_results.append({"title": title, "url": url, "category": category})

        ad_keywords = ["培训", "课程", "报名", "直播课", "优惠", "加群", "微信咨询", "认证班"]
        filtered_articles: list[dict[str, str]] = []
        categories_count: dict[str, int] = {}
        ad_count = 0

        for article in all_results:
            title = article.get("title", "")
            category = article.get("category", "其他")
            if any(keyword in title for keyword in ad_keywords):
                ad_count += 1
                continue

            filtered_articles.append(article)
            categories_count[category] = categories_count.get(category, 0) + 1

        return {
            "filtered_articles": filtered_articles,
            "categories": categories_count,
            "stats": {
                "total": total_articles,
                "filtered": len(filtered_articles),
                "ad_count": ad_count,
            },
        }

    def _save_ai_response(self, result: dict[str, Any], analysis_type: str, identifier: str) -> None:
        """保存 AI 分析结果到按月分组的 JSON 文件。"""
        try:
            current_month = datetime.now().strftime("%Y_%m")
            base_dir = os.path.join(self.ai_analysis_dir, analysis_type, current_month)
            os.makedirs(base_dir, exist_ok=True)

            valuable_file = os.path.join(base_dir, "valuable_analysis.json")
            worthless_file = os.path.join(base_dir, "worthless_analysis.json")

            model_info = dict(self.llm_client.last_used_info)
            analysis_record = {
                "timestamp": datetime.now().isoformat(),
                "identifier": identifier,
                "model_info": model_info,
                "analysis_result": result,
            }

            if analysis_type == "repository":
                search_keyword = result.get("search_keyword", "N/A")
                analysis_record["search_info"] = {
                    "keyword": search_keyword,
                    "discovery_method": "keyword_search" if search_keyword != "N/A" else "watched_repository",
                }

            target_file = valuable_file if result.get("is_valuable", False) else worthless_file

            records: list[dict[str, Any]] = []
            if os.path.exists(target_file):
                try:
                    loaded = json.loads(open(target_file, "r", encoding="utf-8").read())
                    if isinstance(loaded, list):
                        records = loaded
                except Exception:
                    records = []

            records.append(analysis_record)
            with open(target_file, "w", encoding="utf-8") as f:
                json.dump(records, f, ensure_ascii=False, indent=2, default=str)

        except Exception as exc:
            logger.error("保存AI分析结果失败: %s", str(exc), exc_info=True)

    def _record_worthless_repository(self, repo_name: str) -> None:
        """记录无价值仓库并按阈值更新动态黑名单。"""
        if not repo_name:
            return

        stats_file = os.path.join(self.analysis_history_dir, "worthless_repository_stats.json")
        stats: dict[str, Any] = {"repos": {}, "owners": {}}

        if os.path.exists(stats_file):
            try:
                loaded = json.loads(open(stats_file, "r", encoding="utf-8").read())
                if isinstance(loaded, dict):
                    stats = loaded
            except Exception:
                pass

        repo_stats = stats.setdefault("repos", {})
        owner_stats = stats.setdefault("owners", {})

        current = repo_stats.get(repo_name, {"count": 0, "last_updated": None})
        current["count"] = int(current.get("count", 0)) + 1
        current["last_updated"] = datetime.now().isoformat()
        repo_stats[repo_name] = current

        owner = repo_name.split("/", 1)[0] if "/" in repo_name else ""
        if owner:
            owner_info = owner_stats.get(owner, {"repos": []})
            repos = set(owner_info.get("repos", []))
            repos.add(repo_name)
            owner_info["repos"] = sorted(repos)
            owner_stats[owner] = owner_info

        try:
            with open(stats_file, "w", encoding="utf-8") as f:
                json.dump(stats, f, ensure_ascii=False, indent=2)
        except Exception:
            logger.warning("写入无价值仓库统计失败")

        if int(current.get("count", 0)) >= 3:
            self.blacklist_manager.add_to_blacklist(repo_name, "repository", "Consecutive worthless analysis")

        if owner:
            owner_repo_count = len(owner_stats.get(owner, {}).get("repos", []))
            if owner_repo_count >= 5:
                self.blacklist_manager.add_to_blacklist(owner, "user", "Multiple worthless repositories")


if __name__ == "__main__":
    analyzer = SecurityAnalyzer()
    print(analyzer is not None)
