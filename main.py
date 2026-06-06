from __future__ import annotations

import os
import argparse
import signal
import time
from datetime import datetime, timedelta
from queue import Empty, Queue
from threading import Event, Thread
from typing import Any

from ai.analyzer import SecurityAnalyzer
from ai.llm_client import LLMClient
from clients.github_client import GithubClient
from config import BLOG_BASE_URL, BLOG_TOKEN, MONITOR_INTERVAL, settings
from database.init_db import init_database
from database.session import SessionFactory, get_engine
from monitors.cve_monitor import CVEMonitor
from monitors.github_monitor import GithubMonitor
from reports.generator import ReportGenerator
from utils.article_fetcher import ArticleFetcher
from utils.article_manager import ArticleManager
from utils.blacklist_manager import BlacklistManager
from utils.blog_manager import BlogManager
from utils.config_diagnostics import build_config_diagnostics, format_config_diagnostics
from utils.logger import get_logger

logger = get_logger("security_monitor.main")
ARTICLE_FETCH_INTERVAL = 2 * 60 * 60
VERSION = "0.1.0"


class SecurityMonitorSystem:
    """安全监控系统编排层。"""

    def __init__(self) -> None:
        self.engine = get_engine()
        init_database()
        self.session_factory = SessionFactory(self.engine)

        self.github_client = GithubClient()
        self.blacklist_manager = BlacklistManager()
        self.llm_client = LLMClient()

        self.blog_manager = BlogManager(base_url=BLOG_BASE_URL, token=BLOG_TOKEN)
        self.report_generator = ReportGenerator(
            session_factory=self.session_factory,
            blog_manager=self.blog_manager,
        )

        self.analyzer = SecurityAnalyzer(
            llm_client=self.llm_client,
            blacklist_manager=self.blacklist_manager,
            engine=self.engine,
            session_factory=self.session_factory,
        )

        self.cve_monitor = CVEMonitor(
            self.engine,
            github_client=self.github_client,
            blacklist_manager=self.blacklist_manager,
            session_factory=self.session_factory,
        )
        self.github_monitor = GithubMonitor(
            self.engine,
            github_client=self.github_client,
            blacklist_manager=self.blacklist_manager,
            session_factory=self.session_factory,
        )

        self.article_fetcher = ArticleFetcher()
        self.article_manager = ArticleManager(self.analyzer, blog_manager=self.blog_manager)

        self.data_queue: Queue[tuple[str, dict[str, Any]]] = Queue()
        self.stop_event = Event()
        self.last_article_fetch: datetime | None = None

    def _handle_signal(self, signum: int, _frame: Any) -> None:
        logger.info("接收到退出信号: %s", signum)
        self.stop_event.set()

    def _setup_signals(self) -> None:
        signal.signal(signal.SIGINT, self._handle_signal)
        signal.signal(signal.SIGTERM, self._handle_signal)

    def run_analysis(self) -> None:
        logger.info("AI分析线程启动")
        consecutive_errors = 0

        while not self.stop_event.is_set():
            task_acquired = False
            source_type = "unknown"

            try:
                source_type, data = self.data_queue.get(timeout=1)
                task_acquired = True

                if source_type == "cve":
                    result = self.analyzer.analyze_cve(data)
                else:
                    result = self.analyzer.analyze_repository(data)

                if result and result.get("is_valuable", False):
                    self.report_generator.save_analysis_result(result, source_type)
                consecutive_errors = 0
            except Empty:
                continue
            except Exception as exc:
                consecutive_errors += 1
                logger.error(
                    "AI分析线程异常(连续%s次): %s",
                    consecutive_errors,
                    str(exc),
                    exc_info=True,
                )
                if self.stop_event.wait(min(consecutive_errors, 5)):
                    break
            finally:
                if task_acquired:
                    try:
                        self.data_queue.task_done()
                    except ValueError:
                        logger.warning("task_done 调用异常，source_type=%s", source_type)

    def process_articles(self) -> None:
        logger.info("开始处理安全文章")
        today_str = datetime.now().strftime("%Y-%m-%d")
        daily_report_path = os.path.join("results/daily_articles", f"{today_str}.md")
        ai_report_path = os.path.join(self.report_generator.ai_analysis_dir, f"Ai_{datetime.now().strftime('%Y_%m_%d')}.md")

        try:
            os.makedirs(os.path.dirname(daily_report_path), exist_ok=True)
            articles = self.article_fetcher.get_doonsec_articles()
            new_articles = self.article_manager.filter_new_articles(articles)

            if new_articles:
                logger.info("发现 %s 篇新文章", len(new_articles))
                analysis_result = self.article_manager.process_articles(new_articles)
                self.article_manager.generate_daily_report(analysis_result, daily_report_path)
                return

            logger.info("没有发现新文章")
            if os.path.exists(ai_report_path) and os.path.getsize(ai_report_path) > 0:
                with open(ai_report_path, "r", encoding="utf-8") as ai_file:
                    ai_content = ai_file.read()
                with open(daily_report_path, "w", encoding="utf-8") as daily_file:
                    daily_file.write(f"# 每日安全资讯 ({today_str})\n\n")
                    daily_file.write("今日未发现新的安全文章，以下是 AI 分析结果：\n\n")
                    daily_file.write(ai_content)
            elif not os.path.exists(daily_report_path):
                with open(daily_report_path, "w", encoding="utf-8") as daily_file:
                    daily_file.write(f"# 每日安全资讯 ({today_str})\n\n")
                    daily_file.write("今日未发现新的安全文章，也无 AI 分析结果。\n\n")
        except Exception as exc:
            logger.error("处理文章失败: %s", str(exc), exc_info=True)

    def run_monitoring(self) -> None:
        logger.info("监控线程启动")
        while not self.stop_event.is_set():
            try:
                self.data_queue.join()
                data_found = False
                start_time = datetime.now()

                logger.info("开始CVE监控")
                cve_data = self.cve_monitor.fetch_latest_cves()
                if cve_data:
                    cves_to_analyze = self.cve_monitor.process_cve_data(cve_data)
                    for cve in cves_to_analyze:
                        self.data_queue.put(("cve", cve))
                    data_found = data_found or bool(cves_to_analyze)
                    logger.info("本轮CVE待分析: %s", len(cves_to_analyze))

                logger.info("开始GitHub仓库监控")
                repos_to_analyze = self.github_monitor.run()
                for repo in repos_to_analyze:
                    if isinstance(repo, dict) and repo.get("name"):
                        self.data_queue.put(("repository", repo))
                        data_found = True
                logger.info("本轮仓库待分析: %s", len(repos_to_analyze))

                if data_found:
                    logger.info("等待本轮分析任务完成")
                    self.data_queue.join()

                if self.last_article_fetch is None or (start_time - self.last_article_fetch).total_seconds() >= ARTICLE_FETCH_INTERVAL:
                    self.process_articles()
                    self.last_article_fetch = start_time

                self.report_generator.convert_and_update_blog()

                end_time = datetime.now()
                duration = (end_time - start_time).total_seconds()
                logger.info(
                    "监控循环完成，用时 %.2f 秒，下次运行: %s",
                    duration,
                    (end_time + timedelta(seconds=MONITOR_INTERVAL)).strftime("%Y-%m-%d %H:%M:%S"),
                )

                if self.stop_event.wait(MONITOR_INTERVAL):
                    break
            except Exception as exc:
                logger.error("监控线程异常: %s", str(exc), exc_info=True)
                if self.stop_event.wait(300):
                    break

    def _run_status_check(self) -> None:
        logger.info("状态检查线程启动")
        last_status_time: datetime | None = None

        while not self.stop_event.is_set():
            try:
                current_time = datetime.now()
                if current_time.minute == 0 and current_time.second == 0:
                    if last_status_time is None or (current_time - last_status_time).total_seconds() >= 3600:
                        logger.info("监控系统运行正常，待分析队列: %s", self.data_queue.qsize())
                        last_status_time = current_time
                if self.stop_event.wait(10):
                    break
            except Exception as exc:
                logger.error("状态检查异常: %s", str(exc), exc_info=True)
                if self.stop_event.wait(60):
                    break

    def run(self) -> None:
        self._setup_signals()
        logger.info("安全监控系统启动")

        threads = [
            Thread(target=self.run_monitoring, name="MonitorThread", daemon=True),
            Thread(target=self.run_analysis, name="AnalysisThread", daemon=True),
            Thread(target=self._run_status_check, name="StatusThread", daemon=True),
        ]

        for thread in threads:
            thread.start()

        try:
            while not self.stop_event.wait(1):
                continue
        finally:
            logger.info("正在停止监控系统")
            self.stop_event.set()
            for thread in threads:
                thread.join(timeout=5)
                if thread.is_alive():
                    logger.warning("线程 %s 未在超时内退出", thread.name)
            logger.info("监控系统已停止")



def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="cybersentinel-ai",
        description="Automated CVE and security repository monitoring with AI analysis.",
    )
    parser.add_argument(
        "--check-config",
        action="store_true",
        help="print a non-sensitive configuration diagnostic report and exit",
    )
    parser.add_argument(
        "--init-db",
        action="store_true",
        help="initialize the SQLite database tables and exit",
    )
    parser.add_argument(
        "--version",
        action="store_true",
        help="print version information and exit",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_arg_parser().parse_args(argv)

    if args.version:
        print(f"CyberSentinel AI {VERSION}")
        return 0

    if args.check_config:
        print(format_config_diagnostics(build_config_diagnostics(settings)), end="")
        return 0

    if args.init_db:
        init_database()
        print(f"Database initialized at {settings.database_path}")
        return 0

    try:
        system = SecurityMonitorSystem()
        system.run()
    except KeyboardInterrupt:
        logger.info("程序被用户中断")
    except Exception as exc:
        logger.error("程序发生致命错误: %s", str(exc), exc_info=True)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
