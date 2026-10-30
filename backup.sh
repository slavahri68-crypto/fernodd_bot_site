#!/bin/sh
# ============================================================
#  backup.sh — ежедневный дамп PostgreSQL (хранит 30 последних)
# ============================================================
set -e

BACKUP_DIR=/backups
KEEP=30

mkdir -p "$BACKUP_DIR"

while true; do
    NOW=$(date +%Y%m%d_%H%M%S)
    FILE="$BACKUP_DIR/dump_$NOW.sql.gz"

    echo "[$(date '+%F %T')] Создаю бэкап $FILE..."
    if pg_dump | gzip > "$FILE"; then
        SIZE=$(du -h "$FILE" | cut -f1)
        echo "[$(date '+%F %T')] ✅ Готово ($SIZE)"
    else
        echo "[$(date '+%F %T')] ❌ Ошибка дампа"
        rm -f "$FILE"
    fi

    # ротация: оставляем последние $KEEP
    ls -1t "$BACKUP_DIR"/dump_*.sql.gz 2>/dev/null | tail -n +$((KEEP + 1)) | xargs -r rm --

    # ждём до 03:00 следующего дня
    NOW_SEC=$(date +%s)
    TARGET=$(date -d "tomorrow 03:00" +%s 2>/dev/null || date -v+1d -v3H -v0M -v0S +%s)
    SLEEP=$((TARGET - NOW_SEC))
    [ "$SLEEP" -lt 60 ] && SLEEP=86400
    echo "[$(date '+%F %T')] Следующий бэкап через $((SLEEP / 3600)) ч."
    sleep "$SLEEP"
done