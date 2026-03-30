#!/usr/bin/env python3
"""Minimal workspace setup for fetch-and-save task."""

import os
import sys

workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
os.makedirs(workspace, exist_ok=True)
print(f"Workspace ready: {workspace}")
