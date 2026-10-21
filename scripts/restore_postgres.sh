#!/usr/bin/env bash
# ==============================================================================
# Project Campus — Safe PostgreSQL Restore and Verification Script
# ==============================================================================
# Restores a custom-format (-Fc) pg_dump backup into an explicitly designated,
# verified, and FRESH/EMPTY disposable PostgreSQL database.
#
# MANDATORY SAFETY CONTROLS:
# - Unconditional refusal of production environments (ENVIRONMENT/ENV=production/prod)
# - Unconditional refusal of production containers (*prod*, campus_postgres_prod)
# - Unconditional refusal of production database names (*prod*, campus_prod, etc.)
# - Unconditional refusal of configured application database (POSTGRES_DB / project_campus_dev)
# - Requires explicit CONFIRM_DISPOSABLE_TARGET=yes AND CONFIRM_DISPOSABLE_SERVER=yes
# - Enforces server allowlist (APPROVED_TEST_HOSTS / APPROVED_TEST_CONTAINERS)
# - Rejects ambiguous combinations of container and host libpq settings
# - Queries PostgreSQL server to verify target database identity and emptiness
# - Strictly prohibits --clean and --if-exists (will NOT drop existing data)
# - Restores with --no-owner --no-privileges --single-transaction
# - Performs post-restore verification: Alembic version, tables, and connectivity
# ==============================================================================

set -euo pipefail

# Mandatory inputs via environment or positional parameters
BACKUP_FILE="${1:-${BACKUP_FILE:-}}"
TARGET_DB="${2:-${TARGET_DB:-}}"
POSTGRES_USER="${POSTGRES_USER:-}"
CONTAINER_NAME="${CONTAINER_NAME:-}"
CONFIRM_DISPOSABLE_TARGET="${CONFIRM_DISPOSABLE_TARGET:-no}"
CONFIRM_DISPOSABLE_SERVER="${CONFIRM_DISPOSABLE_SERVER:-no}"
EXPECTED_ALEMBIC_REVISION="${EXPECTED_ALEMBIC_REVISION:-0cbebed2ada2}"
RESTORE_TARGET_TYPE="${RESTORE_TARGET_TYPE:-auto}"
APPROVED_TEST_HOSTS="${APPROVED_TEST_HOSTS:-localhost 127.0.0.1 postgres campus_postgres_test}"
APPROVED_TEST_CONTAINERS="${APPROVED_TEST_CONTAINERS:-campus_postgres_test postgres}"

log() {
    echo "[$(date -u +'%Y-%m-%dT%H:%M:%SZ')] $*"
}

error_exit() {
    echo "[$(date -u +'%Y-%m-%dT%H:%M:%SZ')] ERROR: $*" >&2
    exit 1
}

# Signal handlers
trap_int() {
    echo "[$(date -u +'%Y-%m-%dT%H:%M:%SZ')] Interrupted by SIGINT; aborting restore operation." >&2
    exit 130
}

trap_term() {
    echo "[$(date -u +'%Y-%m-%dT%H:%M:%SZ')] Terminated by SIGTERM; aborting restore operation." >&2
    exit 143
}

trap trap_int INT
trap trap_term TERM

# --- Step 1: Input & Environment Validation ---

# 1a. Reject production execution mode unconditionally
ENV_CHECK="$(echo "${ENVIRONMENT:-${ENV:-}}" | tr '[:upper:]' '[:lower:]')"
if [ "${ENV_CHECK}" = "production" ] || [ "${ENV_CHECK}" = "prod" ]; then
    error_exit "Safety rejection: ENVIRONMENT is set to '${ENVIRONMENT:-${ENV}}'. Restore script is strictly prohibited in production mode."
fi

# 1b. Reject production container target unconditionally
if [ -n "${CONTAINER_NAME:-}" ]; then
    LOWER_CONTAINER="$(echo "${CONTAINER_NAME}" | tr '[:upper:]' '[:lower:]')"
    case "${LOWER_CONTAINER}" in
        *prod*|*production*)
            error_exit "Safety rejection: CONTAINER_NAME '${CONTAINER_NAME}' indicates a production container. Restoration is refused unconditionally."
            ;;
    esac
