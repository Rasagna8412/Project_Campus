"""Unit and safety tests for PostgreSQL restore script (scripts/restore_postgres.sh)."""

import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
RESTORE_SCRIPT = REPO_ROOT / "scripts" / "restore_postgres.sh"


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
def restore_env():
    """Create isolated temporary directory and mock bin directory for restore script testing."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        bin_dir = tmp_path / "bin"
        bin_dir.mkdir(parents=True, exist_ok=True)
        backup_file = tmp_path / "valid_test_backup.dump"
        backup_file.write_text("PGDUMP_MOCK_VALID_ARCHIVE", encoding="utf-8")

        yield {
            "root": tmp_path,
            "bin_dir": bin_dir,
            "backup_file": backup_file,
            "bash": get_bash_executable(),
        }


def create_mock_docker(
    bin_dir: Path,
    list_valid: bool = True,
    db_name: str = "campus_disposable_target",
    is_empty: bool = True,
    restore_success: bool = True,
    alembic_rev: str = "0cbebed2ada2",
    tables_count: int = 6,
    connectivity: bool = True,
    server_ip: str = "127.0.0.1",
):
    """Create a mock docker executable simulating psql, pg_restore, and container interactions."""
    mock_docker = bin_dir / "docker"

    empty_val = "0" if is_empty else "5"
    conn_val = "1" if connectivity else "0"

    content = f"""#!/bin/sh
# Log all invocations to inspect executed flags
echo "$@" >> "{bin_dir.as_posix()}/docker_invocations.log"

if [ "$1" = "ps" ]; then
    echo "campus_postgres_test"
    exit 0
fi

if [ "$1" = "exec" ]; then
    shift
    # Check if this is pg_restore --list
    case "$*" in
        *pg_restore*--list*)
            if [ "{str(list_valid).lower()}" = "true" ]; then
                exit 0
            else
                echo "pg_restore: error: corrupted header" >&2
                exit 1
            fi
            ;;
        *pg_restore*)
            if [ "{str(restore_success).lower()}" = "true" ]; then
                exit 0
            else
                echo "pg_restore: error: syntax error" >&2
                exit 1
            fi
            ;;
        *psql*)
            # Simulate SQL query responses
            case "$*" in
                *"inet_server_addr()"*)
                    echo "{server_ip}"
                    exit 0
                    ;;
                *"current_database()"*)
                    echo "{db_name}"
                    exit 0
                    ;;
                *"table_type = 'BASE TABLE'"*)
                    echo "{empty_val}"
                    exit 0
                    ;;
                *"alembic_version"*)
                    echo "{alembic_rev}"
                    exit 0
                    ;;
                *"users"*"roles"*"student_profiles"*)
                    echo "{tables_count}"
                    exit 0
                    ;;
                *"SELECT 1;"*)
                    echo "{conn_val}"
                    exit 0
                    ;;
                *)
                    exit 0
                    ;;
            esac
            ;;
        *)
            exit 0
            ;;
    esac
fi

