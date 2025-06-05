# Hybrid FastAPI + GraphQL Architecture Implementation Plan

## Executive Summary

<summary>
<objective>Design a hybrid architecture that leverages GraphQL for data operations while preserving FastAPI for file serving, streaming, and infrastructure concerns</objective>
<approach>Clear separation of responsibilities with shared infrastructure and gradual migration strategy</approach>
<value>Maintain 100% existing functionality while gaining GraphQL's type safety, introspection, and query flexibility</value>
</summary>

## Architecture Design

### Current State Analysis

- **Mature GraphQL Foundation**: Comprehensive Strawberry GraphQL schema with 20+ types, queries, mutations
- **Rich FastAPI Ecosystem**: 47 REST endpoints across 5 functional areas with advanced middleware
- **Critical Dependencies**: SSE streaming, static file serving, health monitoring require FastAPI
- **Shared Infrastructure**: Database (Prisma), DI container, authentication, monitoring already integrated

### Target State Architecture

```
┌─── GraphQL API Layer (/graphql) ─────────────────────────┐
│  ├─ Data Operations (Primary Interface)                  │
│  │  ├─ Portfolio CRUD & Analytics                       │
│  │  ├─ Strategy Management & Backtesting                │
│  │  ├─ Market Data Queries                              │
│  │  └─ Real-time Subscriptions (NEW)                    │
│  │                                                       │
│  ├─ Advanced Features                                    │
│  │  ├─ Field-level permissions                          │
│  │  ├─ Query complexity analysis                        │
│  │  ├─ DataLoader batching                              │
│  │  └─ Schema Federation (future)                       │
│  └─ Development Tools                                    │
│     ├─ GraphiQL Interface                               │
│     ├─ Schema introspection                             │
│     └─ Query playground                                 │
└─────────────────────────────────────────────────────────┘

┌─── FastAPI Infrastructure Layer (/api) ─────────────────┐
│  ├─ Infrastructure Services (Core Platform)             │
│  │  ├─ Health checks & monitoring                      │
│  │  ├─ Metrics & observability                         │
│  │  ├─ Service orchestration                           │
│  │  └─ Container management                             │
│  │                                                      │
│  ├─ Streaming & Real-time                               │
│  │  ├─ Server-Sent Events                              │
│  │  ├─ File streaming                                   │
│  │  └─ Progress tracking                                │
│  │                                                      │
│  ├─ File Operations                                      │
│  │  ├─ Static file serving                             │
│  │  ├─ File uploads/downloads                          │
│  │  ├─ CSV/JSON data export                            │
│  │  └─ Frontend application hosting                     │
│  │                                                      │
│  └─ Legacy REST Support (Transition)                    │
│     ├─ Script execution endpoints                       │
│     ├─ Operation management                             │
│     └─ Cache management                                 │
└─────────────────────────────────────────────────────────┘

┌─── Shared Infrastructure Layer ─────────────────────────┐
│  ├─ Authentication & Authorization                       │
│  │  ├─ JWT token validation                            │
│  │  ├─ API key management                               │
│  │  ├─ Role-based permissions                          │
│  │  └─ Rate limiting policies                          │
│  │                                                      │
│  ├─ Data & Business Logic                               │
│  │  ├─ Prisma ORM & Database                           │
│  │  ├─ Service layer (MA Cross, Portfolio, etc.)       │
│  │  ├─ Redis caching                                   │
│  │  └─ Event bus communication                         │
│  │                                                      │
│  ├─ Cross-cutting Concerns                              │
│  │  ├─ Dependency injection container                  │
│  │  ├─ Structured logging                              │
│  │  ├─ Error handling & recovery                       │
│  │  ├─ Configuration management                        │
│  │  └─ Performance monitoring                          │
│  │                                                      │
│  └─ External Integrations                               │
│     ├─ Market data providers                           │
│     ├─ Trading APIs                                     │
│     └─ Third-party services                            │
└─────────────────────────────────────────────────────────┘
```

### Responsibility Matrix

