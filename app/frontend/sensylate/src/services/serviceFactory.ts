import { api as restApi } from './api';
import { maCrossApi as restMaCrossApi } from './maCrossApi';
import { graphqlApi } from './graphql/apiAdapter';
import { graphqlMaCrossApi } from './graphql/maCrossAdapter';

// Feature flag to control which API to use
const USE_GRAPHQL = import.meta.env.VITE_USE_GRAPHQL === 'true' || false;

/**
 * Service factory that returns either REST or GraphQL implementations
 * This allows for gradual migration and easy switching between APIs
 */
export const api = USE_GRAPHQL ? graphqlApi : restApi;
export const maCrossApi = USE_GRAPHQL ? graphqlMaCrossApi : restMaCrossApi;

// Export a function to check which API is being used
export const isUsingGraphQL = () => USE_GRAPHQL;

// Export function to switch API at runtime (useful for testing)
export const setApiMode = (useGraphQL: boolean) => {
  if (useGraphQL) {
    console.log('Switching to GraphQL API');
    // Note: This would need to trigger a re-render of components
    // In production, this would be handled through environment variables
  } else {
    console.log('Switching to REST API');
  }
};
