FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive

# Install git, python, and cleanup
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    git \
    python3 \
    python3-pip \
    curl \
    && apt-get clean && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY cd ..

CMD ["python" "agent.py" "dev"]