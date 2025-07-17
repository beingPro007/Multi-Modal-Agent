FROM python:3.13-slim

# Set working directory
WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential ffmpeg git \
    && rm -rf /var/lib/apt/lists/*

ENV VENV_PATH=/opt/venv
RUN python -m venv $VENV_PATH
ENV PATH="$VENV_PATH/bin:$PATH"

COPY requirements.txt .
RUN $VENV_PATH/bin/pip install --upgrade pip \
    && $VENV_PATH/bin/pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "agent.py", "dev"]
