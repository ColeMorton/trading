# AWS Deployment Specification

**Document Version:** 1.0
**Date:** 2025-11-01
**Status:** Pre-Production Planning

## Executive Summary

This document specifies the optimal AWS deployment architecture for the Trading Platform API. Based on analysis of the application architecture, traffic requirements, budget constraints, and operational priorities, **EC2 + Docker Compose with managed database services** is the recommended approach.

**Key Metrics:**

- **Expected Traffic:** < 100 requests/minute (MVP phase)
- **Budget Target:** < $200/month
- **Estimated Cost:** $20-50/month
- **Deployment Complexity:** Low (leverage existing Docker setup)
- **Time to Production:** ~2 hours

---

## Application Architecture Analysis

### Technology Stack

**Web Framework:** FastAPI (async/await, ASGI via Uvicorn)

- Production configuration: 4 Uvicorn workers with uvloop
- Server-Sent Events (SSE) for real-time streaming
- API versioning: `/api/v1/`

**Background Processing:** ARQ (async Redis-based job queue)

- Separate worker process for compute-intensive tasks
- 10 max concurrent jobs, 1-hour timeout
- 3 retry attempts with exponential backoff

**Database:** PostgreSQL

- Connection pool: 20 base + 10 overflow
- Async driver: asyncpg
- ORM: SQLAlchemy 2.0+

**Cache/Queue:** Redis

- Dual purpose: caching + job queue (ARQ)
- Max connections: 50
- LRU eviction policy (512MB limit in docker-compose)

### Resource Requirements

**API Service:**

- **CPU:** 2 cores (limit), 0.5 cores (reservation)
- **Memory:** 2GB (limit), 512MB (reservation)
- **Storage:** Shared volume for `/app/data/api_results`

**Worker Service:**

- **CPU:** Similar to API (compute-intensive workloads)
- **Memory:** 2GB recommended
- **Workload:** VectorBT backtesting, Polars DataFrame operations, portfolio optimization

**Rate Limiting:**

- 60 requests/minute (default)
- Burst: +10 requests
- SSE: 3 concurrent connections per session

### Key Dependencies

**Compute-Intensive Libraries:**

- `vectorbt ^0.28.0` - Backtesting engine (CPU-bound)
- `polars ^1.5.0` - High-performance DataFrames (memory-intensive)
- `skfolio ^0.6.0` - Portfolio optimization
- `numpy`, `pyarrow`, `plotly`, `seaborn`

**External Services:**

- Yahoo Finance API (via `yfinance`)

---

## Recommended Architecture: EC2 + Docker Compose

### Architecture Diagram

```
┌─────────────────────────────────────────────────┐
│ AWS Cloud                                       │
│                                                 │
│  ┌───────────────────────────────────────────┐ │
│  │ EC2: t3a.small (2 vCPU, 2GB RAM)          │ │
│  │ Ubuntu 24.04 LTS                          │ │
│  │                                           │ │
│  │  ┌─────────────────────────────────────┐ │ │
│  │  │ Docker Compose Stack                │ │ │
│  │  │                                     │ │ │
│  │  │  • FastAPI (port 8000)             │ │ │
│  │  │  • ARQ Worker                      │ │ │
│  │  │  • Nginx (reverse proxy: 80/443)   │ │ │
│  │  └─────────────────────────────────────┘ │ │
│  │                                           │ │
│  │  Storage: 30GB EBS (gp3)                 │ │
│  │  Network: Elastic IP attached            │ │
│  └───────────────────────────────────────────┘ │
│                 │                               │
│                 │                               │
└─────────────────┼───────────────────────────────┘
                  │
                  ├─→ Neon PostgreSQL (Serverless)
                  │   - Free tier: 0.5GB storage
                  │   - Paid tier: $19/month (3GB)
                  │   - Auto-pause when idle
                  │
                  └─→ Upstash Redis (Serverless)
                      - Free tier: 10K requests/day
                      - Paid tier: $10/month
                      - Pay-per-request pricing
```

### Why This Architecture?

**1. Leverage Existing Docker Setup**

- Your `docker-compose.yml` works as-is with minimal changes
- No need to learn ECS task definitions, Fargate, or complex AWS services
- Existing development environment translates directly to production