fi

# 1c. Validate required input parameters
if [ -z "${BACKUP_FILE}" ]; then
    error_exit "BACKUP_FILE must be specified (via argument 1 or BACKUP_FILE environment variable)."
fi

if [ ! -f "${BACKUP_FILE}" ]; then
    error_exit "Backup file does not exist or is not a regular file: ${BACKUP_FILE}"
fi

if [ ! -r "${BACKUP_FILE}" ]; then
    error_exit "Backup file is not readable: ${BACKUP_FILE}"
fi

if [ -z "${TARGET_DB}" ]; then
    error_exit "TARGET_DB must be explicitly specified (via argument 2 or TARGET_DB environment variable)."
fi

if [ -z "${POSTGRES_USER}" ]; then
    error_exit "POSTGRES_USER must be explicitly specified."
fi

# 1d. Reject ambiguous connection configurations (e.g. PGSERVICE, PGSERVICEFILE, PGHOSTADDR)
if [ -n "${PGSERVICE:-}" ]; then
    error_exit "Safety rejection: PGSERVICE is set ('${PGSERVICE}'). Service-based redirection is prohibited during restore to prevent unintended server connection."
fi
if [ -n "${PGSERVICEFILE:-}" ]; then
    error_exit "Safety rejection: PGSERVICEFILE is set ('${PGSERVICEFILE}'). Custom service configuration is prohibited during restore."
fi
if [ -n "${PGHOSTADDR:-}" ]; then
    if [ "${PGHOSTADDR}" != "127.0.0.1" ] && [ "${PGHOSTADDR}" != "::1" ]; then
        error_exit "Safety rejection: PGHOSTADDR is set to non-loopback address ('${PGHOSTADDR}'). Direct IP override is prohibited."
    fi
fi

# 1e. Determine and validate connection target mode (container vs host)
if [ -n "${CONTAINER_NAME:-}" ]; then
    TARGET_MODE="container"
    CONTAINER_APPROVED=0
    for ac in ${APPROVED_TEST_CONTAINERS}; do
        if [ "${CONTAINER_NAME}" = "${ac}" ]; then
            CONTAINER_APPROVED=1
            break
        fi
    done
    if [ "${CONTAINER_APPROVED}" -ne 1 ]; then
        error_exit "Safety rejection: Container '${CONTAINER_NAME}' is not in approved test containers allowlist (${APPROVED_TEST_CONTAINERS})."
    fi
else
    TARGET_MODE="host"
    PGHOST_VAL="${PGHOST:-127.0.0.1}"
    HOST_APPROVED=0
    for ah in ${APPROVED_TEST_HOSTS}; do
        if [ "${PGHOST_VAL}" = "${ah}" ]; then
            HOST_APPROVED=1
            break
        fi
    done
    if [ "${HOST_APPROVED}" -ne 1 ]; then
        error_exit "Safety rejection: PGHOST '${PGHOST_VAL}' is not in approved test hosts allowlist (${APPROVED_TEST_HOSTS})."
    fi
fi

# 1f. Pre-validate backup archive structure using pg_restore --list
log "Validating backup archive structure via pg_restore --list..."
if [ "${TARGET_MODE}" = "container" ] && command -v docker >/dev/null 2>&1 && docker ps --format '{{.Names}}' 2>/dev/null | grep -q "^${CONTAINER_NAME}$"; then
    if ! docker exec -i "${CONTAINER_NAME}" pg_restore --list < "${BACKUP_FILE}" >/dev/null 2>&1; then
        error_exit "Backup archive failed structural validation (pg_restore --list). File may be corrupted or invalid format."
    fi
