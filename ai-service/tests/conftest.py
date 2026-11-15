import os
import sys

# Make `gnn`, `rag`, `agent`, `main` importable when running `pytest` from ai-service/
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
