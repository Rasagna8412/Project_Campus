"""Regression and failure-recovery tests for PostgreSQL backup script (scripts/backup_postgres.sh)."""

import os
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path
import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
BACKUP_SCRIPT = REPO_ROOT / "scripts" / "backup_postgres.sh"


def get_bash_executable():
    """Locate appropriate bash interpreter across Linux CI and Windows Git Bash."""
    if sys.platform == "win32":
        git_bash = Path(r"C:\Program Files\Git\bin\bash.exe")
        if git_bash.exists():
            return str(git_bash)
    found = shutil.which("bash")
    if found and "system32" not in found.lower():
        return found
    return "bash"


@pytest.fixture
def backup_env():
    """Create isolated temporary backup directory and mock bin directory for testing."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        backup_dir = tmp_path / "backups"
        backup_dir.mkdir(parents=True, exist_ok=True)
        bin_dir = tmp_path / "bin"
        bin_dir.mkdir(parents=True, exist_ok=True)

        yield {
            "root": tmp_path,
            "backup_dir": backup_dir,
            "bin_dir": bin_dir,
            "bash": get_bash_executable(),
        }


def create_mock_docker(bin_dir: Path, behavior: str):
    """Create mock docker executable to simulate pg_dump and pg_restore outcomes."""
    mock_docker_script = bin_dir / "docker"
    # POSIX shell script for mock docker
    if behavior == "success":
        content = """#!/bin/sh
if [ "$1" = "ps" ]; then
    echo "campus_postgres_prod"
    exit 0
elif [ "$1" = "exec" ]; then
    # Check if pg_dump or pg_restore
    case "$*" in
        *pg_dump*)
            printf "PGDUMP_MOCK_DATA_VALID_ARCHIVE"
            exit 0
            ;;
        *pg_restore*)
            exit 0
            ;;
        *)
            exit 0
            ;;
    esac
fi
exit 0
"""
    elif behavior == "dump_failure":
        content = """#!/bin/sh
if [ "$1" = "ps" ]; then
    echo "campus_postgres_prod"
    exit 0
elif [ "$1" = "exec" ]; then
    case "$*" in
        *pg_dump*)
            printf "PARTIAL_TRUNCATED_DUMP_DATA"
            exit 1
            ;;
        *)
            exit 1
            ;;
    esac
fi
exit 1
"""
    elif behavior == "restore_validation_failure":
        content = """#!/bin/sh
if [ "$1" = "ps" ]; then
    echo "campus_postgres_prod"
    exit 0
elif [ "$1" = "exec" ]; then
    case "$*" in
        *pg_dump*)
            printf "MOCK_DUMP_HEADER_CORRUPTED"
            exit 0
            ;;
        *pg_restore*)
            echo "pg_restore: error: corrupted header" >&2
            exit 1
            ;;
        *)
            exit 0
            ;;
    esac
fi
exit 0
"""
    elif behavior == "sigterm":
        content = """#!/bin/sh
if [ "$1" = "ps" ]; then
    echo "campus_postgres_prod"
    exit 0
elif [ "$1" = "exec" ]; then
    case "$*" in
        *pg_dump*)
            printf "PARTIAL_TRUNCATED_DUMP_DATA"
            kill -s TERM $PPID 2>/dev/null || kill -15 $PPID
            sleep 1
            exit 1
            ;;
        *)
            exit 1
            ;;
    esac
fi
exit 1
"""
    elif behavior == "sigint":
        content = """#!/bin/sh
if [ "$1" = "ps" ]; then
    echo "campus_postgres_prod"
    exit 0
elif [ "$1" = "exec" ]; then
    case "$*" in
        *pg_dump*)
            printf "PARTIAL_TRUNCATED_DUMP_DATA"
            kill -s INT $PPID 2>/dev/null || kill -2 $PPID
            sleep 1
            exit 1
            ;;
        *)
            exit 1
            ;;
    esac