| Feature Category      | GraphQL          | FastAPI           | Shared          |
| --------------------- | ---------------- | ----------------- | --------------- |
| **Data Queries**      | ✅ Primary       | ⚠️ Legacy         | Database, Cache |
| **Real-time Updates** | ✅ Subscriptions | ✅ SSE            | Event Bus       |
| **File Operations**   | ❌               | ✅ Required       | Storage         |
| **Authentication**    | ✅ Context       | ✅ Middleware     | JWT, Sessions   |
| **Health Monitoring** | ⚠️ Basic         | ✅ Comprehensive  | Metrics         |
| **Frontend Apps**     | ❌               | ✅ Static Serving | Assets          |
| **API Documentation** | ✅ Introspection | ✅ OpenAPI        | Standards       |

## Implementation Phases

### Phase 1: Enhance GraphQL Infrastructure

**Estimated Effort**: 3 days
**Objective**: Add subscriptions, authentication, and performance optimizations to existing GraphQL implementation
**Scope**: WebSocket subscriptions, DataLoader batching, JWT authentication, query complexity analysis
**Dependencies**: Current GraphQL schema and monitoring setup

**Implementation Steps**:

1. Add WebSocket subscription support for real-time updates
2. Implement DataLoader pattern for N+1 query optimization
3. Complete JWT authentication integration in GraphQL context
4. Add query complexity analysis and field-level permissions

**Validation**: Test subscription functionality and performance benchmarks
**Rollback**: GraphQL changes are additive; FastAPI remains primary

**Deliverables**:

- Real-time GraphQL subscriptions for analysis progress → Acceptance: SSE functionality replicated via WebSocket
- Authenticated GraphQL context with user permissions → Acceptance: User-specific data access working
- Performance-optimized resolvers with batching → Acceptance: N+1 queries eliminated, <100ms response times

**Risks**:

- WebSocket complexity → Start with simple subscriptions, add features incrementally
- Authentication integration issues → Use existing JWT middleware patterns

### Phase 2: Create Hybrid Routing Strategy

**Estimated Effort**: 2 days
**Objective**: Implement intelligent request routing and API versioning for seamless client migration
**Scope**: API gateway pattern, GraphQL/REST compatibility layer, versioning, migration utilities
**Dependencies**: Enhanced GraphQL infrastructure from Phase 1

**Implementation Steps**:

1. Create API gateway pattern with intelligent routing
2. Implement GraphQL/REST compatibility layer
3. Add API versioning headers and deprecation notices
4. Create migration utilities for client applications

**Validation**: Test routing logic and client compatibility
**Rollback**: Remove routing layer, revert to direct FastAPI handling

**Deliverables**:

- Intelligent API routing based on client preferences → Acceptance: Automatic GraphQL/REST routing working
- Version-aware API with deprecation support → Acceptance: Clean migration path for clients
- Client migration toolkit and documentation → Acceptance: Clear upgrade path documented

**Risks**:

- Routing complexity affecting performance → Profile and optimize critical paths
- Client breaking changes → Maintain 100% backward compatibility during transition

### Phase 3: Strategic Endpoint Migration

**Estimated Effort**: 4 days
**Objective**: Migrate high-value, low-risk endpoints to GraphQL while preserving FastAPI for infrastructure
**Scope**: Portfolio/strategy queries, configuration mutations, analysis subscriptions, preserve file operations
**Dependencies**: Hybrid routing infrastructure from Phase 2

**Implementation Steps**:

1. Migrate portfolio and strategy queries to GraphQL-first
2. Add GraphQL mutations for configuration management
3. Implement GraphQL subscriptions for analysis status
4. Preserve FastAPI for file operations and health checks

**Validation**: End-to-end testing of migrated functionality
**Rollback**: Revert to FastAPI endpoints via routing configuration

**Deliverables**:

- Portfolio operations via GraphQL → Acceptance: Feature parity with REST endpoints
- Real-time analysis updates via subscriptions → Acceptance: SSE functionality maintained via WebSocket
- Preserved file serving and static hosting → Acceptance: All frontend apps function normally

**Risks**:

- Feature parity gaps → Comprehensive testing against existing REST functionality
- Performance regression → Benchmark and optimize GraphQL resolvers

