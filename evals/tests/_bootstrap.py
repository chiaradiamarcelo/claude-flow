"""Put the evals/ dir on sys.path so tests can `import check_routing` and
`from harness.agent import ...` regardless of where unittest is invoked from."""
import sys
from pathlib import Path

EVALS_DIR = Path(__file__).resolve().parents[1]
if str(EVALS_DIR) not in sys.path:
    sys.path.insert(0, str(EVALS_DIR))
