# syntax=docker/dockerfile:1
ARG PYTHON_VERSION=3.11.6
FROM python:${PYTHON_VERSION}-slim

ENV PYTHONUNBUFFERED=1

ARG PROGRAM_MAIN="leadAgent.py"
ARG UID=10001

# Create non-privileged user
RUN adduser \
    --disabled-password \
    --gecos "" \
    --home "/home/appuser" \
    --shell "/sbin/nologin" \
    --uid "${UID}" \
    appuser

# Install build dependencies
RUN apt-get update && \
    apt-get install -y gcc python3-dev && \
    rm -rf /var/lib/apt/lists/*

# Create RAG build directories as root and give appuser ownership
RUN mkdir -p /home/appuser/rag_build/chroma_db && \
    chown -R ${UID}:${UID} /home/appuser/rag_build

WORKDIR /home/appuser

# Copy requirements and install
COPY requirements.txt .
RUN python -m pip install --no-cache-dir -r requirements.txt

# Copy all application code
COPY . .

# ---- Build-time API keys ----
ARG OPENAI_API_KEY
ARG TAVILY_API_KEY
ENV OPENAI_API_KEY=${OPENAI_API_KEY}
ENV TAVILY_API_KEY=${TAVILY_API_KEY}

# Switch to non-privileged user
USER appuser

# Build RAG data at build time
# RUN python rag_build/build_rag_data.py

# Expose LiveKit healthcheck port
EXPOSE 8081

# Start the agent at runtime
CMD ["sh", "-c", "python rag_build/build_rag_data.py & python leadAgent.py start"]