### Phase 4: Production Optimization & Monitoring

**Estimated Effort**: 2 days
**Objective**: Add production-ready features including caching, monitoring, and performance optimization
**Scope**: Query caching, persisted queries, comprehensive metrics, database optimization, deployment config
**Dependencies**: Migrated endpoints from Phase 3

**Implementation Steps**:

1. Implement GraphQL query caching and persisted queries
2. Add comprehensive GraphQL metrics to existing monitoring
3. Optimize database queries with connection pooling
4. Create production deployment configuration

**Validation**: Load testing and production readiness assessment
**Rollback**: Disable optimizations, revert to basic GraphQL setup

**Deliverables**:

- Production-ready GraphQL caching → Acceptance: Query performance improved by 40%+
- Comprehensive monitoring dashboard → Acceptance: GraphQL metrics integrated with existing systems
- Load-tested hybrid architecture → Acceptance: Handles current traffic with headroom

**Risks**:

- Cache invalidation complexity → Use proven cache invalidation strategies
- Monitoring overhead → Ensure monitoring doesn't impact performance

## Architecture Implementation Details

### 1. Enhanced GraphQL Layer

```python
# /app/api/graphql/enhanced_schema.py
import strawberry
from strawberry.extensions import QueryDepthLimiter, ValidationCache
from strawberry.subscriptions import GRAPHQL_TRANSPORT_WS_PROTOCOL

@strawberry.type
class Subscription:
    @strawberry.subscription
    async def analysis_progress(self, analysis_id: str) -> AsyncIterator[AnalysisProgress]:
        """Real-time analysis progress via WebSocket subscription"""
        async for progress in analysis_service.stream_progress(analysis_id):
            yield progress

    @strawberry.subscription
    async def portfolio_updates(self, portfolio_id: str) -> AsyncIterator[Portfolio]:
        """Real-time portfolio value updates"""
        async for update in portfolio_service.stream_updates(portfolio_id):
            yield update

# Enhanced schema with production extensions
schema = strawberry.Schema(
    query=Query,
    mutation=Mutation,
    subscription=Subscription,
    extensions=[
        QueryDepthLimiter(max_depth=10),
        ValidationCache(),
        GraphQLMonitoringExtension(),
        DataLoaderExtension(),
    ]
)
```

### 2. Intelligent API Gateway

```python
# /app/api/gateway/router.py
from fastapi import Request, Response
from fastapi.routing import APIRoute

class HybridAPIGateway:
    """Intelligent routing between GraphQL and REST endpoints"""

    def __init__(self):
        self.graphql_endpoints = {
            "portfolios", "strategies", "tickers", "analysis"
        }
        self.fastapi_required = {
            "health", "files", "stream", "static", "viewer", "sensylate"
        }

    async def route_request(self, request: Request) -> Response:
        """Route requests based on capabilities and client preferences"""

        # Always use FastAPI for infrastructure
        if any(path in request.url.path for path in self.fastapi_required):
            return await self.fastapi_handler(request)

        # Check client GraphQL capability
        accepts_graphql = "application/graphql" in request.headers.get("accept", "")
        has_graphql_header = request.headers.get("x-prefer-graphql") == "true"

        # Route data operations to GraphQL if supported
        if (accepts_graphql or has_graphql_header) and
           any(endpoint in request.url.path for endpoint in self.graphql_endpoints):
            return await self.graphql_handler(request)

        # Default to FastAPI
        return await self.fastapi_handler(request)
```

### 3. Enhanced Context and Authentication

```python
# /app/api/graphql/enhanced_context.py
from strawberry.fastapi import BaseContext
from strawberry.types import Info
from typing import Optional

@strawberry.type
class GraphQLContext(BaseContext):
    """Enhanced GraphQL context with full authentication and permissions"""

    def __init__(self, request, response, user=None):
        super().__init__(request, response)
        self.user = user
        self.permissions = UserPermissions(user) if user else None
        self.dataloaders = create_dataloaders()

    @property
    def is_authenticated(self) -> bool:
        return self.user is not None

    def require_permission(self, permission: str) -> None:
        if not self.permissions or not self.permissions.has(permission):
            raise AuthorizationError(f"Permission '{permission}' required")

async def get_enhanced_graphql_context(request, response) -> GraphQLContext:
    """Create enhanced context with authentication and DataLoaders"""
    user = await authenticate_jwt_token(request)
    return GraphQLContext(request, response, user)
```

