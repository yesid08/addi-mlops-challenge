import os
import sys
from pathlib import Path

# Provide a fake key before any module-level import that triggers BaseSettings validation.
os.environ.setdefault("OPENAI_API_KEY", "sk-test-fake-key-for-tests")

# Make the project root importable so `source.*` and `deliverables.*` resolve correctly.
_PROJECT_ROOT = str(Path(__file__).parents[3])
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)
