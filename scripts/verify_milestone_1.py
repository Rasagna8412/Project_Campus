"""Project Campus — Milestone 1 Comprehensive Verification Script.

Executes all backend and frontend automated checks to verify readiness.
"""

import subprocess
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent


def run_command(cmd: list[str], cwd: Path, desc: str) -> bool:
    print(f"\n==================================================")
    print(f"RUNNING: {desc}")
    print(f"Command: {' '.join(cmd)}")
    print(f"Directory: {cwd}")
    print(f"==================================================")

    result = subprocess.run(cmd, cwd=cwd)
    if result.returncode == 0:
        print(f"PASS: {desc}")
        return True
    else:
        print(f"FAIL: {desc} (Exit code {result.returncode})")
        return False


def main():
    results = {}

    # 1. Backend Pytest
    python_exe = ROOT_DIR / ".venv" / "Scripts" / "python.exe"
    if not python_exe.exists():
        python_exe = Path(sys.executable)

    pytest_cmd = [str(python_exe), "-m", "pytest", "-v", "tests"]
    results["Backend Unit & Integration Tests"] = run_command(
        pytest_cmd, ROOT_DIR, "Backend Pytest Test Suite"
    )

    # 2. Database Migration Check (Alembic Current)
    alembic_cmd = [str(python_exe), "-m", "alembic", "current"]
    results["Alembic Migration Current"] = run_command(
        alembic_cmd, ROOT_DIR / "backend", "Alembic Migration Verification"
    )

    # 3. Frontend Type Check & Production Build
    npm_cmd = ["npm.cmd" if sys.platform == "win32" else "npm", "run", "build"]
    results["Frontend Build & Type Check"] = run_command(
        npm_cmd, ROOT_DIR / "frontend", "Frontend TypeScript & Vite Build"
    )

    print("\n" + "=" * 50)
    print("MILESTONE 1 VERIFICATION SUMMARY")
    print("=" * 50)
    all_passed = True
    for test_name, passed in results.items():
        status_str = "PASSED" if passed else "FAILED"
        print(f"[{status_str}] - {test_name}")
        if not passed:
            all_passed = False

    if all_passed:
        print("\nALL MILESTONE 1 VERIFICATION CHECKS PASSED SUCCESSFULLY!")
        sys.exit(0)
    else:
        print("\nSOME CHECKS FAILED. Please review the output above.")
        sys.exit(1)


if __name__ == "__main__":
    main()
