"""ASGI entrypoint proxy for Render and standalone deployments.

This module re-exports the configured FastAPI application instance from
`backend.app.main` while ensuring that the repository root is in `sys.path`.
This allows `uvicorn main:app` to succeed seamlessly when Render's Root Directory
is set to `backend`.
"""

import os
import sys

# Ensure parent directory (repo root) is on sys.path so 'backend.app...' absolute imports resolve
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(CURRENT_DIR)

if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)
if CURRENT_DIR not in sys.path:
    sys.path.insert(0, CURRENT_DIR)

from backend.app.main import app, create_app  # noqa: E402

__all__ = ["app", "create_app"]
