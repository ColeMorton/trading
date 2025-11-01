#!/bin/bash
set -e

echo "🚀 Docker Entrypoint: Starting Trading API initialization..."

# Parse DATABASE_URL for connection details
# Format: postgresql://user:password@host:port/database
if [ -n "$DATABASE_URL" ]; then
  # Extract host from DATABASE_URL
  DB_HOST=$(echo "$DATABASE_URL" | sed -E 's|postgresql://[^@]+@([^:/]+).*|\1|')
  DB_PORT=$(echo "$DATABASE_URL" | sed -E 's|postgresql://[^@]+@[^:]+:([0-9]+).*|\1|')

  # Default to 5432 if port not found
  if [ -z "$DB_PORT" ] || [ "$DB_PORT" = "$DATABASE_URL" ]; then
    DB_PORT=5432
  fi

  echo "⏳ Waiting for PostgreSQL at $DB_HOST:$DB_PORT..."
  MAX_RETRIES=30
  RETRY_COUNT=0

  # Step 1: Wait for port to be open
  until nc -z "$DB_HOST" "$DB_PORT" 2>/dev/null || [ $RETRY_COUNT -eq $MAX_RETRIES ]; do
    RETRY_COUNT=$((RETRY_COUNT + 1))
    echo "PostgreSQL port is unavailable - attempt $RETRY_COUNT/$MAX_RETRIES"
    sleep 2
  done

  if [ $RETRY_COUNT -eq $MAX_RETRIES ]; then
    echo "❌ PostgreSQL port did not become ready in time"
    exit 1
  fi

  echo "✅ PostgreSQL port is open"

  # Step 2: Verify database accepts connections
  echo "⏳ Verifying database connection..."
  DB_USER=$(echo "$DATABASE_URL" | sed -E 's|postgresql://([^:]+):.*|\1|')
  DB_NAME=$(echo "$DATABASE_URL" | sed -E 's|.*/([^?]+).*|\1|')

  RETRY_COUNT=0
  MAX_DB_RETRIES=20

  until PGPASSWORD="$POSTGRES_PASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -c "SELECT 1" >/dev/null 2>&1 || [ $RETRY_COUNT -eq $MAX_DB_RETRIES ]; do
    RETRY_COUNT=$((RETRY_COUNT + 1))
    echo "Database connection not ready - attempt $RETRY_COUNT/$MAX_DB_RETRIES"
    sleep 2
  done

  if [ $RETRY_COUNT -eq $MAX_DB_RETRIES ]; then
    echo "❌ Database did not accept connections in time"
    exit 1
  fi

  echo "✅ Database connection verified"
else
  echo "⚠️  DATABASE_URL not set, skipping database connection check"
fi

# Run database migrations (only if RUN_MIGRATIONS is set to "true")
if [ "${RUN_MIGRATIONS:-false}" = "true" ]; then
  echo "📊 Running database migrations..."
  cd /app

  # Run Alembic migrations with detailed output
  echo "Running: alembic upgrade head"
  if alembic upgrade head 2>&1 | tee /tmp/migration.log; then
    echo "✅ Database migrations completed successfully"

    # Verify critical tables exist
    echo "🔍 Verifying database schema..."
    DB_USER=$(echo "$DATABASE_URL" | sed -E 's|postgresql://([^:]+):.*|\1|')
    DB_HOST=$(echo "$DATABASE_URL" | sed -E 's|postgresql://[^@]+@([^:/]+).*|\1|')
    DB_PORT=$(echo "$DATABASE_URL" | sed -E 's|postgresql://[^@]+@[^:]+:([0-9]+).*|\1|')
    DB_NAME=$(echo "$DATABASE_URL" | sed -E 's|.*/([^?]+).*|\1|')

    # Check for essential tables
    if PGPASSWORD="$POSTGRES_PASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -c "SELECT 1 FROM api_keys LIMIT 1" >/dev/null 2>&1; then
      echo "✅ Database schema verified (api_keys table exists)"
    else
      echo "⚠️  Warning: api_keys table not found, migrations may not have completed fully"
    fi
  else
    echo "❌ Database migration failed"
    echo "Migration log:"
    cat /tmp/migration.log
    exit 1
  fi
else
  echo "⏭️  Skipping database migrations (RUN_MIGRATIONS not set to 'true')"
fi

# Create result storage directory with proper permissions
# Must be done before switching to non-root user
RESULT_DIR="${RESULT_STORAGE_PATH:-data/api_results}"
if [ ! -d "$RESULT_DIR" ]; then
  echo "📁 Creating result storage directory: $RESULT_DIR"
  mkdir -p "$RESULT_DIR"
  # Set ownership to app user (UID 1001) if running as root
  if [ "$(id -u)" = "0" ]; then
    chown -R 1001:1001 "$RESULT_DIR"
    echo "✅ Set ownership of $RESULT_DIR to app user"
  fi
else
  echo "✅ Result storage directory already exists: $RESULT_DIR"
fi

echo "✨ Initialization complete!"
echo "🎯 Starting application: $@"

# Execute the main command (passed as arguments)
exec "$@"
