"""Project Campus — Safe Administrative Password Reset Utility (Root Wrapper).

Allows executing the utility from repository root or host terminal:
    python scripts/reset_password.py --email student@example.com
"""

from pathlib import Path
import sys

ROOT_DIR = Path(__file__).resolve().parent.parent
BACKEND_SCRIPTS = ROOT_DIR / "backend" / "scripts"

if str(BACKEND_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(BACKEND_SCRIPTS))

from reset_password import main

if __name__ == "__main__":
    main()
