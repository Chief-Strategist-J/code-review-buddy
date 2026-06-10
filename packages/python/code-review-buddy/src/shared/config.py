import os
from pathlib import Path

# Hardcoded repository root as required by assignment, fallback to environment variable for flexibility
REPO_ROOT = os.environ.get("REPO_ROOT", "/home/btpl-lap-22/live/codeReview")
REPO_ROOT = str(Path(REPO_ROOT).resolve())