### 4. DataLoader Implementation

```python
# /app/api/graphql/dataloaders.py
from strawberry.dataloader import DataLoader
from typing import List, Optional

class PortfolioDataLoader:
    """Batch portfolio queries to prevent N+1 problems"""

    @staticmethod
    async def load_portfolios(portfolio_ids: List[str]) -> List[Optional[Portfolio]]:
        portfolios = await portfolio_service.get_portfolios_by_ids(portfolio_ids)
        return [portfolios.get(pid) for pid in portfolio_ids]

    @staticmethod
    async def load_strategies(strategy_ids: List[str]) -> List[Optional[Strategy]]:
        strategies = await strategy_service.get_strategies_by_ids(strategy_ids)
        return [strategies.get(sid) for sid in strategy_ids]

def create_dataloaders() -> dict:
    """Create DataLoader instances for the request context"""
    return {
        "portfolios": DataLoader(load_fn=PortfolioDataLoader.load_portfolios),
        "strategies": DataLoader(load_fn=PortfolioDataLoader.load_strategies),
        "price_data": DataLoader(load_fn=MarketDataLoader.load_price_data),
    }
```

### 5. Production Configuration

```python
# /app/api/hybrid_main.py
from fastapi import FastAPI
from strawberry.fastapi import GraphQLRouter
from strawberry.subscriptions import GRAPHQL_TRANSPORT_WS_PROTOCOL

def create_hybrid_app() -> FastAPI:
    """Create production-ready hybrid FastAPI + GraphQL application"""

    app = FastAPI(
        title="Trading Platform Hybrid API",
        version="2.0.0",
        docs_url="/api/docs",  # Keep REST docs separate
    )

    # GraphQL with WebSocket subscriptions
    graphql_app = GraphQLRouter(
        schema,
        graphiql=settings.DEVELOPMENT,
        context_getter=get_enhanced_graphql_context,
        subscription_protocols=[GRAPHQL_TRANSPORT_WS_PROTOCOL],
    )

    # Mount GraphQL
    app.include_router(graphql_app, prefix="/graphql", tags=["graphql"])

    # Mount FastAPI infrastructure
    app.include_router(health_router, prefix="/health", tags=["infrastructure"])
    app.include_router(files_router, prefix="/api/data", tags=["files"])
    app.include_router(stream_router, prefix="/api", tags=["streaming"])

    # Add hybrid gateway middleware
    app.add_middleware(HybridAPIGateway)

    # Static file serving for frontend apps
    app.mount("/viewer", StaticFiles(directory="app/frontend/csv_viewer"))
    app.mount("/sensylate", StaticFiles(directory="app/frontend/sensylate/dist"))

    return app
```

## Migration Strategy

### Client Migration Path

1. **Phase 1: Dual Support** - Clients can use either REST or GraphQL
2. **Phase 2: GraphQL Preferred** - New features only in GraphQL
3. **Phase 3: REST Deprecated** - Clear deprecation timeline
4. **Phase 4: REST Legacy** - Critical infrastructure only

### Backward Compatibility

- **100% REST Functionality Preserved** during migration
- **API Versioning** with clear deprecation notices
- **Client Detection** for automatic routing
- **Migration Tools** for easy client updates

## FastAPI Features Analysis

### Critical Features That Cannot Be Migrated to Pure GraphQL

#### Server-Sent Events (SSE) - BREAKING

```
/api/scripts/status-stream/{execution_id}
/api/ma-cross/stream/{execution_id}
```

- **Purpose**: Real-time progress updates for long-running analysis
- **Impact**: GraphQL has no SSE support; requires WebSocket subscriptions
- **Frontend Dependencies**: Both CSV viewer and analysis components rely on these

#### Static File Serving - BREAKING

