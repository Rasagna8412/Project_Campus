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

TIMESTAMP="$(date +%Y%m%d_%H%M%S)"
BACKUP_FILENAME="campus_${POSTGRES_DB}_${TIMESTAMP}.dump"
BACKUP_FILEPATH="${BACKUP_DIR}/${BACKUP_FILENAME}"

echo "[$(date -u +'%Y-%m-%dT%H:%M:%SZ')] Starting database backup for '${POSTGRES_DB}'..."

# Ensure backup destination directory exists with restricted permissions (0700)
mkdir -p "${BACKUP_DIR}"
chmod 0700 "${BACKUP_DIR}"

# Restrict file creation mask so dumps are created with 0600 (owner read/write only)
umask 077

# Step 1: Execute consistent compressed dump from postgres container
echo "[$(date -u +'%Y-%m-%dT%H:%M:%SZ')] Executing pg_dump from container '${CONTAINER_NAME}'..."
if docker ps --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
    docker exec "${CONTAINER_NAME}" pg_dump -U "${POSTGRES_USER}" -d "${POSTGRES_DB}" -Fc > "${BACKUP_FILEPATH}"
else
    # Fallback to docker compose execution if container name differs
    docker compose -f "${COMPOSE_FILE}" exec -T postgres pg_dump -U "${POSTGRES_USER}" -d "${POSTGRES_DB}" -Fc > "${BACKUP_FILEPATH}"
fi

# Step 2: Enforce strict file permissions
chmod 0600 "${BACKUP_FILEPATH}"
FILESIZE=$(stat -c%s "${BACKUP_FILEPATH}" 2>/dev/null || stat -f%z "${BACKUP_FILEPATH}" 2>/dev/null || echo "unknown")
echo "[$(date -u +'%Y-%m-%dT%H:%M:%SZ')] Dump completed: ${BACKUP_FILENAME} (${FILESIZE} bytes)"

# Step 3: Integrity verification
echo "[$(date -u +'%Y-%m-%dT%H:%M:%SZ')] Verifying dump integrity using pg_restore --list..."
if docker exec -i "${CONTAINER_NAME}" pg_restore --list < "${BACKUP_FILEPATH}" > /dev/null 2>&1; then
    echo "[$(date -u +'%Y-%m-%dT%H:%M:%SZ')] Verification PASSED: Archive header and TOC are intact."
else
    echo "[$(date -u +'%Y-%m-%dT%H:%M:%SZ')] ERROR: Backup verification FAILED! Removing corrupted file." >&2
    rm -f "${BACKUP_FILEPATH}"
    exit 1
fi

# Step 4: Apply retention policy (prune backups older than RETENTION_DAYS)
echo "[$(date -u +'%Y-%m-%dT%H:%M:%SZ')] Pruning backups older than ${RETENTION_DAYS} days in ${BACKUP_DIR}..."
PRUNED_COUNT=0
while IFS= read -r -d '' old_file; do
    rm -f "${old_file}"
    PRUNED_COUNT=$((PRUNED_COUNT + 1))
    echo "[$(date -u +'%Y-%m-%dT%H:%M:%SZ')] Pruned obsolete backup: $(basename "${old_file}")"
done < <(find "${BACKUP_DIR}" -type f -name "campus_*.dump" -mtime +"${RETENTION_DAYS}" -print0)

echo "[$(date -u +'%Y-%m-%dT%H:%M:%SZ')] Backup process completed successfully. Pruned ${PRUNED_COUNT} old files."
