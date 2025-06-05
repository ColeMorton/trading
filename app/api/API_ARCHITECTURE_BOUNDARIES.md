# API Architecture Boundaries

This document defines clear service boundaries between REST and GraphQL APIs in the unified trading platform architecture, eliminating overlap and establishing consistent patterns.

## Architecture Overview

### Service Separation Principles

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   REST API      │    │   GraphQL API   │    │  Static Assets  │
│   (Operations)  │    │   (Data Query)  │    │   (Frontend)    │
├─────────────────┤    ├─────────────────┤    ├─────────────────┤
│ • Execution     │    │ • Complex       │    │ • CSV Viewer    │
│ • Control       │    │   Queries       │    │ • Sensylate     │
│ • Monitoring    │    │ • Relationships │    │ • Documentation │
│ • Admin         │    │ • Aggregations  │    │ • Assets        │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## REST API Responsibilities

### Primary Use Cases

- **Strategy Execution**: Trigger and control strategy runs
- **System Operations**: Health checks, monitoring, lifecycle management
- **File Operations**: Direct file access, uploads, downloads
- **Administrative Tasks**: Configuration, user management, system control

### Endpoint Categories

#### 1. Execution Control (`/api/v1/scripts`, `/api/v1/ma-cross`)

```
POST /api/v1/scripts/execute          # Execute trading scripts
GET  /api/v1/scripts/status/{id}      # Check execution status
GET  /api/v1/scripts/stream/{id}      # Real-time execution stream (SSE)
POST /api/v1/ma-cross/analyze         # Execute MA Cross analysis
POST /api/v1/ma-cross/optimize        # Parameter optimization
```

#### 2. System Monitoring (`/api/v1/health`, `/api/performance`)

```
GET  /api/v1/health                   # System health status
GET  /api/performance/metrics         # Performance metrics
GET  /api/performance/dashboard       # Performance dashboard
POST /api/performance/alerts          # Configure alerts
```

#### 3. Data Access (`/api/v1/data`)

```
GET  /api/v1/data/csv/{path}          # Direct CSV file access
GET  /api/v1/data/json/{path}         # Direct JSON file access
POST /api/v1/data/upload              # File uploads
```

#### 4. Administrative (`/api/admin`, `/api/services`)

```
GET  /api/services/health             # Service health checks
POST /api/services/initialize         # Initialize services
POST /api/services/shutdown           # Shutdown services
GET  /api/container/registrations     # Dependency container info
```

## GraphQL API Responsibilities

### Primary Use Cases

- **Complex Data Queries**: Multi-table joins, nested relationships
- **Data Aggregation**: Portfolio metrics, performance analytics
- **Real-time Subscriptions**: Live data updates
- **Flexible Client Queries**: Allow clients to specify exact data needs

### Schema Organization

#### 1. Query Operations (`/graphql`)

```graphql
type Query {
  # Portfolio Operations
  portfolios(filter: PortfolioFilter): [Portfolio!]!
  portfolio(id: ID!): Portfolio
  portfolioMetrics(portfolioIds: [ID!]!): [PortfolioMetrics!]!

  # Strategy Operations
  strategies(type: StrategyType): [Strategy!]!
  strategy(id: ID!): Strategy
  backtestResults(strategyId: ID!, timeRange: TimeRange): [BacktestResult!]!
  signals(ticker: String!, strategy: String!, timeRange: TimeRange): [Signal!]!

  # Market Data
  tickers(exchange: String, sector: String): [Ticker!]!
  ticker(symbol: String!): Ticker
  priceData(
    symbol: String!
    timeframe: Timeframe!
    range: DateRange
  ): [PriceBar!]!
  availableTimeframes: [Timeframe!]!
}
```

#### 2. Mutation Operations (`/graphql`)

```graphql
type Mutation {
  # Portfolio Management
  createPortfolio(input: CreatePortfolioInput!): Portfolio!
  updatePortfolio(id: ID!, input: UpdatePortfolioInput!): Portfolio
  deletePortfolio(id: ID!): Boolean!

  # Strategy Configuration
  createStrategy(input: CreateStrategyInput!): Strategy!
  updateStrategy(id: ID!, input: UpdateStrategyInput!): Strategy
  deleteStrategy(id: ID!): Boolean!

  # Analysis Operations (Async)
  executeAnalysis(input: AnalysisInput!): AnalysisResponse!
  cancelAnalysis(analysisId: ID!): Boolean!
}
```

#### 3. Subscription Operations (`/graphql`)

```graphql
type Subscription {
  # Real-time updates
  portfolioUpdates(portfolioId: ID!): Portfolio!
  analysisProgress(analysisId: ID!): AnalysisProgress!
  systemHealth: SystemHealth!
  performanceMetrics: PerformanceMetrics!
}
```

## Clear Boundary Rules

### REST API Boundaries

1. **Operation-Focused**: Use REST for actions that change system state
2. **Simple Queries**: Use REST for straightforward, single-resource queries
3. **File Operations**: All file uploads/downloads go through REST
4. **System Control**: All administrative and monitoring operations via REST
5. **Streaming**: Use Server-Sent Events for real-time operational updates

### GraphQL API Boundaries

1. **Data-Focused**: Use GraphQL for complex data retrieval and relationships
2. **Aggregations**: Use GraphQL for analytics and metric calculations
3. **Flexible Queries**: Use GraphQL when clients need to specify exact fields
4. **Real-time Data**: Use GraphQL subscriptions for live data updates
5. **No File Operations**: GraphQL does not handle file uploads/downloads

### Forbidden Overlaps

#### ❌ Do Not Duplicate

