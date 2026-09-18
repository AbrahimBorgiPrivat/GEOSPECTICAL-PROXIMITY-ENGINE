import sys
from pathlib import Path

SRC_ROOT = Path(__file__).parents[1]
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))
