FROM python:3.12-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    coreutils diffutils findutils && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /workspace

# Seed files are created by the setup script
COPY setup_workspace.py /setup_workspace.py
RUN python3 /setup_workspace.py "/workspace"
