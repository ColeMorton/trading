import {
  ApolloClient,
  InMemoryCache,
  createHttpLink,
  ApolloLink,
  from,
} from '@apollo/client';
import { onError } from '@apollo/client/link/error';
import { setContext } from '@apollo/client/link/context';
import { persistCache, LocalStorageWrapper } from 'apollo3-cache-persist';

// Create HTTP link pointing to the GraphQL endpoint
const httpLink = createHttpLink({
  uri: '/graphql', // Uses Vite proxy to localhost:8000
  credentials: 'same-origin',
});

// Auth link - adds authentication headers if available
const authLink = setContext((_, { headers }) => {
  // Get the authentication token from local storage if it exists
  const token = localStorage.getItem('auth-token');

  return {
    headers: {
      ...headers,
      authorization: token ? `Bearer ${token}` : '',
    },
  };
});

// Error handling link
const errorLink = onError(
  ({ graphQLErrors, networkError, operation, forward }) => {
    if (graphQLErrors) {
      graphQLErrors.forEach(({ message, locations, path }) => {
        console.error(
          `GraphQL error: Message: ${message}, Location: ${locations}, Path: ${path}`
        );
      });
    }

    if (networkError) {
      console.error(`Network error: ${networkError}`);

      // If offline, the cache will be used automatically
      if (!navigator.onLine) {
        console.log('Offline mode - using cached data');
      }
    }
  }
);

// Logging link for development
const loggingLink = new ApolloLink((operation, forward) => {
  if (import.meta.env.DEV) {
    console.log(`GraphQL Request: ${operation.operationName}`);
    console.log('Variables:', operation.variables);
  }

  return forward(operation).map((result) => {
    if (import.meta.env.DEV) {
      console.log(`GraphQL Response: ${operation.operationName}`, result);
    }
    return result;
  });
});

// Create Apollo cache with configuration
export const cache = new InMemoryCache({
  typePolicies: {
    Query: {
      fields: {
        // Define merge functions for paginated queries
        portfolios: {
          keyArgs: ['filter'],
          merge(existing = [], incoming) {
            return [...incoming];
          },
        },
        strategies: {
          keyArgs: ['filter'],
          merge(existing = [], incoming) {
            return [...incoming];
          },
        },
        priceData: {
          keyArgs: ['symbol', 'filter'],
          merge(existing = [], incoming) {
            return [...incoming];
          },
        },
      },
    },
    Portfolio: {
      keyFields: ['id'],
    },
    Strategy: {
      keyFields: ['id'],
    },
    Ticker: {
      keyFields: ['id'],
    },
  },
});

// Initialize Apollo Client
let apolloClient: ApolloClient<any>;

export async function initializeApollo() {
  // Persist cache to localStorage for offline support
  await persistCache({
    cache,
    storage: new LocalStorageWrapper(window.localStorage),
    maxSize: 1048576 * 10, // 10MB
    key: 'apollo-cache-persist',
  });

  apolloClient = new ApolloClient({
    link: from([errorLink, loggingLink, authLink, httpLink]),
    cache,
    defaultOptions: {
      watchQuery: {
        fetchPolicy: 'cache-and-network',
        errorPolicy: 'all',
      },
      query: {
        fetchPolicy: 'cache-first',
        errorPolicy: 'all',
      },
    },
  });

  return apolloClient;
}

export function getApolloClient() {
  if (!apolloClient) {
    throw new Error(
      'Apollo Client not initialized. Call initializeApollo() first.'
    );
  }
  return apolloClient;
}
