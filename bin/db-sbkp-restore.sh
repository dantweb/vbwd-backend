#!/bin/bash
# Database Backup and Restore Script
#
# Usage:
#   ./bin/db-sbkp-restore.sh --create_backup <filename> [--gz]
#   ./bin/db-sbkp-restore.sh --restore_backend <filename> [--force]
#
# Commands:
#   --create_backup <filename>    Create a full database backup (schema + data)
#   --restore_backend <filename>  Restore database from backup
#                                 Drops current DB, recreates, imports backup.
#                                 Does NOT run install_demo_data.
#
# Options:
#   --gz      Gzip the backup output (use with --create_backup)
#   --force   Skip confirmation prompts (use with --restore_backend)

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$SCRIPT_DIR"

# Colors
RED='\033[0;31m'
YELLOW='\033[1;33m'
GREEN='\033[0;32m'
NC='\033[0m'

# Defaults
COMMAND=""
FILENAME=""
GZ=false
FORCE=false

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --create_backup)
            COMMAND="backup"
            FILENAME="$2"
            shift 2
            ;;
        --gz)
            GZ=true
            shift
            ;;
        --restore_backend)
            COMMAND="restore"
            FILENAME="$2"
            shift 2
            ;;
        --force)
            FORCE=true
            shift
            ;;
        --help|-h)
            echo "Usage: $0 <command> [options]"
            echo ""
            echo "Commands:"
            echo "  --create_backup <filename>    Create a full database backup (schema + data)"
            echo "  --restore_backend <filename>  Restore database from backup"
            echo ""
            echo "Options:"
            echo "  --gz                          Gzip the backup output (use with --create_backup)"
            echo "  --force                       Skip confirmation prompts (use with --restore_backend)"
            echo "  --help, -h                    Show this help message"
            echo ""
            echo "Examples:"
            echo "  $0 --create_backup backup.sql"
            echo "  $0 --create_backup backup.sql.gz --gz"
            echo "  $0 --restore_backend backup.sql"
            echo "  $0 --restore_backend backup.sql.gz"
            echo "  $0 --restore_backend backup.sql --force"
            echo ""
            exit 0
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# Validate command
if [ -z "$COMMAND" ]; then
    echo -e "${RED}ERROR: No command specified${NC}"
    echo "Use --help for usage information"
    exit 1
fi

if [ -z "$FILENAME" ]; then
    echo -e "${RED}ERROR: No filename specified${NC}"
    echo "Use --help for usage information"
    exit 1
fi

# Load .env file
if [ -f ".env" ]; then
    set -a
    # shellcheck disable=SC1090
    source <(grep -v '^#' .env | grep -v '^\s*$' | sed 's/\r$//')
    set +a
fi

# Database credentials
DB_USER="${POSTGRES_USER:-vbwd}"
DB_NAME="${POSTGRES_DB:-vbwd}"

# Check that postgres container is running
check_containers() {
    if ! docker compose ps 2>/dev/null | grep -qE "postgres.*(Up|running)"; then
        echo -e "${RED}ERROR: PostgreSQL container is not running${NC}"
        echo "Start the containers first with: docker compose up -d"
        exit 1
    fi
}

# ─── BACKUP ──────────────────────────────────────────────────────────────────
if [ "$COMMAND" = "backup" ]; then
    check_containers

    echo -e "${GREEN}╔════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║                    Creating Database Backup                   ║${NC}"
    echo -e "${GREEN}╚════════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    echo "  Database : $DB_NAME"
    echo "  Output   : $FILENAME"
    if [ "$GZ" = true ]; then
        echo "  Format   : Compressed (gzip)"
    else
        echo "  Format   : Plain SQL"
    fi
    echo ""

    if [ "$GZ" = true ]; then
        docker compose exec -T postgres pg_dump \
            -U "$DB_USER" \
            --no-password \
            "$DB_NAME" | gzip > "$FILENAME"
    else
        docker compose exec -T postgres pg_dump \
            -U "$DB_USER" \
            --no-password \
            "$DB_NAME" > "$FILENAME"
    fi

    FILESIZE=$(du -sh "$FILENAME" | cut -f1)

    echo -e "${GREEN}╔════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║                   Backup Created Successfully                 ║${NC}"
    echo -e "${GREEN}╚════════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    echo "  File: $FILENAME ($FILESIZE)"
    echo ""