elif [ "${TARGET_MODE}" = "host" ] && command -v pg_restore >/dev/null 2>&1; then
    if ! pg_restore --list "${BACKUP_FILE}" >/dev/null 2>&1; then
        error_exit "Backup archive failed structural validation (pg_restore --list). File may be corrupted or invalid format."
    fi
else
    error_exit "Neither running container '${CONTAINER_NAME}' nor host pg_restore is available for validation."
fi
log "Backup archive validation PASSED."

# --- Step 2: Target & Server Safety Controls ---

# Check 2a: Explicit disposable confirmations
if [ "${CONFIRM_DISPOSABLE_TARGET}" != "yes" ]; then
    error_exit "Safety lock: Target must be confirmed as disposable by setting CONFIRM_DISPOSABLE_TARGET=yes."
fi

if [ "${CONFIRM_DISPOSABLE_SERVER}" != "yes" ]; then
    error_exit "Safety lock: Server must be confirmed as a disposable test environment by setting CONFIRM_DISPOSABLE_SERVER=yes."
fi

# Check 2b: Unconditional refusal of production and development names
LOWER_TARGET="$(echo "${TARGET_DB}" | tr '[:upper:]' '[:lower:]')"
case "${LOWER_TARGET}" in
    *prod*|*production*|project_campus|campus|project_campus_dev|campus_dev|*_dev)
        error_exit "Safety rejection: Target database '${TARGET_DB}' matches protected/production name pattern. Restoration is refused unconditionally."
        ;;
esac

# Check 2c: Refusal to restore into the configured application database
if [ -n "${POSTGRES_DB:-}" ]; then
    LOWER_APP_DB="$(echo "${POSTGRES_DB}" | tr '[:upper:]' '[:lower:]')"
    if [ "${LOWER_TARGET}" = "${LOWER_APP_DB}" ]; then
        error_exit "Safety rejection: Target database '${TARGET_DB}' matches configured application POSTGRES_DB. Restoration is refused unconditionally."
    fi
fi

# SQL Execution Helper
run_sql() {
    local db="$1"
    local query="$2"
    if [ "${TARGET_MODE}" = "container" ] && command -v docker >/dev/null 2>&1 && docker ps --format '{{.Names}}' 2>/dev/null | grep -q "^${CONTAINER_NAME}$"; then
        docker exec "${CONTAINER_NAME}" psql -U "${POSTGRES_USER}" -d "${db}" -t -A -c "${query}"
    elif [ "${TARGET_MODE}" = "host" ] && command -v psql >/dev/null 2>&1; then
        psql -U "${POSTGRES_USER}" -d "${db}" -t -A -c "${query}"
    else
        error_exit "Neither running container '${CONTAINER_NAME}' nor host psql is available to query database."
    fi
}

# Check 2d: Query server to verify server endpoint and target database identity
log "Verifying connected server endpoint and target database identity..."
SERVER_ENDPOINT="$(run_sql "${TARGET_DB}" "SELECT COALESCE(inet_server_addr()::text, 'local_socket');" 2>/dev/null || true)"
if [ -z "${SERVER_ENDPOINT}" ]; then
    error_exit "Failed to query server network identity. Target database '${TARGET_DB}' may not exist or connection failed."
fi

if [ "${TARGET_MODE}" = "host" ]; then
    case "${SERVER_ENDPOINT}" in
        127.0.0.1|::1|local_socket)
            ;;
        *)
            ENDPOINT_APPROVED=0
            for ah in ${APPROVED_TEST_HOSTS}; do
                if [ "${SERVER_ENDPOINT}" = "${ah}" ]; then
                    ENDPOINT_APPROVED=1
                    break
                fi
            done
            if [ "${ENDPOINT_APPROVED}" -ne 1 ]; then
                error_exit "Safety rejection: Connected server endpoint '${SERVER_ENDPOINT}' is not in approved test hosts (${APPROVED_TEST_HOSTS})."
            fi
            ;;
    esac
fi

