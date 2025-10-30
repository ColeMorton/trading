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

  until nc -z "$DB_HOST" "$DB_PORT" 2>/dev/null || [ $RETRY_COUNT -eq $MAX_RETRIES ]; do
    RETRY_COUNT=$((RETRY_COUNT + 1))
    echo "PostgreSQL is unavailable - attempt $RETRY_COUNT/$MAX_RETRIES"
    sleep 2
  done

  if [ $RETRY_COUNT -eq $MAX_RETRIES ]; then
    echo "❌ PostgreSQL did not become ready in time"
    exit 1
  fi

  echo "✅ PostgreSQL is ready"
else
  echo "⚠️  DATABASE_URL not set, skipping database connection check"
fi

# Run database migrations (only if RUN_MIGRATIONS is set to "true")
if [ "${RUN_MIGRATIONS:-false}" = "true" ]; then
  echo "📊 Running database migrations..."
  cd /app

  # Run Alembic migrations
  if alembic upgrade head; then
    echo "✅ Database migrations completed successfully"
  else
    echo "❌ Database migration failed"
    exit 1
  fi
else
  echo "⏭️  Skipping database migrations (RUN_MIGRATIONS not set to 'true')"
fi

echo "✨ Initialization complete!"
echo "🎯 Starting application: $@"

# Execute the main command (passed as arguments)
exec "$@"