fi

# ─── RESTORE ─────────────────────────────────────────────────────────────────
if [ "$COMMAND" = "restore" ]; then
    if [ ! -f "$FILENAME" ]; then
        echo -e "${RED}ERROR: File not found: $FILENAME${NC}"
        exit 1
    fi

    check_containers

    # Auto-detect gzip
    IS_GZ=false
    if [[ "$FILENAME" == *.gz ]]; then
        IS_GZ=true
    elif command -v file &>/dev/null && file "$FILENAME" 2>/dev/null | grep -q "gzip"; then
        IS_GZ=true
    fi

    FILESIZE=$(du -sh "$FILENAME" | cut -f1)

    echo -e "${YELLOW}╔════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${YELLOW}║                  DATABASE RESTORE WARNING                      ║${NC}"
    echo -e "${YELLOW}╚════════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    echo -e "${RED}⚠️  THIS WILL PERMANENTLY DELETE ALL CURRENT DATABASE DATA ⚠️${NC}"
    echo ""
    echo "This will:"
    echo "  1. Terminate all connections to the database"
    echo "  2. Drop the entire PostgreSQL database"
    echo "  3. Recreate an empty database"
    echo "  4. Import from: $FILENAME ($FILESIZE)"
    if [ "$IS_GZ" = true ]; then
        echo "     Format: gzip compressed (auto-detected)"
    else
        echo "     Format: plain SQL"
    fi
    echo ""
    echo "  Note: migrations and demo data are NOT run — the backup is imported as-is."
    echo ""

    if [ "$FORCE" = false ]; then
        echo -e "${YELLOW}This operation CANNOT be undone!${NC}"
        echo ""
        read -r -p "Type 'RESTORE' to continue, or anything else to cancel: " CONFIRMATION
        if [ "$CONFIRMATION" != "RESTORE" ]; then
            echo -e "${GREEN}Operation cancelled. Database unchanged.${NC}"
            exit 0
        fi
    fi

    echo ""
    echo -e "${GREEN}╔════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║              Starting Database Restore Process                 ║${NC}"
    echo -e "${GREEN}╚════════════════════════════════════════════════════════════════╝${NC}"
    echo ""

    # Step 1: Terminate connections and drop database
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "Step 1/3: Dropping existing database"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

    docker compose exec -T postgres psql -U "$DB_USER" -d postgres << EOF
SELECT pg_terminate_backend(pg_stat_activity.pid)
FROM pg_stat_activity
WHERE pg_stat_activity.datname = '$DB_NAME'
  AND pid <> pg_backend_pid();

DROP DATABASE IF EXISTS $DB_NAME;
EOF

    echo -e "${GREEN}✓ Database dropped${NC}"

    # Step 2: Create fresh database
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "Step 2/3: Creating fresh database"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

    docker compose exec -T postgres psql -U "$DB_USER" -d postgres << EOF
CREATE DATABASE $DB_NAME
    WITH OWNER = $DB_USER
    ENCODING = 'UTF8'
    LC_COLLATE = 'en_US.utf8'
    LC_CTYPE = 'en_US.utf8'
    TEMPLATE = template0;
EOF

    echo -e "${GREEN}✓ Database created${NC}"

    # Step 3: Import backup
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "Step 3/3: Importing backup"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "  Source: $FILENAME"

    if [ "$IS_GZ" = true ]; then
        gunzip -c "$FILENAME" | docker compose exec -T postgres psql \
            -U "$DB_USER" \
            -d "$DB_NAME" \
            --set ON_ERROR_STOP=off \
            -q
    else
        docker compose exec -T postgres psql \
            -U "$DB_USER" \
            -d "$DB_NAME" \
            --set ON_ERROR_STOP=off \
            -q < "$FILENAME"
    fi

    echo -e "${GREEN}✓ Backup imported${NC}"

    echo ""
    echo -e "${GREEN}╔════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║             Database Restore Completed Successfully            ║${NC}"
    echo -e "${GREEN}╚════════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    echo "  ✓ Database dropped and recreated"
    echo "  ✓ Backup imported: $FILENAME"
    echo ""
fi
