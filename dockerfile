FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    git \
    python3 \
    python3-pip \
    python3-venv \
    curl \
    && apt-get clean && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY . .

RUN python3 -m venv /app/venv

RUN . /app/venv/bin/activate && pip install --upgrade pip && pip install -r requirements.txt

CMD ["/app/venv/bin/python", "agent.py", "dev"]
