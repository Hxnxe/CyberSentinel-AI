#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from reports.action_report import collect_report_data, write_report  # noqa: E402


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="generate-report",
        description="Generate a one-shot CyberSentinel AI report for GitHub Actions artifacts.",
    )
    parser.add_argument(
        "--output",
        default="artifacts/github-security-report.md",
        help="Markdown output path. Default: artifacts/github-security-report.md",
    )
    parser.add_argument(
        "--max-items",
        type=int,
        default=20,
        help="Maximum CVE and repository candidates to include per section. Default: 20",
    )
    parser.add_argument(
        "--keyword-limit",
        type=int,
        default=5,
        help="Maximum search keywords to use when REPORT_KEYWORDS is not supplied. Default: 5",
    )
    parser.add_argument(
        "--keywords",
        default=None,
        help="Comma or newline separated keyword list. Defaults to project security keywords.",
    )
    parser.add_argument(
        "--database-path",
        default="github-actions-report.db",
        help="SQLite database path for this one-shot run. Default: github-actions-report.db",
    )
    parser.add_argument(
        "--skip-cve",
        action="store_true",
        help="Skip CVE candidate collection.",
    )
    parser.add_argument(
        "--skip-repositories",
        action="store_true",
        help="Skip repository candidate collection.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    report_data = collect_report_data(
        max_items=args.max_items,
        keyword_limit=args.keyword_limit,
        keywords=args.keywords,
        include_cve=not args.skip_cve,
        include_repositories=not args.skip_repositories,
        database_path=args.database_path,
    )
    path = write_report(args.output, report_data)
    print(f"Report written to {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
