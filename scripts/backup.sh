#!/bin/bash
# KisanMitra Database Backup Script
# Usage: ./scripts/backup.sh [--restore <backup_file>]
#
# Backups go to: ./backups/
# Keeps last 7 daily backups

set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
BACKUP_DIR="$PROJECT_ROOT/backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/kisanmitra_${TIMESTAMP}.sql.gz"
KEEP_DAYS=7

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log() { echo -e "${GREEN}[BACKUP]${NC} $1"; }
warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
error() { echo -e "${RED}[ERROR]${NC} $1"; exit 1; }

mkdir -p "$BACKUP_DIR"

# Load env
if [ -f "$PROJECT_ROOT/.env" ]; then
    source "$PROJECT_ROOT/.env"
fi
DB_PASSWORD="${DB_PASSWORD:-password}"

# Check for restore mode
if [ "${1:-}" = "--restore" ]; then
    RESTORE_FILE="${2:-}"
    [ -z "$RESTORE_FILE" ] && error "Usage: $0 --restore <backup_file>"
    [ ! -f "$RESTORE_FILE" ] && error "Backup file not found: $RESTORE_FILE"

    warn "This will OVERWRITE the current database. Are you sure? (y/N)"
    read -r confirm
    [ "$confirm" != "y" ] && { log "Restore cancelled."; exit 0; }

    log "Restoring from $RESTORE_FILE..."
    gunzip -c "$RESTORE_FILE" | docker exec -i kisanmitra-postgres psql -U admin -d kisanmitra
    log "Restore complete."
    exit 0
fi

# Backup
log "Starting PostgreSQL backup..."
log "  Database: kisanmitra"
log "  Output: $BACKUP_FILE"

docker exec kisanmitra-postgres pg_dump -U admin -d kisanmitra --no-owner --no-acl | gzip > "$BACKUP_FILE"

FILESIZE=$(du -h "$BACKUP_FILE" | cut -f1)
log "Backup complete: $FILESIZE"

# Cleanup old backups
log "Cleaning up backups older than $KEEP_DAYS days..."
DELETED=$(find "$BACKUP_DIR" -name "kisanmitra_*.sql.gz" -mtime +$KEEP_DAYS -delete -print | wc -l)
log "  Deleted $DELETED old backup(s)"

# List current backups
log "Current backups:"
ls -lh "$BACKUP_DIR"/kisanmitra_*.sql.gz 2>/dev/null | while read -r line; do
    echo "  $line"
done
