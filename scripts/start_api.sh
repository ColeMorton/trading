#!/bin/bash
# Startup script for Trading CLI API

echo "🚀 Starting Trading CLI API..."

# Change to project directory
cd "$(dirname "$0")/.."

# Check if .env exists (optional - will use defaults)
if [ ! -f .env ]; then
    echo "ℹ️  No .env file found - using default configuration"
    echo "   (This is fine for development)"
fi

# Check if Docker services are running
echo "📊 Checking services..."

if docker-compose ps postgres | grep -q "Up"; then
    echo "✅ PostgreSQL (Docker) is running"
    DB_READY=true
else
    echo "⚠️  Docker PostgreSQL not running. Starting it..."
    docker-compose up -d postgres
    echo "⏳ Waiting for PostgreSQL to be healthy..."
    sleep 5
    DB_READY=true
fi

if docker-compose ps redis | grep -q "Up"; then
    echo "✅ Redis (Docker) is running"
else
    echo "⚠️  Docker Redis not running. Starting it..."
    docker-compose up -d redis
    echo "⏳ Waiting for Redis to be healthy..."
    sleep 3
fi

# Check if database tables exist
echo "🔍 Checking database tables..."
TABLE_CHECK=$(docker-compose exec -T postgres psql -U trading_user -d trading_db -t -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_name IN ('api_keys', 'jobs');" 2>/dev/null || echo "0")

if [ "$(echo $TABLE_CHECK | tr -d ' ')" = "2" ]; then
    echo "✅ Database tables already exist - skipping migrations"
else
    echo "🔄 Creating database tables..."
    if [ -f scripts/setup_database.sql ]; then
        docker-compose exec -T postgres psql -U trading_user -d trading_db < scripts/setup_database.sql
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
