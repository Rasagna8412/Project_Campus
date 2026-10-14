"""Project Campus — Milestone 2 Comprehensive Verification Script.

Executes all backend and frontend automated checks, database migrations, and builds to verify Milestone 2 readiness.
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

    python_exe = ROOT_DIR / ".venv" / "Scripts" / "python.exe"
    if not python_exe.exists():
        python_exe = Path(sys.executable)

    # 1. Backend Pytest Suite (Auth, Onboarding, Authorization, Health)
    pytest_cmd = [str(python_exe), "-m", "pytest", "-v", "tests"]
    results["Backend Test Suite (Pytest)"] = run_command(
        pytest_cmd, ROOT_DIR, "Backend Pytest (Auth, Onboarding, Authorization, Health)"
    )

    # 2. Database Migration Check (Alembic Current)
    alembic_cmd = [str(python_exe), "-m", "alembic", "current"]
    results["Alembic Migration Current"] = run_command(
        alembic_cmd, ROOT_DIR / "backend", "Alembic Migration Verification (eeac6986a79e)"
    )

    # 3. Frontend Vitest Test Suite
    npm_cmd = "npm.cmd" if sys.platform == "win32" else "npm"
    vitest_cmd = [npm_cmd, "test", "--", "--run"]
    results["Frontend Vitest Suite"] = run_command(
        vitest_cmd, ROOT_DIR / "frontend", "Frontend Vitest (App, Auth, Onboarding)"
    )

    # 4. Frontend Type Check & Production Build
    build_cmd = [npm_cmd, "run", "build"]
    results["Frontend Build & Type Check"] = run_command(
        build_cmd, ROOT_DIR / "frontend", "Frontend TypeScript & Vite Build"
    )

    print("\n" + "=" * 60)
    print("PROJECT CAMPUS — MILESTONE 2 VERIFICATION SUMMARY")
    print("=" * 60)
    all_passed = True
    for test_name, passed in results.items():
        status_str = "PASSED" if passed else "FAILED"
        print(f"[{status_str}] - {test_name}")
        if not passed:
            all_passed = False

    if all_passed:
        print("\nALL MILESTONE 2 VERIFICATION CHECKS PASSED SUCCESSFULLY!")
        sys.exit(0)
    else:
        print("\nSOME CHECKS FAILED. Please review the output above.")
        sys.exit(1)


if __name__ == "__main__":
    main()
