"""PDF Intelligence RAG Application Package."""

import os
import sys

# Ensure repository root is on sys.path so 'backend.app...' absolute imports
# resolve regardless of whether the working directory is the repository root or 'backend/'.
_app_dir = os.path.dirname(os.path.abspath(__file__))
_backend_dir = os.path.dirname(_app_dir)
_repo_root = os.path.dirname(_backend_dir)

if _repo_root not in sys.path:
    sys.path.insert(0, _repo_root)