- Portfolio CRUD operations (GraphQL only)
- Strategy execution endpoints (REST only)
- Health check endpoints (REST only)
- Complex analytical queries (GraphQL only)

#### ✅ Allowed Complements

- REST: `POST /api/v1/ma-cross/execute` → GraphQL: `query { backtestResults }`
- REST: `GET /api/v1/health` → GraphQL: `subscription { systemHealth }`
- REST: `GET /api/v1/data/csv/file.csv` → GraphQL: `query { portfolioMetrics }`

## Integration Patterns

### 1. Execute → Query Pattern

```typescript
// 1. Execute via REST
const response = await fetch('/api/v1/ma-cross/analyze', {
  method: 'POST',
  body: JSON.stringify(analysisConfig),
});
const { analysis_id } = await response.json();

// 2. Query results via GraphQL
const results = await graphqlClient.query({
  query: GET_ANALYSIS_RESULTS,
  variables: { analysisId: analysis_id },
});
```

### 2. Monitor → Subscribe Pattern

```typescript
// 1. Start monitoring via REST
await fetch('/api/performance/start-monitoring', { method: 'POST' });

// 2. Subscribe to updates via GraphQL
const subscription = graphqlClient.subscribe({
  query: PERFORMANCE_UPDATES_SUBSCRIPTION,
});
```

### 3. Configure → Query Pattern

```typescript
// 1. Configure via REST
await fetch('/api/services/initialize', { method: 'POST' });

// 2. Query configuration via GraphQL
const config = await graphqlClient.query({
  query: GET_SYSTEM_CONFIGURATION,
});
```

## Versioning Strategy

### REST API Versioning

- URL-based versioning: `/api/v1/`, `/api/v2/`
- Version-specific routers for backward compatibility
- Deprecation warnings in response headers
- Migration guides for version transitions

### GraphQL API Versioning

- Schema evolution with field deprecation
- Single evolving schema (no URL versioning)
- Deprecation directives on fields and types
- Client-side compatibility through field selection

## Performance Considerations

### REST API Optimizations

- Response caching for read-heavy operations
- Pagination for large datasets
- Compression for file transfers
- Rate limiting per operation type

### GraphQL API Optimizations

- Query complexity analysis and limits
- DataLoader for N+1 query prevention
- Response caching with TTL
- Field-level permissions and filtering

## Error Handling

### REST API Errors

```typescript
// Standard HTTP status codes with detailed error objects
{
  "status": "error",
  "code": 400,
  "message": "Invalid analysis parameters",
  "details": {
    "field": "short_window",
    "error": "Must be less than long_window"
  },
  "request_id": "req_123456"
}
```

### GraphQL API Errors

```typescript
// GraphQL error format with extensions
{
  "errors": [
    {
      "message": "Portfolio not found",
      "locations": [{"line": 2, "column": 3}],
      "path": ["portfolio"],
      "extensions": {
        "code": "PORTFOLIO_NOT_FOUND",
        "portfolioId": "portfolio_123",
        "timestamp": "2025-01-06T12:00:00Z"
      }
    }
  ],
  "data": null
}
```

## Security Model

### Authentication

- Both APIs use the same JWT-based authentication
- Shared security middleware for token validation
- Role-based access control (RBAC) across both APIs

### Authorization

- REST: Endpoint-level permissions
- GraphQL: Field-level permissions with custom directives
- Shared permission service for consistency

### Rate Limiting

- REST: Per-endpoint rate limits
- GraphQL: Query complexity-based limits
- Shared rate limiting infrastructure

## Monitoring and Observability

### Metrics Collection

- REST: HTTP request metrics (response time, status codes)
- GraphQL: Query complexity, field resolution time, error rates
- Unified performance monitoring dashboard

### Logging

- Structured logging format for both APIs
- Request correlation IDs across REST and GraphQL
- Centralized log aggregation and analysis

### Tracing

- Distributed tracing across API boundaries
- Service map visualization
- Performance bottleneck identification

## Implementation Guidelines

### For Developers

#### When to Use REST

```typescript
// ✅ Good: System operations
await restClient.post('/api/v1/scripts/execute', config);

// ✅ Good: File operations
await restClient.get('/api/v1/data/csv/portfolio.csv');

// ✅ Good: Health checks
const health = await restClient.get('/api/v1/health');
```

#### When to Use GraphQL

```typescript
// ✅ Good: Complex data queries
const portfolio = await graphqlClient.query(`
  query GetPortfolio($id: ID!) {
    portfolio(id: $id) {
      name
      strategies {
        name
        performance {
          totalReturn
          sharpeRatio
        }
      }
    }
  }
`);

// ✅ Good: Flexible analytics
const metrics = await graphqlClient.query(`
  query GetMetrics($timeRange: TimeRange!) {
    portfolioMetrics(timeRange: $timeRange) {
      totalReturn
      maxDrawdown
      trades {
        count
        winRate
      }
    }
  }
`);
```

### Migration Path

#### Phase 1: Establish Boundaries (Current)

- Document clear API responsibilities
- Identify and eliminate overlaps
- Implement unified error handling

#### Phase 2: Consolidate Operations

- Move complex queries to GraphQL
- Keep operational endpoints in REST
- Update client integrations

#### Phase 3: Optimize Performance

- Implement API-specific optimizations
- Add comprehensive monitoring
- Performance tune based on usage patterns

## Conclusion

This architecture provides:

- **Clear Separation**: No functional overlap between APIs
- **Optimal Use Cases**: Each API handles what it does best
- **Consistent Integration**: Predictable patterns for client development
- **Scalable Design**: Architecture supports independent scaling and evolution
- **Developer Experience**: Clear guidelines for API selection and usage

The separation ensures that each API can evolve independently while maintaining a cohesive overall system architecture.
