# syntax=docker/dockerfile:1
# Multi-arch (amd64 + arm64) — runs identically on Linux/macOS/Windows/Raspberry Pi.
#   Build: docker build -t grand-log reel-pipeline/
#   Run:   docker run --rm -v "$PWD/work:/app/work" grand-log "<reel-url>" --dry-run
# (The long-running Den Den Mushi bot service + compose.yaml land with the bot.)
FROM python:3.12-slim AS runtime

# Real ffmpeg binary (NOT `pip install ffmpeg`) — required by yt-dlp + whisper
RUN apt-get update \
    && apt-get install -y --no-install-recommends ffmpeg ca-certificates \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY pipeline ./pipeline

# Mount these as volumes: model cache downloads once, work/ holds output.
ENV HF_HOME=/cache/huggingface OMP_NUM_THREADS=4
RUN useradd -m appuser \
    && mkdir -p /cache/huggingface /app/work \
    && chown -R appuser /cache /app/work
USER appuser

ENTRYPOINT ["python", "-m", "pipeline.process"]
CMD ["--help"]
