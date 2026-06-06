from __future__ import annotations

import os
from datetime import datetime
from typing import Any

from database.repositories import RepositoryRepo
from database.session import get_session
from utils.logger import get_logger
from utils.markdown_parser import convert_md_to_html

logger = get_logger("reports.generator")


class ReportGenerator:
    """统一处理分析结果落盘与博客更新。"""

    def __init__(
        self,
        *,
        session_factory: Any,
        blog_manager: Any,
        ai_analysis_dir: str = "results/ai_analysis",
        html_output_dir: str = "results/ai_html",
    ) -> None:
        self.session_factory = session_factory
        self.blog_manager = blog_manager
        self.ai_analysis_dir = ai_analysis_dir
        self.html_output_dir = html_output_dir

        os.makedirs(self.ai_analysis_dir, exist_ok=True)
        os.makedirs(self.html_output_dir, exist_ok=True)

    def _check_repository_limit(self, repo_name: str) -> bool:
        with get_session(self.session_factory) as session:
            repo_repo = RepositoryRepo(session)
            return repo_repo.check_daily_limit(repo_name)

    @staticmethod
    def _extract_repo_name(result: dict[str, Any], source_type: str) -> str | None:
        if source_type == "repository":
            return result.get("repository_name")
        if source_type == "cve":
            repo_url = result.get("repository_url", "")
            if "github.com/" in repo_url:
                return "/".join(repo_url.split("github.com/")[-1].split("/")[:2])
        return None

    @staticmethod
    def _build_common_sections(result: dict[str, Any]) -> str:
        content = ""
        if result.get("summary"):
            content += f"\n#### 💡 分析概述\n\n{result.get('summary')}\n"

        if result.get("key_points"):
            content += "\n#### 🔍 关键发现\n\n| 序号 | 发现内容 |\n|------|----------|\n"
            for idx, point in enumerate(result["key_points"], 1):
                if point and point != "Unknown":
                    content += f"| {idx} | {point} |\n"

        if result.get("technical_details"):
            content += "\n#### 🛠️ 技术细节\n\n"
            for detail in result["technical_details"]:
                if detail and detail != "Unknown":
                    content += f"> {detail}\n\n"

        if result.get("affected_components"):
            content += "\n#### 🎯 受影响组件\n\n```\n"
            for comp in result["affected_components"]:
                if comp and comp != "Unknown" and comp != "未指定受影响组件":
                    content += f"• {comp}\n"
            content += "```\n"

        if result.get("code_analysis"):
            content += "\n#### 💻 代码分析\n\n"
            for idx, analysis in enumerate(result["code_analysis"], 1):
                if analysis and analysis != "Unknown":
                    content += f"**分析 {idx}**:\n> {analysis}\n\n"

        if result.get("value_reason"):
            content += (
                "\n#### ⚡ 价值评估\n\n<details>\n<summary>展开查看详细评估</summary>\n\n"
                f"{result.get('value_reason')}\n</details>\n"
            )

        if result.get("recent_commits"):
            content += "\n#### 📝 最近提交\n\n"
            for commit in result["recent_commits"][:5]:
                if isinstance(commit, dict):
                    message = str(commit.get("message", "")).split("\n")[0]
                    commit_date = commit.get("date", "")
                    if message and commit_date:
                        content += f"- **{commit_date}**: {message}\n"
        return content

    def save_analysis_result(self, result: dict[str, Any], source_type: str) -> bool:
        """保存分析结果到当日 Markdown 报告。"""
        try:
            repo_name = self._extract_repo_name(result, source_type)
            if repo_name and not self._check_repository_limit(repo_name):
                logger.info("仓库 %s 今日已记录，跳过写入", repo_name)
                return False

            today = datetime.now()
            filename = os.path.join(self.ai_analysis_dir, f"Ai_{today.strftime('%Y_%m_%d')}.md")
            identifier = result.get("cve_id") if source_type == "cve" else result.get("repository_name")
            if not identifier:
                logger.warning("分析结果缺少唯一标识，跳过写入")
                return False

            if not os.path.exists(filename):
                header = (
                    f"# AI 安全分析日报 ({today.strftime('%Y-%m-%d')})\n\n"
                    "本文档包含 AI 对安全相关内容的自动化分析结果。"
                    "[概览](https://blog.897010.xyz/c/today)\n\n"
                )
                with open(filename, "w", encoding="utf-8") as f:
                    f.write(header)

            with open(filename, "r", encoding="utf-8") as f:
                existing_content = f.read()

            if f"### {identifier}" in existing_content:
                logger.info("内容已存在，跳过: %s", identifier)
                return False

            short_desc = str(result.get("short_description", "")).strip()
            desc_text = f" - {short_desc}" if short_desc else ""

            if source_type == "cve":
                content = f"\n### {identifier}{desc_text}\n\n"
                content += "#### 📌 漏洞信息\n\n| 属性 | 详情 |\n|------|------|\n"
                content += f"| CVE编号 | {result.get('cve_id')} |\n"
                content += f"| 风险等级 | `{result.get('risk_level')}` |\n"
                content += f"| 利用状态 | `{result.get('exploit_status')}` |\n"
                if result.get("published_date"):
                    content += f"| 发布时间 | {result.get('published_date')} |\n"
                if result.get("last_modified"):
                    content += f"| 最后更新 | {result.get('last_modified')} |\n"
                if result.get("repository_url"):
                    repo_url = result.get("repository_url")
                    content += "\n#### 📦 相关仓库\n\n"
                    content += f"- [{str(repo_url).split('/')[-1]}]({repo_url})\n"
            else:
                content = f"\n### {identifier}{desc_text}\n\n"
                content += "#### 📌 仓库信息\n\n| 属性 | 详情 |\n|------|------|\n"
                content += (
                    f"| 仓库名称 | [{result.get('repository_name')}]({result.get('repository_url')}) |\n"
                )
                content += f"| 风险等级 | `{result.get('risk_level')}` |\n"
                content += f"| 安全类型 | `{result.get('security_type')}` |\n"
                if result.get("update_type"):
                    content += f"| 更新类型 | `{result.get('update_type')}` |\n"
                if result.get("commits_analyzed") or result.get("files_changed"):
                    content += "\n#### 📊 代码统计\n\n"
                    if result.get("commits_analyzed"):
                        content += f"- 分析提交数: **{result.get('commits_analyzed')}**\n"
                    if result.get("files_changed"):
                        content += f"- 变更文件数: **{result.get('files_changed')}**\n"

            content += self._build_common_sections(result)
            content += "\n---\n"

            with open(filename, "a", encoding="utf-8") as f:
                f.write(content)

            logger.info("已保存分析结果到: %s", filename)
            return True
        except Exception as exc:
            logger.error("保存分析结果失败: %s", str(exc), exc_info=True)
            return False

    def convert_and_update_blog(self) -> bool:
        """将当天 Markdown 转 HTML 并同步到博客。"""
        try:
            today = datetime.now().strftime("%Y_%m_%d")
            md_file = os.path.join(self.ai_analysis_dir, f"Ai_{today}.md")
            html_file = os.path.join(self.html_output_dir, f"Ai_{today}.html")

            if not os.path.exists(md_file):
                logger.info("今天没有AI分析结果，跳过博客更新")
                return False

            with open(md_file, "r", encoding="utf-8") as f:
                content = f.read()
            if not content.strip():
                logger.info("今天的AI分析结果为空，跳过博客更新")
                return False

            convert_md_to_html(md_file)
            if not os.path.exists(html_file):
                logger.error("Markdown 转换 HTML 失败")
                return False

            with open(html_file, "r", encoding="utf-8") as f:
                html_content = f.read()

            success = self.blog_manager.update_html_content(html_content)
            if success:
                logger.info("成功更新博客的 HTML 内容")
            else:
                logger.error("更新博客 HTML 内容失败")
            return success
        except Exception as exc:
            logger.error("转换并更新博客失败: %s", str(exc), exc_info=True)
            return False