exit 0
"""
    mock_docker.write_text(content, encoding="utf-8")
    mock_docker.chmod(0o755)
    return mock_docker


def run_restore_script(
    restore_env,
    backup_file: str = None,
    target_db: str = "campus_disposable_target",
    confirm_disposable_target: str = "yes",
    confirm_disposable_server: str = "yes",
    postgres_user: str = "campus_test_user",
    container_name: str = "campus_postgres_test",
    env_overrides: dict = None,
):
    """Execute restore_postgres.sh with isolated environment."""
    if backup_file is None:
        backup_file = str(restore_env["backup_file"]).replace("\\", "/")

    env = os.environ.copy()
    # Clean ambient environment variables to prevent test cross-contamination
    env.pop("ENVIRONMENT", None)
    env.pop("ENV", None)
    env.pop("PGSERVICE", None)

    env["PATH"] = f"{restore_env['bin_dir']}{os.pathsep}{env.get('PATH', '')}"
    env["BACKUP_FILE"] = str(backup_file).replace("\\", "/")
    env["TARGET_DB"] = str(target_db)
    env["POSTGRES_USER"] = str(postgres_user)
    env["CONTAINER_NAME"] = str(container_name)
    env["CONFIRM_DISPOSABLE_TARGET"] = str(confirm_disposable_target)
    env["CONFIRM_DISPOSABLE_SERVER"] = str(confirm_disposable_server)

    if env_overrides:
        env.update(env_overrides)

    proc = subprocess.run(
        [restore_env["bash"], str(RESTORE_SCRIPT).replace("\\", "/")],
        env=env,
        capture_output=True,
        text=True,
    )
    return proc


def test_restore_successful_on_verified_disposable_target(restore_env):
    """Verify that restore succeeds when target is verified, fresh, empty, and post-checks pass."""
    create_mock_docker(restore_env["bin_dir"])
    result = run_restore_script(restore_env)
    assert result.returncode == 0, f"Restore failed: {result.stderr}"
    assert "Target database 'campus_disposable_target' verified" in result.stdout
    assert "Post-restore verification PASSED completely" in result.stdout

    # Verify that --clean and --if-exists were NEVER invoked
    log_file = restore_env["bin_dir"] / "docker_invocations.log"
    if log_file.exists():
        log_content = log_file.read_text(encoding="utf-8")
        assert "--clean" not in log_content
        assert "--if-exists" not in log_content
        assert "--no-owner" in log_content
        assert "--no-privileges" in log_content


def test_restore_rejects_missing_backup_file(restore_env):
    """Verify that restore aborts immediately if the backup file does not exist."""
    create_mock_docker(restore_env["bin_dir"])
    missing_file = restore_env["root"] / "non_existent_file.dump"
    result = run_restore_script(restore_env, backup_file=str(missing_file))
    assert result.returncode != 0
    assert "does not exist or is not a regular file" in result.stderr


def test_restore_rejects_invalid_or_unreadable_backup_archive(restore_env):
    """Verify that restore aborts if pg_restore --list fails on a corrupted backup."""
    create_mock_docker(restore_env["bin_dir"], list_valid=False)
    result = run_restore_script(restore_env)
    assert result.returncode != 0
    assert "Backup archive failed structural validation" in result.stderr


def test_restore_rejects_missing_target_database_config(restore_env):
    """Verify that restore rejects execution if TARGET_DB is omitted or empty."""
    create_mock_docker(restore_env["bin_dir"])
    result = run_restore_script(restore_env, target_db="")
    assert result.returncode != 0
    assert "TARGET_DB must be explicitly specified" in result.stderr


def test_restore_rejects_missing_disposable_target_confirmation(restore_env):
    """Verify that restore aborts if CONFIRM_DISPOSABLE_TARGET is not explicitly set to 'yes'."""
    create_mock_docker(restore_env["bin_dir"])
    result = run_restore_script(restore_env, confirm_disposable_target="no")
    assert result.returncode != 0
    assert "Safety lock: Target must be confirmed as disposable" in result.stderr


def test_restore_rejects_missing_disposable_server_confirmation(restore_env):
    """Verify that restore aborts if CONFIRM_DISPOSABLE_SERVER is not explicitly set to 'yes'."""
    create_mock_docker(restore_env["bin_dir"])
    result = run_restore_script(restore_env, confirm_disposable_server="no")
    assert result.returncode != 0
    assert "Safety lock: Server must be confirmed as a disposable test environment" in result.stderr


@pytest.mark.parametrize("env_var,val", [("ENVIRONMENT", "production"), ("ENVIRONMENT", "prod"), ("ENV", "Production"), ("ENV", "PROD")])
def test_restore_unconditionally_rejects_production_environment_modes(restore_env, env_var, val):
    """Verify that restore script rejects execution when ambient ENVIRONMENT or ENV is production."""
    create_mock_docker(restore_env["bin_dir"])
    result = run_restore_script(restore_env, env_overrides={env_var: val})
    assert result.returncode != 0
    assert "Restore script is strictly prohibited in production mode" in result.stderr


@pytest.mark.parametrize("prod_container", ["campus_postgres_prod", "my_production_db", "prod_database"])
def test_restore_unconditionally_rejects_production_container_name(restore_env, prod_container):
    """Verify that restore script rejects execution when CONTAINER_NAME indicates production."""
    create_mock_docker(restore_env["bin_dir"])
    result = run_restore_script(restore_env, container_name=prod_container)
    assert result.returncode != 0
    assert "indicates a production container" in result.stderr


@pytest.mark.parametrize(
    "forbidden_db",
    [
        "project_campus_prod",
        "campus_prod",
        "production_db",
        "project_campus",
        "campus",
        "project_campus_dev",
        "campus_dev",
    ],
)
def test_restore_unconditionally_rejects_known_production_names(restore_env, forbidden_db):
    """Verify that known production or development database names are rejected unconditionally."""
    create_mock_docker(restore_env["bin_dir"], db_name=forbidden_db)
    result = run_restore_script(restore_env, target_db=forbidden_db)
    assert result.returncode != 0
    assert "matches protected/production name pattern" in result.stderr
    assert "refused unconditionally" in result.stderr

    # Ensure pg_restore was NEVER called
    log_file = restore_env["bin_dir"] / "docker_invocations.log"
    if log_file.exists():
        assert "pg_restore -U" not in log_file.read_text(encoding="utf-8")


def test_restore_rejects_target_matching_configured_application_db(restore_env):
    """Verify that if target matches POSTGRES_DB from environment, restore aborts."""
    create_mock_docker(restore_env["bin_dir"])
    result = run_restore_script(
        restore_env,
        target_db="my_staging_db",
        env_overrides={"POSTGRES_DB": "my_staging_db"},
    )
    assert result.returncode != 0
    assert "matches configured application POSTGRES_DB" in result.stderr


def test_restore_rejects_unapproved_server_host(restore_env):
    """Verify that in host mode, PGHOST outside APPROVED_TEST_HOSTS is rejected."""
    mock_docker = restore_env["bin_dir"] / "docker"
    if mock_docker.exists():
        mock_docker.unlink()

    result = run_restore_script(
        restore_env,
        container_name="",
        env_overrides={"PGHOST": "remote-rds.production.internal"},
    )
    assert result.returncode != 0
    assert "is not in approved test hosts allowlist" in result.stderr


def test_restore_rejects_pgservice_redirection(restore_env):
    """Verify that setting PGSERVICE aborts restore to prevent silent connection hijacking."""
    create_mock_docker(restore_env["bin_dir"])
    result = run_restore_script(
        restore_env,
        env_overrides={"PGSERVICE": "hijacked_service"},
    )
    assert result.returncode != 0
    assert "PGSERVICE is set" in result.stderr


def test_restore_rejects_pgservicefile_redirection(restore_env):
    """Verify that setting PGSERVICEFILE aborts restore to prevent config hijacking."""
    create_mock_docker(restore_env["bin_dir"])
    result = run_restore_script(
        restore_env,
        env_overrides={"PGSERVICEFILE": "/tmp/custom_pg_service.conf"},
    )
    assert result.returncode != 0
    assert "PGSERVICEFILE is set" in result.stderr


def test_restore_rejects_non_loopback_pghostaddr_override(restore_env):
    """Verify that setting non-loopback PGHOSTADDR aborts restore to prevent direct IP hijacking."""
    create_mock_docker(restore_env["bin_dir"])
    result = run_restore_script(
        restore_env,
        env_overrides={"PGHOSTADDR": "198.51.100.1"},
    )
    assert result.returncode != 0
    assert "PGHOSTADDR is set to non-loopback address" in result.stderr


def test_restore_rejects_unverifiable_database_identity(restore_env):
    """Verify that if the server returns a different current_database() than requested, restore aborts."""
    create_mock_docker(restore_env["bin_dir"], db_name="different_database_name")
    result = run_restore_script(restore_env, target_db="campus_disposable_target")
    assert result.returncode != 0
    assert "Database identity mismatch" in result.stderr


def test_restore_rejects_non_empty_target_database(restore_env):
    """Verify that restore refuses to execute into a non-empty database and never uses --clean."""
    create_mock_docker(restore_env["bin_dir"], is_empty=False)
    result = run_restore_script(restore_env)
    assert result.returncode != 0
    assert "is NOT empty" in result.stderr
    assert "strictly prohibited" in result.stderr

    # Ensure pg_restore was never called
    log_file = restore_env["bin_dir"] / "docker_invocations.log"
    if log_file.exists():
        assert "pg_restore -U" not in log_file.read_text(encoding="utf-8")


def test_restore_command_failure_reports_and_exits_nonzero(restore_env):
    """Verify that if pg_restore encounters an execution error, the script exits non-zero."""
    create_mock_docker(restore_env["bin_dir"], restore_success=False)
    result = run_restore_script(restore_env)
    assert result.returncode != 0
    assert "pg_restore failed with exit code" in result.stderr


def test_restore_post_verification_failure_on_alembic_revision_mismatch(restore_env):
    """Verify that if the restored database reports a wrong migration revision, the script exits 1."""
    create_mock_docker(restore_env["bin_dir"], alembic_rev="old_outdated_revision_123")
    result = run_restore_script(restore_env)
    assert result.returncode != 0
    assert "Migration revision is 'old_outdated_revision_123', expected '0cbebed2ada2'" in result.stderr


def test_restore_post_verification_failure_on_missing_tables(restore_env):
    """Verify that if core tables are missing post-restore, the script exits 1."""
    create_mock_docker(restore_env["bin_dir"], tables_count=2)
    result = run_restore_script(restore_env)
    assert result.returncode != 0
    assert "Expected 6 core application tables, found 2" in result.stderr


def test_restore_signal_handling_int_exits_130(restore_env):
    """Verify that SIGINT aborts the restore script with exit code 130."""
    mock_docker = restore_env["bin_dir"] / "docker"
    # Create mock docker that sends SIGINT to parent during pg_restore execution
    content = """#!/bin/sh