**2. Extremely Cost-Effective**

- EC2 reserved instance: $15/month (vs. Fargate: $40+/month)
- Free tier databases available for MVP testing
- No ALB costs ($16/month saved)
- Direct Elastic IP (free when attached)

**3. Simple Deployment**

- SSH into EC2, run `docker-compose up -d`
- Systemd service for auto-start on reboot
- Fast iteration cycles (push code, restart containers)

**4. Easy Migration Path**

- When traffic grows, migrate to ECS Fargate using same containers
- Infrastructure-as-Code (Terraform) can be added later
- No architecture redesign needed for scaling

**5. Minimal DevOps Experience Required**

- Docker knowledge you already have
- Standard Linux server administration
- No complex AWS networking or IAM policies initially

---

## Cost Breakdown

### Monthly Costs (Optimized)

| Component                 | Specification                                           | Monthly Cost   |
| ------------------------- | ------------------------------------------------------- | -------------- |
| **EC2 Instance**          | t3a.small (2 vCPU, 2GB RAM)<br>1-year reserved instance | $15            |
| **EBS Volume**            | 30GB gp3 storage                                        | $3             |
| **Neon PostgreSQL**       | Free tier (0.5GB)<br>_or Paid tier (3GB)_               | $0<br>_$19_    |
| **Upstash Redis**         | Free tier (10K req/day)<br>_or Paid tier_               | $0<br>_$10_    |
| **Elastic IP**            | Attached to running instance                            | $0             |
| **Data Transfer**         | Low traffic estimate                                    | $1-5           |
| **Backups**               | EBS snapshots (weekly)                                  | $1-2           |
|                           |                                                         |                |
| **TOTAL (Free tier DBs)** |                                                         | **~$20/month** |
| **TOTAL (Paid tier DBs)** |                                                         | **~$50/month** |

### Cost Optimization Notes

1. **Reserved Instance:** 1-year commitment saves ~40% vs. on-demand
2. **Spot Instance:** Could use for non-critical testing (~70% savings) but less predictable
3. **gp3 vs gp2:** gp3 is 20% cheaper with better baseline performance
4. **Serverless Databases:** Auto-pause when idle (perfect for MVP)
5. **No NAT Gateway:** Public subnet with direct internet access ($32/month saved)

### Cost Comparison with Alternatives

| Approach                               | Monthly Cost | Complexity |
| -------------------------------------- | ------------ | ---------- |
| **EC2 + Docker Compose** (Recommended) | $20-50       | Low        |
| AWS Lightsail Container Service        | $95-100      | Medium     |
| ECS Fargate (on-demand)                | $150-200     | High       |
| ECS Fargate (Spot)                     | $75-85       | Medium     |
| Elastic Beanstalk                      | $80-120      | Medium     |

---

## Infrastructure Requirements

### EC2 Instance Specification

**Instance Type:** `t3a.small` (AMD-based, cost-optimized)

- **vCPUs:** 2
- **Memory:** 2GB
- **Network:** Up to 5 Gbps
- **EBS-Optimized:** Yes
- **Cost:** $0.0188/hour ($13.76/month on-demand, ~$15/month reserved)

**Why t3a.small?**

- Sufficient for 2 containers (API + Worker) at low traffic
- Burstable CPU (baseline 20%, burst to 100%) perfect for variable workloads
- AMD processors are 10% cheaper than Intel t3 instances
- Can upgrade to t3a.medium (4GB RAM) if needed for $25/month

**Operating System:** Ubuntu 24.04 LTS (free, long-term support)

**Storage:**

- **Root Volume:** 30GB gp3 ($2.40/month)
- **IOPS:** 3000 baseline (sufficient for small database workloads)
- **Throughput:** 125 MB/s

**Networking:**

- **VPC:** Default VPC (or custom for isolation)
- **Subnet:** Public subnet with Internet Gateway
- **Security Group:** Allow ports 22 (SSH), 80 (HTTP), 443 (HTTPS), 8000 (API - optional for direct access)
- **Elastic IP:** Static public IP ($0 when attached, $3.60/month if unused)

### Database Services

#### Option 1: Neon PostgreSQL (Recommended)

**Free Tier:**

- 0.5GB storage
- Auto-pause after 5 minutes of inactivity
- 300 compute hours/month
- Perfect for MVP testing