ACTUAL_DB="$(run_sql "${TARGET_DB}" "SELECT current_database();" 2>/dev/null || true)"
if [ -z "${ACTUAL_DB}" ]; then
    error_exit "Failed to verify database identity. Target database '${TARGET_DB}' may not exist or connection failed."
fi

if [ "${ACTUAL_DB}" != "${TARGET_DB}" ]; then
    error_exit "Database identity mismatch! Connected to '${ACTUAL_DB}', expected '${TARGET_DB}'."
fi

# Check 2e: Require target to be fresh and empty (0 tables in public schema)
TABLE_COUNT="$(run_sql "${TARGET_DB}" "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public' AND table_type = 'BASE TABLE';" 2>/dev/null || echo "0")"
if [ "${TABLE_COUNT}" -ne 0 ]; then
    error_exit "Target database '${TARGET_DB}' is NOT empty (contains ${TABLE_COUNT} table(s)). Restoration into non-empty databases is strictly prohibited."
fi
log "Target database '${TARGET_DB}' verified: Identity confirmed and schema is fresh/empty."

# --- Step 3: Execute Restoration ---
log "Restoring custom-format backup into '${TARGET_DB}' using --no-owner and --no-privileges..."
RESTORE_STATUS=0
if [ "${TARGET_MODE}" = "container" ] && command -v docker >/dev/null 2>&1 && docker ps --format '{{.Names}}' 2>/dev/null | grep -q "^${CONTAINER_NAME}$"; then
    docker exec -i "${CONTAINER_NAME}" pg_restore -U "${POSTGRES_USER}" -d "${TARGET_DB}" --no-owner --no-privileges --single-transaction < "${BACKUP_FILE}" || RESTORE_STATUS=$?
elif [ "${TARGET_MODE}" = "host" ] && command -v pg_restore >/dev/null 2>&1; then
    pg_restore -U "${POSTGRES_USER}" -d "${TARGET_DB}" --no-owner --no-privileges --single-transaction "${BACKUP_FILE}" || RESTORE_STATUS=$?
else
    error_exit "pg_restore execution failed: tool unavailable."
fi

if [ "${RESTORE_STATUS}" -ne 0 ]; then
    error_exit "pg_restore failed with exit code ${RESTORE_STATUS}."
fi
log "pg_restore completed successfully."

# --- Step 4: Post-Restore Verification ---
log "Executing post-restore verification suite..."

# 4a. Verify Alembic migration revision
RESTORED_REVISION="$(run_sql "${TARGET_DB}" "SELECT version_num FROM alembic_version;" 2>/dev/null || true)"
if [ -z "${RESTORED_REVISION}" ]; then
    error_exit "Post-restore check failed: 'alembic_version' table is missing."
fi

if [ "${RESTORED_REVISION}" != "${EXPECTED_ALEMBIC_REVISION}" ]; then
    error_exit "Post-restore check failed: Migration revision is '${RESTORED_REVISION}', expected '${EXPECTED_ALEMBIC_REVISION}'."
fi
log "Verified Alembic revision: ${RESTORED_REVISION}"

# 4b. Verify core application tables exist
CORE_TABLES_COUNT="$(run_sql "${TARGET_DB}" "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema='public' AND table_name IN ('users', 'roles', 'student_profiles', 'lessons', 'questions', 'review_items');" 2>/dev/null || echo "0")"
if [ "${CORE_TABLES_COUNT}" -lt 6 ]; then
    error_exit "Post-restore check failed: Expected 6 core application tables, found ${CORE_TABLES_COUNT}."
fi
log "Verified core application tables exist (${CORE_TABLES_COUNT}/6 found)."

# 4c. Verify basic query execution (database connectivity)
CONNECT_CHECK="$(run_sql "${TARGET_DB}" "SELECT 1;" 2>/dev/null || true)"
if [ "${CONNECT_CHECK}" != "1" ]; then
    error_exit "Post-restore check failed: Connectivity probe 'SELECT 1' failed."
fi
log "Verified database connectivity and query execution."

log "Post-restore verification PASSED completely for target database '${TARGET_DB}'."