if [ "$1" = "ps" ]; then echo "campus_postgres_test"; exit 0; fi
if [ "$1" = "exec" ]; then
    case "$*" in
        *pg_restore*--list*) exit 0 ;;
        *pg_restore*)
            kill -s INT $PPID 2>/dev/null || kill -2 $PPID
            sleep 1
            exit 1
            ;;
        *psql*)
            case "$*" in
                *"inet_server_addr()"*) echo "127.0.0.1"; exit 0 ;;
                *"current_database()"*) echo "campus_disposable_target"; exit 0 ;;
                *"table_type = 'BASE TABLE'"*) echo "0"; exit 0 ;;
                *) exit 0 ;;
            esac
            ;;
    esac
fi
exit 0
"""
    mock_docker.write_text(content, encoding="utf-8")
    mock_docker.chmod(0o755)

    result = run_restore_script(restore_env)
    assert result.returncode == 130
    assert "Interrupted by SIGINT" in result.stderr


def test_restore_signal_handling_term_exits_143(restore_env):
    """Verify that SIGTERM aborts the restore script with exit code 143."""
    mock_docker = restore_env["bin_dir"] / "docker"
    content = """#!/bin/sh
if [ "$1" = "ps" ]; then echo "campus_postgres_test"; exit 0; fi
if [ "$1" = "exec" ]; then
    case "$*" in
        *pg_restore*--list*) exit 0 ;;
        *pg_restore*)
            kill -s TERM $PPID 2>/dev/null || kill -15 $PPID
            sleep 1
            exit 1
            ;;
        *psql*)
            case "$*" in
                *"inet_server_addr()"*) echo "127.0.0.1"; exit 0 ;;
                *"current_database()"*) echo "campus_disposable_target"; exit 0 ;;
                *"table_type = 'BASE TABLE'"*) echo "0"; exit 0 ;;
                *) exit 0 ;;
            esac
            ;;
    esac