**Paid Tier ($19/month):**

- 3GB storage
- Autoscaling compute
- Point-in-time recovery (7 days)
- No connection limits

**Pros:**

- Serverless (scales to zero)
- Branching for development environments
- PostgreSQL 15+ compatible
- Low latency from AWS regions

**Cons:**

- Cold start latency (if auto-paused)
- External dependency

#### Option 2: AWS RDS PostgreSQL

**t4g.micro ($12/month):**

- 1 vCPU, 1GB RAM
- 20GB storage included
- Single-AZ deployment
- Automated backups (7 days)

**Pros:**

- Native AWS integration
- Predictable performance (no auto-pause)
- CloudWatch monitoring included

**Cons:**

- More expensive than Neon free tier
- Always-on (no scale-to-zero)

#### Redis Options

**Upstash Redis (Recommended):**

- Free tier: 10,000 requests/day
- Paid tier: $10/month for 100K requests/day
- Serverless, pay-per-request
- Global replication available

**AWS ElastiCache Redis:**

- cache.t4g.micro: $12/month
- 0.5GB memory
- Single-node (no replication in t4g.micro)

### Backup Strategy

**Application Data:**

- Daily backup of `/app/data/api_results` to S3 (or local snapshots)
- Retention: 7 days

**Database:**

- Neon: Automatic daily backups (7-day retention on paid tier)
- RDS: Automated daily backups (7-day retention)

**EC2:**

- Weekly EBS snapshots ($0.05/GB-month)
- Incremental backups (only changed blocks)
- 30GB snapshot = ~$1.50/month

---

## Deployment Architecture Details

### Docker Compose Adaptation

**Current Setup:** `docker-compose.yml` with services:

- `trading-api` - FastAPI application
- `arq-worker` - Background job processor
- `postgres` - PostgreSQL 15-alpine
- `redis` - Redis 7-alpine
- `nginx` - Reverse proxy

**AWS Adaptation:** `docker-compose.aws.yml` (override)

- Remove `postgres` service → Use Neon/RDS
- Remove `redis` service → Use Upstash/ElastiCache
- Keep `trading-api`, `arq-worker`, `nginx`
- Update environment variables for external DB/Redis URLs

### Security Configuration

**EC2 Security Group Rules:**

| Type   | Protocol | Port | Source    | Purpose                      |
| ------ | -------- | ---- | --------- | ---------------------------- |
| SSH    | TCP      | 22   | Your IP   | Administration               |
| HTTP   | TCP      | 80   | 0.0.0.0/0 | Public web access            |
| HTTPS  | TCP      | 443  | 0.0.0.0/0 | Secure web access            |
| Custom | TCP      | 8000 | 0.0.0.0/0 | Direct API access (optional) |

**Hardening:**

- Disable password authentication (SSH keys only)
- Install `fail2ban` for brute-force protection
- Enable UFW firewall
- Regular security updates via `unattended-upgrades`
- Non-root user for application deployment

**Secrets Management:**

- Environment variables in `.env` file (not committed to git)
- Restrict file permissions: `chmod 600 .env`
- Consider AWS Secrets Manager for production ($0.40/secret/month)

### SSL/TLS Configuration

**Let's Encrypt (Free):**

- Nginx with certbot for automatic SSL
- Auto-renewal every 90 days
- HTTP → HTTPS redirect

**AWS Certificate Manager (ACM):**

- Free SSL certificates
- Requires Route53 or ALB (adds $16/month for ALB)
- Not worth it for EC2-only deployment

---

## Alternative Architectures Considered

### AWS Lightsail Container Service

**Cost:** $95-100/month

- 2× containers at $40/month (2GB RAM each) = $80
- Lightsail PostgreSQL: $15/month
- **Total:** $95/month

**Pros:**

- Simplified ECS with fixed pricing
- Load balancing included
- Easy to understand

**Cons:**

- 2× over budget
- Less control than raw ECS
- Still requires container configuration

**Verdict:** Too expensive for MVP phase

### ECS Fargate (On-Demand)

**Cost:** $150-200/month