```
/viewer/          # CSV viewer HTML app
/sensylate/       # React PWA with static assets
/api/data/csv/    # CSV file downloads
/api/data/json/   # JSON file downloads
```

- **Impact**: GraphQL serves only JSON; needs separate HTTP server
- **Dependencies**: Two complete frontend applications

#### HTTP-Specific Features - MAJOR ADAPTATION

**Custom Status Codes**:

- `202 Accepted` for async operations
- `429 Too Many Requests` for rate limiting
- `503 Service Unavailable` for health checks
- `204 No Content` for specific responses

**Response Types**:

- `StreamingResponse` for SSE
- `HTMLResponse` for frontend apps
- `FileResponse` for downloads
- `RedirectResponse` for routing

### REST Endpoints by Functional Area

#### Operational Management (15 endpoints)

```
GET  /api/versions                    # API versioning
GET  /api/migration/{from}/{to}       # Migration guides
POST /api/services/initialize         # Service startup
GET  /api/operations/metrics          # Operation monitoring
POST /api/operations/data-analysis    # Background tasks
```

#### Health & Monitoring (8 endpoints)

```
GET /health/live                      # Kubernetes probes
GET /health/ready                     # Readiness checks
GET /health/detailed                  # Comprehensive status
GET /health/metrics                   # Prometheus metrics
```

#### Script Execution (5 endpoints)

```
POST /api/scripts/execute             # Python script execution
GET  /api/scripts/status/{id}         # Status polling
GET  /api/scripts/status-stream/{id}  # SSE streaming ⚠️
GET  /api/scripts/list                # Script inventory
```

#### MA Cross Analysis (13 endpoints)

```
POST /api/ma-cross/analyze            # Portfolio analysis
GET  /api/ma-cross/stream/{id}        # SSE streaming ⚠️
GET  /api/ma-cross/config-presets     # Configuration
POST /api/ma-cross/cache/invalidate   # Cache management
GET  /api/ma-cross/rate-limit/stats   # Performance monitoring
```

#### Data Access (6 endpoints)

```
GET /api/data/csv/{path}              # File downloads ⚠️
GET /api/data/json/{path}             # File downloads ⚠️
GET /api/data/ticker-lists            # Data catalogs
GET /api/data/list/{directory}        # Directory listing
```

### Advanced FastAPI Features in Use

#### Middleware Stack

- `RateLimitMiddleware` - Per-IP/endpoint rate limiting
- `SecurityHeadersMiddleware` - HSTS, CSP, CSRF protection
- `APIKeyMiddleware` - Authentication layer
- `RequestValidationMiddleware` - Content validation
- `CORSMiddleware` - Cross-origin configuration

#### Dependency Injection System

- Complex DI container with health monitoring
- Service orchestrator pattern
- Enhanced dependency configuration
- Request-scoped services

#### Performance & Monitoring

- Per-endpoint rate limiting policies
- Request timing and metrics collection
- Cache invalidation strategies
- Background operation management

## Implementation Benefits

### Immediate Gains

- **Type Safety**: GraphQL schema provides compile-time validation
- **Developer Experience**: GraphiQL, introspection, and better tooling
- **Performance**: DataLoader batching eliminates N+1 queries
- **Flexibility**: Clients request exactly the data they need

### Strategic Advantages

- **Zero Disruption**: All existing functionality preserved
- **Gradual Migration**: Low-risk, incremental adoption
- **Future-Proof**: Modern API standards with room for growth
- **Operational Excellence**: Enhanced monitoring and observability

### Technical Excellence

- **Clean Architecture**: Clear separation of concerns
- **Performance Optimized**: Caching, batching, and connection pooling
- **Production Ready**: Comprehensive monitoring and error handling
- **Scalable Design**: Federation-ready for microservices evolution

## Implementation Tracking

_This section will be updated after each phase completion with detailed summaries, accomplishments, files changed, validation results, issues & resolutions, and insights gained._

---

The hybrid architecture preserves your entire existing ecosystem while providing a clear path to modern GraphQL capabilities. Each phase delivers independent value and can be deployed safely without breaking changes.
