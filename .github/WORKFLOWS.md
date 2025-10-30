# GitHub Actions Workflows Documentation

## 📊 Workflow Status Badges

Add these to your main README.md:

```markdown
## CI/CD Status

[![CI/CD Pipeline](https://github.com/colemorton/trading/actions/workflows/ci-cd.yml/badge.svg)](https://github.com/colemorton/trading/actions/workflows/ci-cd.yml)
[![Security Scanning](https://github.com/colemorton/trading/actions/workflows/security.yml/badge.svg)](https://github.com/colemorton/trading/actions/workflows/security.yml)
[![Nightly Tests](https://github.com/colemorton/trading/actions/workflows/nightly.yml/badge.svg)](https://github.com/colemorton/trading/actions/workflows/nightly.yml)
```

---

## 🔄 Available Workflows

### 1. **CI/CD Pipeline** (`ci-cd.yml`)

**Triggers:**

- Push to `main` or `develop` branches
- Pull requests to `main`
- Manual dispatch

**Jobs:**

1. **Lint** - Code quality checks (Ruff, mypy, Bandit)
2. **Test Backend** - Unit and integration tests (parallelized)
3. **Test Performance** - Performance benchmarks
4. **Build** - Docker image builds with caching
5. **E2E Test** - End-to-end integration tests
6. **CI Summary** - Consolidated pipeline results

**Features:**

- ✅ Composite action for Python/Poetry setup with intelligent caching
- ✅ Matrix parallelization for faster test execution
- ✅ PostgreSQL and Redis service containers
- ✅ Codecov integration for coverage tracking
- ✅ GitHub Step Summaries for quick results overview
- ✅ Artifact retention (test results: 30 days, performance: 90 days)

**Performance Optimizations:**

- Cached Poetry dependencies (per Python version + lock file hash)
- Docker BuildKit with GitHub Actions cache
- Parallel test execution with pytest-xdist (`-n auto`)
- Matrix strategy for test groups (unit/integration)

---

### 2. **Security Scanning** (`security.yml`)

**Triggers:**

- Push to `main` or `develop` branches
- Pull requests to `main`
- Daily schedule (3 AM UTC)
- Manual dispatch

**Jobs:**

1. **CodeQL Analysis** - SAST for Python
2. **Dependency Scan** - Safety check for vulnerable packages
3. **Container Scan** - Trivy for Docker image vulnerabilities
4. **Secret Scan** - Gitleaks for exposed secrets
5. **Bandit Scan** - Python security linting
6. **Security Summary** - Consolidated security results

**Features:**