- API task (1 vCPU, 2GB): ~$30/month
- Worker task (1 vCPU, 2GB): ~$30/month
- ALB: $16/month
- RDS t4g.micro: $12/month
- ElastiCache: $12/month
- Data transfer: $5-10/month
- EFS (shared storage): $5/month
- **Total:** $110-115/month minimum

**Pros:**

- Fully managed, serverless containers
- Auto-scaling built-in
- No server patching

**Cons:**

- Over budget
- Higher complexity (task definitions, networking, IAM)
- Overkill for < 100 req/min

**Verdict:** Better for production scale, not MVP

### ECS Fargate Spot

**Cost:** $75-85/month

- API/Worker on Spot: ~$26/month (70% savings)
- ALB: $16/month
- Neon PostgreSQL: $19/month
- Upstash Redis: $10/month
- EFS: $5/month
- **Total:** $76/month

**Pros:**

- Cost-effective serverless option
- Professional architecture
- Easy to scale

**Cons:**

- Still near budget limit
- Spot instances can be interrupted (requires graceful shutdown)
- Higher learning curve

**Verdict:** Viable alternative if you want AWS-native from day one

### Elastic Beanstalk

**Cost:** $80-120/month

- Manages EC2, ALB, Auto Scaling automatically
- But you still pay for underlying resources
- Adds ~$20-30/month in overhead

**Pros:**

- Platform-as-a-Service experience
- Built-in monitoring and deployment

**Cons:**

- Less control than raw EC2
- More expensive than EC2 + Docker Compose
- Requires Beanstalk-specific configuration

**Verdict:** Not cost-effective for simple Docker workload

---

## Migration Path: EC2 → ECS Fargate

When traffic exceeds 500-1000 req/min or you need high availability:

### Phase 1: Current (EC2 + Docker Compose)

- Single EC2 instance
- Docker Compose orchestration
- External databases (Neon/Upstash)
- **Cost:** $20-50/month

### Phase 2: Transition (Multi-Container Setup)

- Separate task definitions (ECS-compatible)
- Push images to ECR
- Test ECS locally (optional: LocalStack)
- **Preparation:** 1-2 weeks

### Phase 3: Production Migration (ECS Fargate)

- Deploy to ECS Fargate with Spot pricing
- Application Load Balancer
- Auto-scaling policies (CPU/memory based)
- **Cost:** $75-150/month (depending on scale)
- **Downtime:** < 5 minutes (blue/green deployment)

### Key Benefits of Migration Path:

1. **No Architecture Redesign:** Same containers work in both environments
2. **Gradual Learning Curve:** Master Docker first, then ECS
3. **Cost-Justified:** Only pay for complexity when you need it
4. **Proven Pattern:** Thousands of companies follow this path

---

## Implementation Checklist

### Pre-Deployment

- [ ] Create AWS account (if needed)
- [ ] Setup Neon PostgreSQL database
- [ ] Setup Upstash Redis instance
- [ ] Generate SSH key pair for EC2
- [ ] Decide on domain name (optional for SSL)

### Infrastructure Setup

- [ ] Launch EC2 t3a.small instance (Ubuntu 24.04 LTS)
- [ ] Attach 30GB gp3 EBS volume
- [ ] Allocate and associate Elastic IP
- [ ] Configure security group rules
- [ ] Install Docker and Docker Compose
- [ ] Create non-root deployment user

### Application Deployment

- [ ] Clone repository to EC2
- [ ] Create `.env.production` with database credentials
- [ ] Create `docker-compose.aws.yml` override file
- [ ] Build and start containers
- [ ] Verify API health endpoint
- [ ] Test worker job processing

### Production Readiness

- [ ] Setup systemd service for auto-start
- [ ] Configure Nginx reverse proxy
- [ ] Setup Let's Encrypt SSL (if using domain)
- [ ] Configure log rotation
- [ ] Setup CloudWatch monitoring (optional)
- [ ] Create EBS snapshot schedule
- [ ] Document recovery procedures

### Testing

- [ ] API endpoints return expected responses
- [ ] Workers process jobs successfully
- [ ] Database connections are stable
- [ ] Redis caching works correctly
- [ ] SSL certificate is valid (if configured)
- [ ] Server restarts recover gracefully

---

## Monitoring and Maintenance

### Metrics to Track

**Application Metrics:**

