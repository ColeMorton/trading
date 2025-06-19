import React, { useEffect, useState } from 'react';
import { ApolloProvider as BaseApolloProvider } from '@apollo/client';
import { initializeApollo } from '../apollo/client';
import LoadingIndicator from '../components/LoadingIndicator';

interface ApolloProviderProps {
  children: React.ReactNode;
}

export const ApolloProvider: React.FC<ApolloProviderProps> = ({ children }) => {
  const [client, setClient] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let mounted = true;

    const init = async () => {
      try {
        const apolloClient = await initializeApollo();
        if (mounted) {
          setClient(apolloClient);
          setLoading(false);
        }
      } catch (err) {
        if (mounted) {
          setError('Failed to initialize Apollo Client');
          setLoading(false);
          console.error('Apollo initialization error:', err);
        }
      }
    };

    init();

    return () => {
      mounted = false;
    };
  }, []);

  if (loading) {
    return (
      <div className="d-flex justify-content-center align-items-center min-vh-100">
        <LoadingIndicator />
      </div>
    );
  }

  if (error) {
    return (
      <div className="alert alert-danger m-3" role="alert">
        {error}
      </div>
    );
  }

  if (!client) {
    return null;
  }

  return <BaseApolloProvider client={client}>{children}</BaseApolloProvider>;
};