- ✅ Automated vulnerability detection (CRITICAL, HIGH, MEDIUM)
- ✅ SARIF uploads to GitHub Security tab
- ✅ Daily scheduled scans for proactive security
- ✅ Non-blocking scans (report but don't fail builds)

**Scanned Components:**

- Python dependencies (via Safety)
- Docker base images and layers (via Trivy)
- Source code (via CodeQL & Bandit)
- Git history (via Gitleaks)

---

### 3. **Dependabot** (`dependabot.yml`)

**Schedule:**

- Python dependencies: Weekly (Mondays 6 AM)
- GitHub Actions: Monthly
- Docker base images: Weekly

**Features:**

- ✅ Automated dependency updates
- ✅ Grouped dev dependencies
- ✅ Semantic versioning awareness
- ✅ Automatic PR creation with labels

**Configuration:**

- Open PR limit: 10 (Python), 5 (Actions), 3 (Docker)
- Ignores major version updates for stable packages (numpy, pandas)
- Automatic assignment to `colemorton`

---

### 4. **Deploy to Staging** (`deploy-staging.yml`)

**Triggers:**

- Push to `develop` branch
- Manual dispatch (with optional image tag)

**Features:**

- ✅ Automated deployment from develop branch
- ✅ Health checks with configurable timeout (300s)
- ✅ Smoke tests after deployment
- ✅ Automatic rollback on failure
- ✅ Deployment summaries with status

**Safety Checks:**

- Health check endpoint validation
- Smoke test execution
- Rollback on any failure

---

### 5. **Deploy to Production** (`deploy-production.yml`)

**Triggers:**

- Manual dispatch only (requires approval)

**Features:**

- ✅ Pre-deployment validation checks
- ✅ Blue-green deployment strategy
- ✅ Staging health verification before production deploy
- ✅ 5-minute monitoring period after traffic switch
- ✅ Automatic rollback on failure
- ✅ Configuration backup before deployment

**Blue-Green Deployment Flow:**

1. Deploy new version to "green" environment
2. Health check green environment
3. Run smoke tests on green
4. Switch traffic from blue to green
5. Monitor for 5 minutes
6. Decommission old blue environment

**Safety Checks:**

- Image verification
- Staging health check
- Configuration validation
- Green environment health checks
- Smoke tests (optional skip)
- Post-deployment monitoring

---

### 6. **Emergency Rollback** (`rollback.yml`)

**Triggers:**

- Manual dispatch only

**Inputs:**

- `environment`: staging or production
- `previous_image_tag`: Target version (optional, uses last stable if empty)
- `reason`: Required rollback justification

**Features:**

- ✅ Quick rollback to previous known good version
- ✅ Pre-rollback snapshot creation
- ✅ Health check after rollback
- ✅ Smoke test verification
- ✅ Incident documentation in summary

**Safety Checks:**

- Verify rollback target exists
- Create pre-rollback snapshot
- Health checks after rollback
- Smoke tests execution

---

### 7. **Nightly Regression & Performance Tests** (`nightly.yml`)

**Triggers:**

- Daily schedule (2 AM UTC)
- Manual dispatch

**Jobs:**

1. **Regression Tests** - All regression markers
2. **Performance Baseline** - Benchmark tracking
3. **Stress Tests** - Load and stress testing
4. **Memory Leak Detection** - Memory profiling
5. **Nightly Summary** - Consolidated results

**Features:**

- ✅ Long-running test suites that don't block PRs
- ✅ Performance baseline tracking (365-day retention)
- ✅ Stress and memory leak detection
- ✅ Failure notifications

---

### 8. **MA Cross Module Tests** (`ma_cross_tests.yml`)

**Triggers:**

- Path-based: Changes to `app/ma_cross/**`, `app/tools/**`, `tests/**`
- Daily schedule (2 AM UTC)
- Manual dispatch with test suite selection

**Features:**

- ✅ Module-specific test isolation
- ✅ Matrix strategy for test suites (unit, integration, e2e, regression)
- ✅ Path-based triggering to avoid unnecessary runs
- ✅ Comprehensive test summary generation

---

### 9. **Concurrency Module Tests** (`concurrency_tests.yml`)

**Triggers:**

- Path-based: Changes to `app/concurrency/**`, `tests/concurrency/**`

**Features:**

- ✅ Dedicated concurrency testing
- ✅ Unit, integration, error handling, and performance tests
- ✅ PR comments with performance results
- ✅ Coverage analysis and reporting

---

## 🛠️ Composite Actions

### `setup-python-poetry` (`.github/actions/setup-python-poetry/action.yml`)

Reusable composite action for Python + Poetry + dependency setup.

**Inputs:**

- `python-version`: Python version (default: 3.11)
- `poetry-version`: Poetry version (default: 1.8.3)
- `install-dependencies`: Whether to install deps (default: true)
- `dependency-groups`: Groups to install (main/dev/all)
- `cache-key-suffix`: Additional cache key suffix

**Outputs:**

- `cache-hit`: Whether cache was hit
- `python-version`: Python version installed

**Caching Strategy:**

- Poetry installation cached by version + OS
- Dependencies cached by Python version + lock file hash + groups
- Automatic restore with fallback keys

---

## 📈 Performance Metrics

**Expected CI/CD Performance:**

- Lint job: ~2-3 minutes (with cache hit)
- Test Backend (each matrix): ~5-8 minutes
- Performance tests: ~10-15 minutes
- Docker build: ~3-5 minutes (with cache)
- E2E tests: ~8-12 minutes
- **Total pipeline time**: ~15-20 minutes (parallelized)

**Cache Hit Rates:**

- Poetry dependencies: >90% on subsequent runs
- Docker layers: >80% with unchanged dependencies
- Performance improvement: ~50% faster with cache hits

---

## 🔐 Required Secrets

### Repository Secrets:

- `CODECOV_TOKEN` - Codecov integration (optional)
- `SLACK_WEBHOOK` - Slack notifications (optional)

### Environment Secrets:

**Staging:**

- (Add staging-specific secrets as needed)

**Production:**

- (Add production-specific secrets as needed)

---

## 📋 Best Practices

### For Contributors:

1. **Local Testing**

   ```bash
   # Run linters before pushing
   poetry run ruff format . && poetry run ruff check .

   # Run tests locally
   poetry run pytest tests/ -v -m "unit or integration"
   ```

2. **Pull Requests**

   - All checks must pass before merge
   - Codecov comment will show coverage changes
   - Security scans run automatically

3. **Deployment**
   - Staging auto-deploys from `develop`
   - Production requires manual approval
   - Always test in staging first

### For Maintainers:

1. **Monitoring**

   - Check GitHub Security tab daily
   - Review Dependabot PRs weekly
   - Monitor nightly test results

2. **Deployment Strategy**

   - Use blue-green for production
   - Always verify staging health before production
   - Keep rollback workflow ready for emergencies

3. **Performance Tracking**
   - Review performance baseline trends monthly
   - Investigate regression test failures promptly
   - Track artifact storage usage

---

## 🚨 Troubleshooting

### Common Issues:

**1. Cache Miss on Dependencies**

- Check if `poetry.lock` changed
- Verify cache key matches in workflow

**2. Test Failures**

- Check test logs in artifacts
- Run locally with same Python version
- Verify service containers are healthy

**3. Deployment Failures**

- Check health endpoint accessibility
- Verify environment secrets are set
- Review deployment logs in artifacts

**4. Security Scan Failures**

- Review GitHub Security tab for details
- Update dependencies if vulnerabilities found
- Check SARIF uploads for detailed reports

---

## 📚 Additional Resources

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Poetry Documentation](https://python-poetry.org/docs/)
- [Pytest Documentation](https://docs.pytest.org/)
- [Docker BuildKit](https://docs.docker.com/build/buildkit/)
- [Trivy Security Scanner](https://trivy.dev/)
- [CodeQL](https://codeql.github.com/)

---

**Last Updated**: 2025-10-30
**Maintained By**: @colemorton
