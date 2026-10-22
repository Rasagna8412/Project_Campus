#!/usr/bin/env bash
# ==============================================================================
# Project Campus — PostgreSQL Backup and Retention Script
# ==============================================================================
# Performs consistent, custom-format (-Fc) pg_dump backups from the running
# production PostgreSQL container, verifies backup integrity, locks file
# permissions (0600), and prunes dumps older than the retention window.
#
# Usage:
#   chmod +x scripts/backup_postgres.sh
#   ./scripts/backup_postgres.sh
#
# Recommended Cron Schedule (Daily at 02:00 AM UTC):
#   0 2 * * * /opt/project_campus/scripts/backup_postgres.sh >> /var/log/campus_backup.log 2>&1
# ==============================================================================

set -euo pipefail

# Configuration with environment defaults
BACKUP_DIR="${BACKUP_DIR:-/var/backups/project_campus}"
RETENTION_DAYS="${RETENTION_DAYS:-14}"
CONTAINER_NAME="${CONTAINER_NAME:-campus_postgres_prod}"
COMPOSE_FILE="${COMPOSE_FILE:-docker-compose.production.yml}"
POSTGRES_USER="${POSTGRES_USER:-campus_user}"
POSTGRES_DB="${POSTGRES_DB:-project_campus_prod}"
BACKUP_METHOD="${BACKUP_METHOD:-auto}"

TIMESTAMP="$(date +%Y%m%d_%H%M%S)"
BACKUP_FILENAME="campus_${POSTGRES_DB}_${TIMESTAMP}.dump"
BACKUP_FILEPATH="${BACKUP_DIR}/${BACKUP_FILENAME}"
if [ -e "${BACKUP_FILEPATH}" ]; then
    BACKUP_FILENAME="campus_${POSTGRES_DB}_${TIMESTAMP}_$$.dump"
    BACKUP_FILEPATH="${BACKUP_DIR}/${BACKUP_FILENAME}"
fi
TEMP_BACKUP_FILEPATH="${BACKUP_FILEPATH}.tmp"

# Cleanup handler ensuring incomplete/corrupted dumps are purged on normal error exit
cleanup() {
    local exit_code=$?
    if [ -f "${TEMP_BACKUP_FILEPATH:-}" ]; then
        echo "[$(date -u +'%Y-%m-%dT%H:%M:%SZ')] Cleaning up incomplete temporary backup: ${TEMP_BACKUP_FILEPATH}" >&2
        rm -f "${TEMP_BACKUP_FILEPATH}"
    fi
    exit "${exit_code}"
}

# Signal handlers ensuring proper exit codes (130 for INT, 143 for TERM) and cleanup
trap_int() {
    if [ -f "${TEMP_BACKUP_FILEPATH:-}" ]; then
        echo "[$(date -u +'%Y-%m-%dT%H:%M:%SZ')] Interrupted by SIGINT; cleaning up temporary backup: ${TEMP_BACKUP_FILEPATH}" >&2
        rm -f "${TEMP_BACKUP_FILEPATH}"
    fi
    exit 130
}

trap_term() {
    if [ -f "${TEMP_BACKUP_FILEPATH:-}" ]; then
        echo "[$(date -u +'%Y-%m-%dT%H:%M:%SZ')] Terminated by SIGTERM; cleaning up temporary backup: ${TEMP_BACKUP_FILEPATH}" >&2
        rm -f "${TEMP_BACKUP_FILEPATH}"
    fi
    exit 143
}

trap cleanup EXIT
trap trap_int INT
trap trap_term TERM

echo "[$(date -u +'%Y-%m-%dT%H:%M:%SZ')] Starting database backup for '${POSTGRES_DB}'..."

# Ensure backup destination directory exists with restricted permissions (0700)
mkdir -p "${BACKUP_DIR}"
chmod 0700 "${BACKUP_DIR}"

# Restrict file creation mask so dumps are created with 0600 (owner read/write only)
umask 077

# Step 1: Execute consistent compressed dump to temporary file
echo "[$(date -u +'%Y-%m-%dT%H:%M:%SZ')] Executing pg_dump from target to temporary artifact..."
if [ "${BACKUP_METHOD}" = "docker" ] || { [ "${BACKUP_METHOD}" = "auto" ] && [ -n "${CONTAINER_NAME:-}" ] && command -v docker >/dev/null 2>&1 && docker ps --format '{{.Names}}' 2>/dev/null | grep -q "^${CONTAINER_NAME}$"; }; then
    echo "[$(date -u +'%Y-%m-%dT%H:%M:%SZ')] Using Docker container execution on '${CONTAINER_NAME}'..."
    docker exec "${CONTAINER_NAME}" pg_dump -U "${POSTGRES_USER}" -d "${POSTGRES_DB}" -Fc > "${TEMP_BACKUP_FILEPATH}"
