#!/bin/bash
# Database migration script for production deployment

set -e

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Load environment variables
if [ -f .env.production ]; then
    export $(cat .env.production | grep -v '^#' | xargs)
else
    echo -e "${RED}Error: .env.production file not found${NC}"
    exit 1
fi

# Function to log messages
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR:${NC} $1"
}

warning() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] WARNING:${NC} $1"
}

# Check if running in Docker or standalone
if [ -f /.dockerenv ]; then
    log "Running inside Docker container"
    DB_HOST=${POSTGRES_HOST:-postgres}
else
    log "Running outside Docker"
    DB_HOST=${POSTGRES_HOST:-localhost}
fi

# Database connection string
DATABASE_URL="postgresql://${POSTGRES_USER}:${POSTGRES_PASSWORD}@${DB_HOST}:${POSTGRES_PORT}/${POSTGRES_DB}"

# Check database connection
log "Checking database connection..."
if poetry run prisma db execute --url "$DATABASE_URL" --stdin <<< "SELECT 1;" > /dev/null 2>&1; then
    log "Database connection successful"
else
    error "Failed to connect to database"
    exit 1
fi

# Create backup before migration
if [ "$1" != "--no-backup" ]; then
    log "Creating database backup..."
    BACKUP_FILE="/app/database/backups/pre-migration-$(date +%Y%m%d-%H%M%S).sql"
    PGPASSWORD=$POSTGRES_PASSWORD pg_dump -h $DB_HOST -U $POSTGRES_USER -d $POSTGRES_DB > $BACKUP_FILE
    log "Backup created: $BACKUP_FILE"
fi

# Generate Prisma client
log "Generating Prisma client..."
poetry run prisma generate

# Run Prisma migrations
log "Running database migrations..."
poetry run prisma migrate deploy --schema=/app/prisma/schema.prisma

# Check migration status
log "Checking migration status..."
poetry run prisma migrate status --schema=/app/prisma/schema.prisma

# Run data seeding if requested
if [ "$1" == "--seed" ] || [ "$2" == "--seed" ]; then
    log "Running database seeding..."
    poetry run python scripts/seed_data.py
fi

# Create indexes for performance
log "Creating database indexes..."
poetry run prisma db execute --url "$DATABASE_URL" --file /app/database/indexes.sql || warning "Some indexes may already exist"

# Verify schema
log "Verifying database schema..."
poetry run prisma db pull --schema=/app/prisma/schema.prisma

# Run data validation
log "Running data validation..."
poetry run python scripts/validate_data.py

log "Migration completed successfully!"

# Print summary
echo -e "\n${GREEN}=== Migration Summary ===${NC}"
echo "Database: $POSTGRES_DB"
echo "Host: $DB_HOST"
echo "User: $POSTGRES_USER"
echo "Migration status: SUCCESS"
echo -e "${GREEN}========================${NC}\n"