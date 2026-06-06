#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

python3 -m venv .venv
. .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt

if [ ! -f .env ]; then
  cp .env.example .env
  echo "Created .env from .env.example. Edit .env with your own tokens before real monitoring."
else
  echo ".env already exists; leaving it unchanged."
fi

python main.py --check-config
echo "Bootstrap complete. Run: source .venv/bin/activate && python main.py"
