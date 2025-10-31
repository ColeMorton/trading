#!/bin/bash
# Startup script for Trading CLI API

set -e  # Exit on error

echo "🚀 Starting Trading CLI API..."

# Change to project directory
cd "$(dirname "$0")/.."

# Check if docker-compose is available
if ! command -v docker-compose &> /dev/null; then
    echo "❌ docker-compose not found. Please install Docker Compose."
    exit 1
fi

# Check if docker-compose.services.yml exists
if [ ! -f docker-compose.services.yml ]; then
    echo "❌ docker-compose.services.yml not found"
    exit 1
fi

# Check if .env exists (optional - will use defaults)
if [ ! -f .env ]; then
    echo "ℹ️  No .env file found - using default configuration"
    echo "   (This is fine for development)"
fi

# Cleanup function
cleanup() {
    echo ""
    echo "🧹 Cleaning up..."
}
trap cleanup EXIT

# Check if Docker services are running
echo "📊 Checking services..."

# Function to wait for service health
wait_for_health() {
    local service=$1
    local max_attempts=30
    local attempt=1

    echo "⏳ Waiting for $service to be healthy..."
    while [ $attempt -le $max_attempts ]; do
        if docker-compose -f docker-compose.services.yml ps $service 2>/dev/null | grep -q "healthy"; then
            echo "✅ $service is healthy"
            return 0
        fi

        if [ $attempt -eq $max_attempts ]; then
            echo "❌ $service failed to become healthy after $max_attempts seconds"
            return 1
        fi

        sleep 1
        attempt=$((attempt + 1))
    done
}

# Start PostgreSQL if not running
set +e  # Temporarily disable exit on error for service checks
docker-compose -f docker-compose.services.yml ps postgres 2>/dev/null | grep -q "Up"
POSTGRES_RUNNING=$?
set -e  # Re-enable exit on error

if [ $POSTGRES_RUNNING -eq 0 ]; then
    echo "✅ PostgreSQL (Docker) is running"
    DB_READY=true
else
    echo "⚠️  Docker PostgreSQL not running. Starting it..."
    docker-compose -f docker-compose.services.yml up -d postgres
    wait_for_health postgres || exit 1
    DB_READY=true
fi

# Start Redis if not running
set +e  # Temporarily disable exit on error for service checks
docker-compose -f docker-compose.services.yml ps redis 2>/dev/null | grep -q "Up"
REDIS_RUNNING=$?
set -e  # Re-enable exit on error

if [ $REDIS_RUNNING -eq 0 ]; then
    echo "✅ Redis (Docker) is running"
else
    echo "⚠️  Docker Redis not running. Starting it..."
    docker-compose -f docker-compose.services.yml up -d redis
    wait_for_health redis || exit 1
fi

# Check if database tables exist
echo "🔍 Checking database tables..."
TABLE_CHECK=$(docker-compose -f docker-compose.services.yml exec -T postgres psql -U trading_user -d trading_db -t -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_name IN ('api_keys', 'jobs');" 2>/dev/null || echo "0")

if [ "$(echo $TABLE_CHECK | tr -d ' ')" = "2" ]; then
    echo "✅ Database tables already exist - skipping migrations"
else
    echo "🔄 Creating database tables..."
    if [ -f scripts/setup_database.sql ]; then
        docker-compose -f docker-compose.services.yml exec -T postgres psql -U trading_user -d trading_db < scripts/setup_database.sql
        echo "✅ Database tables created"
    else
        echo "⚠️  Database tables not found - you may need to run migrations manually"
    fi
fi

# Create result storage directory
echo "📁 Creating result storage directory..."
mkdir -p ./data/api_results

# Start API server
echo "🌐 Starting API server..."
echo "   URL: http://localhost:8000"
echo "   Docs: http://localhost:8000/api/docs"
echo ""

poetry run uvicorn app.api.main:app --host 0.0.0.0 --port 8000 --reload &
API_PID=$!

# Start ARQ worker
echo "⚙️  Starting ARQ worker..."
poetry run arq app.api.jobs.worker.WorkerSettings &
WORKER_PID=$!

echo ""
echo "✅ Trading CLI API started successfully!"
echo ""
echo "📚 API Documentation: http://localhost:8000/api/docs"
echo "🏥 Health Check: http://localhost:8000/health"
echo ""
echo "💡 Test with:"
echo "   curl http://localhost:8000/health"
echo ""
echo "Press Ctrl+C to stop..."
echo ""

# Wait for both processes
wait $API_PID $WORKER_PID
