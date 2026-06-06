# 快速开始

## 1. 安装

```bash
git clone https://github.com/Hxnxe/CyberSentinel-AI.git
cd CyberSentinel-AI

bash scripts/bootstrap.sh
```

脚本会完成：

- 创建 `.venv`
- 安装依赖
- 如果 `.env` 不存在，则从 `.env.example` 复制
- 运行配置自检

## 2. 编辑配置

```bash
nano .env
```

至少建议配置：

```dotenv
GITHUB_TOKENS=["你的 GitHub Token"]
PRIMARY_AI_KEY=你的 AI API Key
PRIMARY_AI_BASE=https://api.openai.com/v1
PRIMARY_AI_MODEL=gpt-4.1-nano
```

## 3. 自检

```bash
source .venv/bin/activate
python main.py --check-config
```

如果 `github` 或 `ai` 显示 `WARN`，说明对应 Token/API Key 未配置。测试仍然可以运行，但正式监控效果会受影响。

## 4. 测试

```bash
python -m pytest -q
```

## 5. 启动

```bash
python main.py
```

停止时按 `Ctrl+C`。
