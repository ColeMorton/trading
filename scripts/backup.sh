#!/bin/sh
# Database backup script for cron job

set -e

# Configuration
BACKUP_DIR="/backups"
RETENTION_DAYS=${BACKUP_RETENTION_DAYS:-7}
TIMESTAMP=$(date +%Y%m%d-%H%M%S)
BACKUP_FILE="${BACKUP_DIR}/trading_db_${TIMESTAMP}.sql.gz"

# Ensure backup directory exists
mkdir -p ${BACKUP_DIR}

# Log function
log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $1"
}

# Perform backup
log "Starting database backup..."

# Create compressed backup
PGPASSWORD=${POSTGRES_PASSWORD} pg_dump \
    -h ${POSTGRES_HOST} \
    -U ${POSTGRES_USER} \
    -d ${POSTGRES_DB} \
    --verbose \
    --no-owner \
    --no-privileges \
    --exclude-table-data='*.log_*' \
    | gzip -9 > ${BACKUP_FILE}

# Check backup file
if [ -f ${BACKUP_FILE} ]; then
    BACKUP_SIZE=$(ls -lh ${BACKUP_FILE} | awk '{print $5}')
    log "Backup completed successfully: ${BACKUP_FILE} (${BACKUP_SIZE})"
else
    log "ERROR: Backup failed!"
    exit 1
fi

# Cleanup old backups
log "Cleaning up old backups..."
find ${BACKUP_DIR} -name "trading_db_*.sql.gz" -type f -mtime +${RETENTION_DAYS} -delete

# List remaining backups
log "Current backups:"
ls -lh ${BACKUP_DIR}/trading_db_*.sql.gz | tail -5

# Redis backup
if [ "${REDIS_HOST}" ]; then
    log "Backing up Redis..."
    redis-cli -h ${REDIS_HOST} -a ${REDIS_PASSWORD} --rdb ${BACKUP_DIR}/redis_${TIMESTAMP}.rdb
fi

log "Backup process completed"