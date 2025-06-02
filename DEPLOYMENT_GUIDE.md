# Production Deployment Guide

## Prerequisites

- Docker Engine 20.10+
- Docker Compose 2.0+
- Domain name with DNS configured
- SSL certificates (Let's Encrypt recommended)
- PostgreSQL backup storage
- Monitoring infrastructure (optional)

## Environment Setup

### 1. Clone Repository

```bash
git clone https://github.com/your-org/trading.git
cd trading
```

### 2. Configure Environment

```bash
# Copy production environment template
cp .env.production.example .env.production

# Edit with your values
vim .env.production
```

Required environment variables:
- `POSTGRES_PASSWORD` - Strong password for PostgreSQL
- `REDIS_PASSWORD` - Strong password for Redis
- `SECRET_KEY` - Application secret key (generate with `openssl rand -hex 32`)
- `API_KEY` - API authentication key (if using API key auth)
- `ALLOWED_HOSTS` - Comma-separated list of allowed hostnames
- `CORS_ORIGINS` - Comma-separated list of allowed CORS origins

### 3. SSL Certificates

For Let's Encrypt:
```bash
# Install certbot
sudo apt-get update
sudo apt-get install certbot

# Generate certificates
sudo certbot certonly --standalone -d your-domain.com -d www.your-domain.com

# Copy certificates
sudo cp /etc/letsencrypt/live/your-domain.com/fullchain.pem nginx/ssl/
sudo cp /etc/letsencrypt/live/your-domain.com/privkey.pem nginx/ssl/
```

## Deployment Steps

### 1. Build Images

```bash
# Build production images
docker compose -f docker-compose.prod.yml build
```

### 2. Database Migration

```bash
# Start only database service
docker compose -f docker-compose.prod.yml up -d postgres

# Run migrations
docker compose -f docker-compose.prod.yml run --rm api ./scripts/migrate.sh

# Verify migration
docker compose -f docker-compose.prod.yml run --rm api poetry run prisma migrate status
```

### 3. Start Services

```bash
# Start all services
docker compose -f docker-compose.prod.yml up -d

# Check service health
docker compose -f docker-compose.prod.yml ps
curl http://localhost/health/detailed
```

### 4. Enable HTTPS

Update `nginx/conf.d/default.conf` to uncomment HTTPS configuration:
```nginx
server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name your-domain.com;
    
    ssl_certificate /etc/nginx/ssl/fullchain.pem;
    ssl_certificate_key /etc/nginx/ssl/privkey.pem;
    
    # ... rest of configuration
}
```

Restart nginx:
```bash
docker compose -f docker-compose.prod.yml restart nginx
```

## Monitoring Setup

### 1. Enable Monitoring Stack

```bash
# Start monitoring services
docker compose -f docker-compose.prod.yml --profile monitoring up -d

# Access Grafana
# URL: http://your-domain.com:3000
# Default login: admin / <GRAFANA_PASSWORD>
```

### 2. Configure Alerts

1. Access Grafana at http://your-domain.com:3000
2. Import dashboards from `monitoring/grafana/dashboards/`
3. Configure alert channels (email, Slack, etc.)

## Backup Configuration

### 1. Enable Automated Backups

```bash
# Start backup service
docker compose -f docker-compose.prod.yml --profile backup up -d

# Verify backup schedule
docker compose -f docker-compose.prod.yml logs db_backup
```

### 2. Manual Backup

```bash
# Create manual backup
docker compose -f docker-compose.prod.yml exec postgres \
    pg_dump -U $POSTGRES_USER $POSTGRES_DB | gzip > backup_$(date +%Y%m%d_%H%M%S).sql.gz
```

## Maintenance

### Update Application

```bash
# Pull latest changes
git pull origin main

# Rebuild images
docker compose -f docker-compose.prod.yml build

# Restart services with zero downtime
docker compose -f docker-compose.prod.yml up -d --no-deps --build api
docker compose -f docker-compose.prod.yml up -d --no-deps --build frontend
```

### View Logs

```bash
# All services
docker compose -f docker-compose.prod.yml logs -f

# Specific service
docker compose -f docker-compose.prod.yml logs -f api

# Last 100 lines
docker compose -f docker-compose.prod.yml logs --tail=100 api
```

### Database Maintenance

```bash
# Vacuum database
docker compose -f docker-compose.prod.yml exec postgres \
    psql -U $POSTGRES_USER -d $POSTGRES_DB -c "VACUUM ANALYZE;"

# Reindex
docker compose -f docker-compose.prod.yml exec postgres \
    psql -U $POSTGRES_USER -d $POSTGRES_DB -c "REINDEX DATABASE $POSTGRES_DB;"
```

## Troubleshooting

### Service Won't Start

```bash
# Check logs
docker compose -f docker-compose.prod.yml logs <service_name>

# Check health
curl http://localhost/health/detailed

# Restart service
docker compose -f docker-compose.prod.yml restart <service_name>
```

### Database Connection Issues

```bash
# Test database connection
docker compose -f docker-compose.prod.yml exec api \
    poetry run python -c "from app.database.config import get_database; import asyncio; asyncio.run(get_database())"

# Check database logs
docker compose -f docker-compose.prod.yml logs postgres
```

### High Memory Usage

```bash
# Check resource usage
docker stats

# Limit memory in docker-compose.prod.yml
deploy:
  resources:
    limits:
      memory: 2G
```

## Security Checklist

- [ ] Strong passwords for all services
- [ ] SSL certificates installed and configured
- [ ] Firewall rules configured (only expose necessary ports)
- [ ] API key authentication enabled for sensitive endpoints
- [ ] Rate limiting configured appropriately
- [ ] CORS origins restricted to your domains
- [ ] Database backups configured and tested
- [ ] Monitoring and alerting enabled
- [ ] Log rotation configured
- [ ] Security headers verified

## Performance Optimization

### 1. Enable Redis Caching

Verify Redis is being used:
```bash
docker compose -f docker-compose.prod.yml exec redis redis-cli
> INFO stats
```

### 2. Database Query Optimization

```bash
# Analyze slow queries
docker compose -f docker-compose.prod.yml exec postgres \
    psql -U $POSTGRES_USER -d $POSTGRES_DB -c "
    SELECT query, calls, mean_exec_time
    FROM pg_stat_statements
    ORDER BY mean_exec_time DESC
    LIMIT 10;"
```

### 3. CDN Configuration

For static assets, configure a CDN:
1. Point CDN to your domain
2. Update `VITE_API_URL` to use CDN URL
3. Configure cache headers in nginx

## Rollback Procedure

If deployment fails:

```bash
# Stop new containers
docker compose -f docker-compose.prod.yml down

# Restore database backup
gunzip < backup_file.sql.gz | docker compose -f docker-compose.prod.yml exec -T postgres \
    psql -U $POSTGRES_USER $POSTGRES_DB

# Start previous version
docker compose -f docker-compose.prod.yml up -d
```

## Support

For issues:
1. Check application logs
2. Review health check endpoints
3. Consult monitoring dashboards
4. Create issue in GitHub repository