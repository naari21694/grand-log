#!/usr/bin/env bash
# Grand Log local install (Linux/macOS). Run: bash scripts/install.sh
set -euo pipefail

cd "$(dirname "$0")/../reel-pipeline"

if ! command -v ffmpeg >/dev/null 2>&1; then
  echo "WARNING: ffmpeg is not on PATH. Install it (apt install ffmpeg / brew install ffmpeg)."
fi

python3 -m venv .venv
# shellcheck disable=SC1091
. .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

if [ ! -f .env ]; then
  cp .env.example .env
  echo "Created reel-pipeline/.env from the template."
fi

echo
echo "Next: edit reel-pipeline/.env and add a brain key (free Gemini key at aistudio.google.com)."
echo "Then check your setup:"
echo "  cd reel-pipeline && . .venv/bin/activate && python -m pipeline.doctor"
echo
python -m pipeline.doctor || true
