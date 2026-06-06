# CyberSentinel AI

CyberSentinel AI 是一个自动化安全监控与 AI 分析系统，用于跟踪 CVE 相关仓库、安全工具仓库和安全文章，生成本地 Markdown/HTML 报告，并可选发布到博客服务。

## 功能概览

- 监控 GitHub 上的 CVE/POC 相关仓库。
- 按关键词搜索安全工具、漏洞利用、攻防研究等仓库。
- 重点跟踪配置中的固定仓库列表。
- 使用 OpenAI 兼容接口和 Gemini 做 AI 辅助分析。
- 使用 SQLite 保存监控状态和分析记录。
- 生成 Markdown/HTML 报告。
- 配置 `BLOG_TOKEN` 后可自动同步到博客；未配置时自动跳过博客发布。

## 快速开始

```bash
git clone https://github.com/Hxnxe/CyberSentinel-AI.git
cd CyberSentinel-AI

python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env
python main.py --check-config
python -m pytest -q
python main.py
```

项目在没有真实密钥时也可以导入和运行测试。正式监控前请编辑 `.env`。

也可以直接使用引导脚本：

```bash
bash scripts/bootstrap.sh
```

## 最小可用配置

复制模板：

```bash
cp .env.example .env
```

编辑 `.env`：

```dotenv
GITHUB_TOKENS=["替换为你自己的 GitHub Token"]
PRIMARY_AI_KEY=替换为你自己的 AI API Key
PRIMARY_AI_BASE=https://api.openai.com/v1
PRIMARY_AI_MODEL=gpt-4.1-nano
```

说明：

- `GITHUB_TOKENS` 推荐配置，否则 GitHub API 很容易触发频率限制。
- `PRIMARY_AI_KEY` 用于 OpenAI 兼容接口。
- `BACKUP_AI_CONFIGS` 可以配置多个备用 OpenAI 兼容服务。
- `GEMINI_AI_KEY` 是可选 Gemini 兜底。
- `BLOG_TOKEN` 为空时不会请求博客接口，只在本地生成报告。

## 常用命令

运行测试：

```bash
python main.py --check-config
python -m pytest -q
```

启动监控：

```bash
python main.py
```

如果安装为可编辑包，也可以运行：

```bash
pip install -e .
cybersentinel-ai
```

## 目录结构

```text
ai/          AI 客户端、Prompt、Schema、结果验证和分析逻辑
clients/     GitHub API 客户端
database/    SQLAlchemy 模型、会话、仓储和初始化逻辑
monitors/    CVE 监控器和 GitHub 仓库监控器
reports/     Markdown/HTML 报告生成
utils/       日志、文章、黑名单、博客、CSV、Markdown 工具
scripts/     初始化脚本和配置自检脚本
docs/        配置、快速开始和部署说明
tests/       pytest 测试套件
main.py      主程序入口
config.py    基于环境变量的配置入口
```

更多说明：

- [中文快速开始](docs/QUICKSTART_ZH.md)
- [配置说明](docs/CONFIGURATION.md)
- [部署说明](docs/DEPLOYMENT.md)

## 不会发布的文件

以下内容属于本地运行产物或敏感信息，已在 `.gitignore` 中排除：

```text
.env
.env.*
venv/
.venv/
logs/
results/
data/
cve_database.db
*.db
*.sqlite
__pycache__/
.pytest_cache/
```

请不要提交真实 Token、数据库、日志、运行结果或虚拟环境。

## 配置说明

主要配置来自 `.env`：

| 变量 | 说明 |
| --- | --- |
| `MONITOR_INTERVAL` | 监控循环间隔，默认 7200 秒 |
| `DATABASE_PATH` | SQLite 数据库路径，默认 `cve_database.db` |
| `GITHUB_TOKENS` | GitHub Token JSON 数组 |
| `GITHUB_TOKEN` | 单 GitHub Token 兜底 |
| `PRIMARY_AI_KEY` | 主 AI 服务 API Key |
| `PRIMARY_AI_BASE` | 主 AI 服务 Base URL |
| `PRIMARY_AI_MODEL` | 主 AI 服务模型名 |
| `BACKUP_AI_CONFIGS` | 备用 AI 服务 JSON 数组 |
| `GEMINI_AI_KEY` | Gemini API Key |
| `BLOG_BASE_URL` | 博客服务地址 |
| `BLOG_TOKEN` | 博客发布 Token，留空则跳过博客发布 |

## 许可证

本项目使用 MIT 许可证。详见 [LICENSE](LICENSE)。
