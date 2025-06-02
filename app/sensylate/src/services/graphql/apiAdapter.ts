import { getApolloClient } from '../../apollo/client';
import { CSVFile, CSVData, UpdateStatus } from '../../types';
import { 
  GetFileListDocument,
  GetPortfoliosDocument,
  GetPriceDataDocument,
  UpdatePortfolioDocument
} from '../../graphql/generated';

/**
 * GraphQL API adapter that maintains the same interface as the REST API service
 * This allows for a gradual migration from REST to GraphQL
 */
export const graphqlApi = {
  /**
   * Get list of available files (strategies/portfolios)
   */
  getFileList: async (): Promise<CSVFile[]> => {
    try {
      const client = getApolloClient();
      
      // Execute GraphQL query
      const { data } = await client.query({
        query: GetFileListDocument,
        fetchPolicy: 'cache-first' // Use cache when available for offline support
      });

      // Transform strategies to file list format
      const files: CSVFile[] = [];
      
      // Add strategy files
      if (data.strategies) {
        data.strategies.forEach(strategy => {
          files.push({
            path: `strategies/${strategy.name}.csv`,
            name: `${strategy.name}.csv`
          });
        });
      }

      // Add portfolio files from portfolios query if needed
      const portfolioResult = await client.query({
        query: GetPortfoliosDocument,
        variables: { filter: { limit: 100 } },
        fetchPolicy: 'cache-first'
      });

      if (portfolioResult.data.portfolios) {
        const uniquePortfolios = new Set<string>();
        portfolioResult.data.portfolios.forEach(portfolio => {
          if (!uniquePortfolios.has(portfolio.name)) {
            uniquePortfolios.add(portfolio.name);
            files.push({
              path: `portfolios/${portfolio.name}.csv`,
              name: `${portfolio.name}.csv`
            });
          }
        });
      }

      // Sort files by name
      return files.sort((a, b) => a.name.localeCompare(b.name));
    } catch (error) {
      console.error('GraphQL error fetching file list:', error);
      throw error;
    }
  },

  /**
   * Get CSV data for a specific file
   */
  getCSVData: async (filePath: string): Promise<CSVData> => {
    try {
      const client = getApolloClient();
      
      // Extract symbol from file path (e.g., "strategies/BTC-USD.csv" -> "BTC-USD")
      const pathParts = filePath.split('/');
      const fileName = pathParts[pathParts.length - 1];
      const symbol = fileName.replace('.csv', '');

      // Fetch price data for the symbol
      const { data } = await client.query({
        query: GetPriceDataDocument,
        variables: {
          symbol,
          filter: {
            limit: 1000 // Get recent data
          }
        },
        fetchPolicy: 'cache-first'
      });

      if (!data.priceData || data.priceData.length === 0) {
        throw new Error(`No data found for ${symbol}`);
      }

      // Transform price data to CSV format
      const csvData = {
        data: data.priceData.map(bar => ({
          date: bar.date,
          open: bar.open,
          high: bar.high,
          low: bar.low,
          close: bar.close,
          volume: bar.volume || 0
        })),
        columns: ['date', 'open', 'high', 'low', 'close', 'volume']
      };

      return csvData;
    } catch (error) {
      console.error('GraphQL error fetching CSV data:', error);
      throw error;
    }
  },

  /**
   * Update portfolio (trigger analysis)
   */
  updatePortfolio: async (fileName: string): Promise<UpdateStatus> => {
    try {
      const client = getApolloClient();
      
      // Extract portfolio name from file name
      const portfolioName = fileName.replace('.csv', '');

      // Find the portfolio
      const { data: portfolioData } = await client.query({
        query: GetPortfoliosDocument,
        variables: {
          filter: {
            name: portfolioName,
            limit: 1
          }
        }
      });

      if (!portfolioData.portfolios || portfolioData.portfolios.length === 0) {
        throw new Error(`Portfolio ${portfolioName} not found`);
      }

      const portfolio = portfolioData.portfolios[0];

      // Execute update mutation
      const { data } = await client.mutate({
        mutation: UpdatePortfolioDocument,
        variables: {
          id: portfolio.id,
          input: {
            name: portfolio.name,
            type: portfolio.type
          }
        }
      });

      // Return update status
      return {
        status: 'success',
        message: `Portfolio ${portfolioName} updated successfully`,
        timestamp: new Date().toISOString()
      };
    } catch (error) {
      console.error('GraphQL error updating portfolio:', error);
      return {
        status: 'error',
        message: error instanceof Error ? error.message : 'Update failed',
        timestamp: new Date().toISOString()
      };
    }
  }
};