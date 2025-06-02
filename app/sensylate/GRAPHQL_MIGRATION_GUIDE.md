# GraphQL Migration Guide

## Overview

This guide explains how to use the new GraphQL API integration in the Sensylate frontend application. The migration from REST to GraphQL has been implemented with a gradual adoption strategy, allowing both APIs to coexist.

## Configuration

### Enabling GraphQL

1. Create a `.env` file in the `app/sensylate` directory:
```bash
cp .env.example .env
```

2. Set the GraphQL flag to enable GraphQL:
```env
VITE_USE_GRAPHQL=true
```

### Installing Dependencies

```bash
cd app/sensylate
npm install
```

## Development Workflow

### 1. Generate GraphQL Types

First, ensure the backend GraphQL server is running:
```bash
cd ../..
python -m app.api.run
```

Then generate TypeScript types from the GraphQL schema:
```bash
npm run codegen
```

For continuous development with auto-regeneration:
```bash
npm run codegen:watch
```

### 2. Writing GraphQL Operations

GraphQL operations are organized in `src/graphql/`:
- `queries/` - Query operations
- `mutations/` - Mutation operations
- `fragments/` - Reusable fragments

Example query (`src/graphql/queries/portfolios.graphql`):
```graphql
query GetPortfolios($filter: PortfolioFilter) {
  portfolios(filter: $filter) {
    id
    name
    type
    ticker {
      symbol
    }
    performance {
      totalReturn
      sharpeRatio
    }
  }
}
```

### 3. Using Generated Hooks

After running codegen, TypeScript hooks are automatically generated:

```typescript
import { useGetPortfoliosQuery } from '../graphql/generated';

const PortfolioList = () => {
  const { data, loading, error } = useGetPortfoliosQuery({
    variables: {
      filter: { limit: 10 }
    }
  });

  if (loading) return <LoadingIndicator />;
  if (error) return <ErrorMessage error={error} />;

  return (
    <ul>
      {data?.portfolios.map(portfolio => (
        <li key={portfolio.id}>{portfolio.name}</li>
      ))}
    </ul>
  );
};
```

## Architecture

### Service Factory Pattern

The application uses a service factory pattern to switch between REST and GraphQL:

```typescript
// src/services/serviceFactory.ts
export const api = USE_GRAPHQL ? graphqlApi : restApi;
export const maCrossApi = USE_GRAPHQL ? graphqlMaCrossApi : restMaCrossApi;
```

This allows components to remain unchanged while switching between APIs.

### Apollo Client Configuration

Apollo Client is configured with:
- **Cache persistence**: LocalStorage caching for offline support
- **Error handling**: Comprehensive error handling with fallbacks
- **Type safety**: Full TypeScript support with generated types
- **Optimistic updates**: For better UX during mutations
- **Network policies**: Smart caching strategies

### Offline Support

The GraphQL implementation maintains offline capabilities through:
1. Apollo Cache persistence to LocalStorage
2. Cache-first fetch policies for read operations
3. Automatic cache rehydration on app startup
4. Network status detection with appropriate fallbacks

## Migration Strategy

### Phase 1: Parallel Implementation ✅
- Apollo Client setup
- GraphQL adapters matching REST interface
- Service factory for API switching

### Phase 2: Component Migration (Current)
- Gradual migration of components to use GraphQL hooks
- Feature flags for A/B testing
- Performance monitoring

### Phase 3: REST Deprecation (Future)
- Remove REST API calls
- Clean up adapter layers
- Full GraphQL adoption

## Testing

### Manual Testing
1. Enable GraphQL in `.env`
2. Run the application
3. Verify all features work as expected
4. Check network tab for GraphQL requests

### Integration Testing
```bash
# Run GraphQL integration tests
npm run test:graphql
```

## Performance Considerations

### Query Optimization
- Use fragments to avoid over-fetching
- Implement pagination for large datasets
- Leverage Apollo Cache for data deduplication

### Cache Management
```typescript
// Clear cache when needed
import { getApolloClient } from './apollo/client';

const client = getApolloClient();
client.cache.reset();
```

## Troubleshooting

### Common Issues

1. **"Cannot find module './graphql/generated'"**
   - Run `npm run codegen` to generate types

2. **GraphQL endpoint not reachable**
   - Ensure backend is running on port 8000
   - Check Vite proxy configuration

3. **Type mismatches**
   - Regenerate types after schema changes
   - Ensure all GraphQL operations are valid

### Debug Mode

Enable GraphQL logging in development:
```typescript
// Logs are automatically enabled in dev mode
// Check browser console for GraphQL operations
```

## Best Practices

1. **Always regenerate types** after schema changes
2. **Use fragments** for shared fields
3. **Implement error boundaries** for GraphQL errors
4. **Monitor cache size** to prevent memory issues
5. **Test offline scenarios** thoroughly

## Resources

- [Apollo Client Documentation](https://www.apollographql.com/docs/react/)
- [GraphQL Code Generator](https://the-guild.dev/graphql/codegen)
- [Strawberry GraphQL](https://strawberry.rocks/)