- Request rate (req/min)
- Response time (p50, p95, p99)
- Error rate (4xx, 5xx)
- Worker job success/failure rate
- Queue depth (Redis)

**System Metrics:**

- CPU utilization
- Memory usage
- Disk I/O
- Network throughput
- Database connection pool usage

### Monitoring Tools

**Free Options:**

- FastAPI built-in `/health` endpoint
- Docker stats (`docker stats`)
- CloudWatch basic monitoring (5-minute granularity, free)
- Uptime monitoring (UptimeRobot, free tier)

**Paid Options (when needed):**

- CloudWatch detailed monitoring ($2.10/month per instance)
- Prometheus + Grafana (self-hosted on EC2)
- Datadog, New Relic ($$$ - wait until scaling)

### Maintenance Tasks

**Weekly:**

- Review application logs for errors
- Check disk space usage
- Verify backup completion

**Monthly:**

- Security updates: `apt update && apt upgrade`
- Review cost reports in AWS Console
- Rotate old EBS snapshots
- Check SSL certificate expiry (if applicable)

**Quarterly:**

- Review and optimize resource sizing
- Evaluate migration to ECS if traffic increased
- Update dependencies in containers

---

## Risk Assessment

### High Risk (Mitigate Before Production)

**Single Point of Failure:**

- **Risk:** Single EC2 instance - if it fails, service is down
- **Mitigation:**
  - Regular EBS snapshots for quick recovery
  - Document recovery procedure (launch new instance, attach EBS, restore)
  - Consider ECS Fargate when high availability is critical

**Database Connection Limits:**

- **Risk:** External databases may have connection limits (Neon free tier: limited)
- **Mitigation:**
  - Monitor connection pool usage
  - Upgrade to paid tier if needed
  - Implement connection pooling correctly (already in place)

### Medium Risk (Monitor)

**Resource Exhaustion:**

- **Risk:** 2GB RAM may be insufficient for heavy compute jobs
- **Mitigation:**
  - Monitor memory usage
  - Upgrade to t3a.medium (4GB) if needed (+$10/month)
  - Implement job queue limits (already configured: max 10 concurrent)

**Spot Database Auto-Pause:**

- **Risk:** Neon free tier auto-pauses, causing cold start latency
- **Mitigation:**
  - Upgrade to paid tier for production ($19/month)
  - Or use RDS t4g.micro for always-on ($12/month)

### Low Risk (Accept)

**Scaling Limitations:**

- **Risk:** Can't auto-scale beyond single instance
- **Accept:** MVP traffic doesn't require it
- **Future:** Migrate to ECS Fargate when needed

**Geographic Redundancy:**

- **Risk:** Single AWS region
- **Accept:** Not critical for MVP
- **Future:** Multi-region when user base grows

---

## Decision Summary

### Chosen Architecture: EC2 + Docker Compose

**Why:**

1. **Budget:** $20-50/month (well under $200 limit)
2. **Simplicity:** Leverage existing Docker expertise
3. **Speed:** Deploy in ~2 hours
4. **Flexibility:** Easy migration to ECS later

**Trade-offs Accepted:**

- No auto-scaling (manual intervention required)
- Single point of failure (mitigated with backups)
- Manual server maintenance (acceptable for MVP)

**When to Re-evaluate:**

- Traffic exceeds 500 req/min consistently
- High availability becomes critical
- Team size grows (multiple developers deploying)
- Budget increases to $200+/month

---

## Next Steps

1. **Review this specification** with stakeholders
2. **Provision external databases** (Neon + Upstash)
3. **Create deployment scripts** (user-data, systemd, nginx config)
4. **Test locally** with external DB connections
5. **Launch EC2 instance** and deploy
6. **Document operational procedures** in runbooks

---

## References

- [AWS EC2 Pricing](https://aws.amazon.com/ec2/pricing/)
- [Neon PostgreSQL Documentation](https://neon.tech/docs)
- [Upstash Redis Documentation](https://upstash.com/docs/redis)
- [FastAPI Deployment Guide](https://fastapi.tiangolo.com/deployment/)
- [Docker Compose Documentation](https://docs.docker.com/compose/)

---

**Document Owner:** DevOps Team
**Review Cadence:** Quarterly or when traffic patterns change
**Last Updated:** 2025-11-01