fi
exit 0
"""
    mock_docker.write_text(content, encoding="utf-8")
    mock_docker.chmod(0o755)

    result = run_restore_script(restore_env)
    assert result.returncode == 143
    assert "Terminated by SIGTERM" in result.stderr


def test_restore_accepts_container_bridge_endpoint(restore_env):
    """Verify that private container bridge endpoints (e.g. 172.18.0.2) are accepted."""
    create_mock_docker(restore_env["bin_dir"], server_ip="172.18.0.2")
    result = run_restore_script(restore_env)
    assert result.returncode == 0, f"Restore failed: {result.stderr}"
    assert "Post-restore verification PASSED completely" in result.stdout


def test_restore_rejects_unapproved_public_server_endpoint(restore_env):
    """Verify that unapproved public server endpoints are rejected even in host mode."""
    mock_docker = restore_env["bin_dir"] / "docker"
    if mock_docker.exists():
        mock_docker.unlink()

    mock_pg_restore = restore_env["bin_dir"] / "pg_restore"
    mock_pg_restore.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    mock_pg_restore.chmod(0o755)

    mock_psql = restore_env["bin_dir"] / "psql"
    mock_psql.write_text("""#!/bin/sh
case "$*" in
    *"inet_server_addr()"*) echo "203.0.113.195"; exit 0 ;;
    *) echo "1"; exit 0 ;;
esac
""", encoding="utf-8")
    mock_psql.chmod(0o755)

    result = run_restore_script(
        restore_env,
        container_name="",
        env_overrides={"PGHOST": "127.0.0.1"},
    )
    assert result.returncode != 0
    assert "is not in approved test hosts" in result.stderr