elif [ "${BACKUP_METHOD}" = "compose" ] || { [ "${BACKUP_METHOD}" = "auto" ] && [ -n "${COMPOSE_FILE:-}" ] && [ -f "${COMPOSE_FILE}" ] && command -v docker >/dev/null 2>&1 && docker compose -f "${COMPOSE_FILE}" ps --status running -q postgres 2>/dev/null | grep -q .; }; then
    echo "[$(date -u +'%Y-%m-%dT%H:%M:%SZ')] Using Docker Compose execution with '${COMPOSE_FILE}'..."
    docker compose -f "${COMPOSE_FILE}" exec -T postgres pg_dump -U "${POSTGRES_USER}" -d "${POSTGRES_DB}" -Fc > "${TEMP_BACKUP_FILEPATH}"
elif [ "${BACKUP_METHOD}" = "host" ] || { [ "${BACKUP_METHOD}" = "auto" ] && command -v pg_dump >/dev/null 2>&1; }; then
    echo "[$(date -u +'%Y-%m-%dT%H:%M:%SZ')] Using host pg_dump execution..."
    pg_dump -h "${PGHOST:-127.0.0.1}" -p "${PGPORT:-5432}" -U "${POSTGRES_USER}" -d "${POSTGRES_DB}" -Fc > "${TEMP_BACKUP_FILEPATH}"
else
    echo "[$(date -u +'%Y-%m-%dT%H:%M:%SZ')] ERROR: No valid PostgreSQL backup execution method available (checked container, running compose, and host pg_dump)." >&2
    exit 1
fi

# Step 2: Enforce strict file permissions on temporary artifact
chmod 0600 "${TEMP_BACKUP_FILEPATH}"

# Step 3: Integrity verification prior to promotion
echo "[$(date -u +'%Y-%m-%dT%H:%M:%SZ')] Verifying dump integrity using pg_restore --list..."
if [ "${BACKUP_METHOD}" = "docker" ] || { [ "${BACKUP_METHOD}" = "auto" ] && [ -n "${CONTAINER_NAME:-}" ] && command -v docker >/dev/null 2>&1 && docker ps --format '{{.Names}}' 2>/dev/null | grep -q "^${CONTAINER_NAME}$"; }; then
    docker exec -i "${CONTAINER_NAME}" pg_restore --list < "${TEMP_BACKUP_FILEPATH}" > /dev/null 2>&1
elif [ "${BACKUP_METHOD}" = "compose" ] || { [ "${BACKUP_METHOD}" = "auto" ] && [ -n "${COMPOSE_FILE:-}" ] && [ -f "${COMPOSE_FILE}" ] && command -v docker >/dev/null 2>&1 && docker compose -f "${COMPOSE_FILE}" ps --status running -q postgres 2>/dev/null | grep -q .; }; then
    docker compose -f "${COMPOSE_FILE}" exec -T postgres pg_restore --list < "${TEMP_BACKUP_FILEPATH}" > /dev/null 2>&1
elif [ "${BACKUP_METHOD}" = "host" ] || { [ "${BACKUP_METHOD}" = "auto" ] && command -v pg_restore >/dev/null 2>&1; }; then
    pg_restore --list "${TEMP_BACKUP_FILEPATH}" > /dev/null 2>&1
else
    echo "[$(date -u +'%Y-%m-%dT%H:%M:%SZ')] ERROR: pg_restore is not available to verify backup integrity." >&2
    exit 1
fi
echo "[$(date -u +'%Y-%m-%dT%H:%M:%SZ')] Verification PASSED: Archive header and TOC are intact."
# Step 3b: Atomically promote verified temporary file to final backup filename
mv "${TEMP_BACKUP_FILEPATH}" "${BACKUP_FILEPATH}"
chmod 0600 "${BACKUP_FILEPATH}"
FILESIZE=$(stat -c%s "${BACKUP_FILEPATH}" 2>/dev/null || stat -f%z "${BACKUP_FILEPATH}" 2>/dev/null || echo "unknown")
echo "[$(date -u +'%Y-%m-%dT%H:%M:%SZ')] Dump successfully promoted: ${BACKUP_FILENAME} (${FILESIZE} bytes)"

# Step 4: Apply retention policy (prune backups older than RETENTION_DAYS)
echo "[$(date -u +'%Y-%m-%dT%H:%M:%SZ')] Pruning backups older than ${RETENTION_DAYS} days in ${BACKUP_DIR}..."
PRUNED_COUNT=0
while IFS= read -r -d '' old_file; do
    rm -f "${old_file}"
    PRUNED_COUNT=$((PRUNED_COUNT + 1))
    echo "[$(date -u +'%Y-%m-%dT%H:%M:%SZ')] Pruned obsolete backup: $(basename "${old_file}")"
done < <(find "${BACKUP_DIR}" -type f -name "campus_*.dump" -mtime +"${RETENTION_DAYS}" -print0)

echo "[$(date -u +'%Y-%m-%dT%H:%M:%SZ')] Backup process completed successfully. Pruned ${PRUNED_COUNT} old files."
