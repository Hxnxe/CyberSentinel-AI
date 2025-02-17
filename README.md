# CyberSentinel AI - 自动化安全监控与AI分析系统

[![License](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

[English README](README_EN.md) | [中文 README](README_ZH.md)

---

**CyberSentinel AI** 是一个强大的自动化安全监控与AI分析系统，旨在帮助安全研究人员和爱好者 **实时追踪最新的安全漏洞 (CVE)** 和 **GitHub 上的安全相关仓库**，并利用 **人工智能技术**进行深度分析，最终将有价值的安全情报 **自动发布到博客平台**。

**🚀  功能亮点**

*   **多源数据监控** (CVE & GitHub 仓库)
*   **智能 AI 分析** (OpenAI & Gemini 双引擎)
*   **全自动化工作流** (7x24 监控、每日简报、动态黑名单)
*   **灵活的配置与管理** (多 Token 支持、可配置参数、详细日志)
*   **博客自动发布** (集成博客平台、Markdown 报告)

**🛠️  技术实现**

*   **监控模块 (Monitors)**: `cve_monitor.py`, `github_monitor.py`
*   **AI 分析模块 (AI)**: `analyzer.py`
*   **数据处理与管理 (Utils)**: `logger.py`, `csv_writer.py`, `article_fetcher.py`, `article_manager.py`, `blog_manager.py`
*   **数据库 (Database)**: `database/models.py`
*   **配置文件 (Config)**: `config.py`
*   **主程序 (Main)**: `main.py`

**⚙️  运行环境**

*   Python 3.8+
*   依赖库 (见 `requirements.txt`)

**📦  安装步骤**

请参考 [English README](README_EN.md) 或 [中文 README](README_ZH.md) 中的详细安装步骤。

**📝  后续计划**

*   更多数据源支持
*   更精细化的 AI 分析
*   更丰富的功能
*   Web UI 管理界面

**🤝  贡献**

欢迎参与项目贡献！如果您有任何建议或 Bug 报告，请提交 Issue 或 Pull Request。

**📜  许可证**

本项目采用 MIT 许可证，详情请见 [LICENSE](LICENSE) 文件。

---

**感谢您的关注！**  ⭐  **Star**  本项目以支持我们的工作！
