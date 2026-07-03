#!/usr/bin/env bash
# SaaS Boilerplate backup — fast DB + media + .env snapshot.
#
# Writes a timestamped snapshot under $BACKUP_ROOT and (optionally) pushes it
# offsite with restic. Run via the systemd timer (deploy/systemd/saas-backup.*).
#
# Install:
#   sudo cp deploy/scripts/backup.sh /usr/local/bin/saas-backup.sh
#   sudo chmod +x /usr/local/bin/saas-backup.sh
#   sudo mkdir -p /var/backups/saas && sudo chmod 700 /var/backups/saas
#   sudo cp deploy/systemd/saas-backup.{service,timer} /etc/systemd/system/
#   sudo systemctl daemon-reload && sudo systemctl enable --now saas-backup.timer
#
# Restore quick-reference:
#   pg_restore -h <host> -U <user> -d <db> -j 4 -c /var/backups/saas/<TS>/db.dump
#   tar -xzf /var/backups/saas/<TS>/media.tar.gz -C /opt/saas-boilerplate/backend/
#   gpg --decrypt --passphrase-file /etc/saas/backup.passphrase env.gpg > backend/.env
#
set -euo pipefail

PROJECT_DIR="${PROJECT_DIR:-/opt/saas-boilerplate}"
BACKEND_DIR="${BACKEND_DIR:-$PROJECT_DIR/backend}"
BACKUP_ROOT="${BACKUP_ROOT:-/var/backups/saas}"
RETENTION_DAYS="${RETENTION_DAYS:-14}"
PASSPHRASE_FILE="${PASSPHRASE_FILE:-/etc/saas/backup.passphrase}"
TIMESTAMP="$(date +%Y%m%d-%H%M%S)"
DEST="$BACKUP_ROOT/$TIMESTAMP"

mkdir -p "$DEST"
cd "$DEST"

# Load DATABASE_URL from the app .env.
set -a
# shellcheck disable=SC1091
. "$BACKEND_DIR/.env"
set +a
[ -n "${DATABASE_URL:-}" ] || { echo "DATABASE_URL not set in $BACKEND_DIR/.env"; exit 1; }

# --- 1. PostgreSQL (custom format, compressed) ----
DB_USER=$(echo "$DATABASE_URL" | sed -E 's|postgres(ql)?://([^:]+):.*|\2|')
DB_PASS=$(echo "$DATABASE_URL" | sed -E 's|postgres(ql)?://[^:]+:([^@]+)@.*|\2|')
DB_HOST=$(echo "$DATABASE_URL" | sed -E 's|.*@([^:/]+).*|\1|')
DB_PORT=$(echo "$DATABASE_URL" | sed -nE 's|.*:([0-9]+)/.*|\1|p'); DB_PORT="${DB_PORT:-5432}"
DB_NAME=$(echo "$DATABASE_URL" | sed -E 's|.*/([^/?]+).*|\1|')

PGPASSWORD="$DB_PASS" pg_dump -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" \
    --format=custom --compress=9 --no-owner --no-privileges -f db.dump "$DB_NAME"

# --- 2. Media (user uploads) ----
if [ -d "$BACKEND_DIR/media" ]; then
    tar -czf media.tar.gz -C "$BACKEND_DIR" media/
fi

# --- 3. .env (encrypted at rest if a passphrase is configured) ----
if [ -f "$BACKEND_DIR/.env" ]; then
    if [ -f "$PASSPHRASE_FILE" ]; then
        gpg --batch --yes --symmetric --cipher-algo AES256 \
            --passphrase-file "$PASSPHRASE_FILE" -o env.gpg "$BACKEND_DIR/.env"
    else
        cp "$BACKEND_DIR/.env" env.txt && chmod 600 env.txt
        echo "WARN: $PASSPHRASE_FILE missing — .env saved unencrypted"
    fi
fi

# --- 4. Manifest ----
cat > MANIFEST.txt <<EOF
SaaS Boilerplate backup
Timestamp: $TIMESTAMP
Host:      $(hostname -f 2>/dev/null || hostname)
DB:        $DB_NAME @ $DB_HOST:$DB_PORT
DB size:   $(du -h db.dump | cut -f1)
EOF

# --- 5. Offsite push (optional) — restic to B2/S3/etc. when configured ----
if [ -n "${RESTIC_REPOSITORY:-}" ] && command -v restic >/dev/null 2>&1; then
    restic backup "$DEST" --tag saas-backup || echo "WARN: restic backup failed"
    restic forget --keep-daily "$RETENTION_DAYS" --prune || true
fi

# --- 6. Local retention ----
find "$BACKUP_ROOT" -maxdepth 1 -type d -name '20*' -mtime +"$RETENTION_DAYS" -exec rm -rf {} +

echo "Backup written to $DEST ($(du -sh "$DEST" | cut -f1))"