fi
exit 1
"""
    else:
        raise ValueError(f"Unknown behavior: {behavior}")

    mock_docker_script.write_text(content, encoding="utf-8")
    mock_docker_script.chmod(0o755)
    return mock_docker_script


def run_backup_script(backup_env, mock_behavior: str):
    """Execute backup_postgres.sh with mock docker on PATH."""
    create_mock_docker(backup_env["bin_dir"], mock_behavior)

    # Convert Windows paths to POSIX if running in Git Bash
    backup_dir_posix = str(backup_env["backup_dir"]).replace("\\", "/")
    if sys.platform == "win32" and len(backup_dir_posix) > 1 and backup_dir_posix[1] == ":":
        backup_dir_posix = f"/{backup_dir_posix[0].lower()}{backup_dir_posix[2:]}"

    env = os.environ.copy()
    env["PATH"] = f"{backup_env['bin_dir']}{os.pathsep}{env.get('PATH', '')}"
    env["BACKUP_DIR"] = backup_dir_posix
    env["RETENTION_DAYS"] = "7"
    env["CONTAINER_NAME"] = "campus_postgres_prod"

    proc = subprocess.run(
        [backup_env["bash"], str(BACKUP_SCRIPT).replace("\\", "/")],
        env=env,
        capture_output=True,
        text=True,
    )
    return proc


def test_backup_success_promotes_dump_and_cleans_tmp(backup_env):
    """Verify that a successful backup generates a valid .dump file and leaves no .tmp files."""
    # Pre-create an existing valid backup
    existing_dump = backup_env["backup_dir"] / "campus_project_campus_prod_20260101_000000.dump"
    existing_dump.write_text("EXISTING_VALID_BACKUP", encoding="utf-8")

    result = run_backup_script(backup_env, mock_behavior="success")
    assert result.returncode == 0, f"Script failed: {result.stderr}"

    # Verify that existing backup is preserved
    assert existing_dump.exists()
    assert existing_dump.read_text(encoding="utf-8") == "EXISTING_VALID_BACKUP"

    # Verify that new promoted backup exists
    new_dumps = list(backup_env["backup_dir"].glob("campus_project_campus_prod_*.dump"))
    assert len(new_dumps) == 2

    # Verify that NO .tmp files remain
    tmp_files = list(backup_env["backup_dir"].glob("*.tmp"))
    assert len(tmp_files) == 0


def test_backup_dump_failure_cleans_up_partial_artifact(backup_env):
    """Verify that if pg_dump fails midway, the partial .tmp file is purged and no corrupt .dump is saved."""
    existing_dump = backup_env["backup_dir"] / "campus_project_campus_prod_20260101_000000.dump"
    existing_dump.write_text("EXISTING_VALID_BACKUP", encoding="utf-8")

    result = run_backup_script(backup_env, mock_behavior="dump_failure")
    assert result.returncode != 0

    # Verify existing backup is preserved
    assert existing_dump.exists()

    # Verify NO new .dump files were created
    dumps = list(backup_env["backup_dir"].glob("campus_project_campus_prod_*.dump"))
    assert len(dumps) == 1
    assert dumps[0].name == "campus_project_campus_prod_20260101_000000.dump"

    # Verify NO .tmp artifacts remain
    tmp_files = list(backup_env["backup_dir"].glob("*.tmp"))
    assert len(tmp_files) == 0


def test_backup_validation_failure_purges_artifact(backup_env):
    """Verify that if pg_restore validation fails, the corrupt artifact is purged and exit code is 1."""
    existing_dump = backup_env["backup_dir"] / "campus_project_campus_prod_20260101_000000.dump"
    existing_dump.write_text("EXISTING_VALID_BACKUP", encoding="utf-8")

    result = run_backup_script(backup_env, mock_behavior="restore_validation_failure")
    assert result.returncode == 1
    assert "Verification FAILED" in result.stderr or "Cleaning up" in result.stderr

    # Verify existing backup is preserved
    assert existing_dump.exists()

    # Verify NO new .dump files were promoted
    dumps = list(backup_env["backup_dir"].glob("campus_project_campus_prod_*.dump"))
    assert len(dumps) == 1

    # Verify NO .tmp files left
    tmp_files = list(backup_env["backup_dir"].glob("*.tmp"))
    assert len(tmp_files) == 0


def test_backup_signal_handling_term_cleans_tmp_and_exits_143(backup_env):
    """Verify that when SIGTERM terminates the backup, the .tmp file is purged and exit code is 143."""
    existing_dump = backup_env["backup_dir"] / "campus_project_campus_prod_20260101_000000.dump"
    existing_dump.write_text("EXISTING_VALID_BACKUP", encoding="utf-8")

    result = run_backup_script(backup_env, mock_behavior="sigterm")
    assert result.returncode == 143
    assert "SIGTERM" in result.stderr

    # Verify existing backup is preserved
    assert existing_dump.exists()

    # Verify NO .tmp files left
    tmp_files = list(backup_env["backup_dir"].glob("*.tmp"))
    assert len(tmp_files) == 0


def test_backup_signal_handling_int_cleans_tmp_and_exits_130(backup_env):
    """Verify that when SIGINT interrupts the backup, the .tmp file is purged and exit code is 130."""
    existing_dump = backup_env["backup_dir"] / "campus_project_campus_prod_20260101_000000.dump"
    existing_dump.write_text("EXISTING_VALID_BACKUP", encoding="utf-8")

    result = run_backup_script(backup_env, mock_behavior="sigint")
    assert result.returncode == 130
    assert "SIGINT" in result.stderr

    # Verify existing backup is preserved
    assert existing_dump.exists()

    # Verify NO .tmp files left
    tmp_files = list(backup_env["backup_dir"].glob("*.tmp"))
    assert len(tmp_files) == 0
