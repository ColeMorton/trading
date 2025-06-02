/**
 * Test script to validate GraphQL integration
 * Run with: npm run test:graphql
 */

import { initializeApollo } from '../apollo/client';
import { 
  GetFileListDocument,
  GetPortfoliosDocument,
  ExecuteMaCrossAnalysisDocument,
  TimeframeType,
  StrategyType,
  DirectionType
} from '../graphql/generated';

async function testGraphQLIntegration() {
  console.log('🚀 Starting GraphQL Integration Test...\n');

  try {
    // Initialize Apollo Client
    console.log('1️⃣ Initializing Apollo Client...');
    const client = await initializeApollo();
    console.log('✅ Apollo Client initialized successfully\n');

    // Test 1: Query file list
    console.log('2️⃣ Testing GetFileList query...');
    const fileListResult = await client.query({
      query: GetFileListDocument,
      variables: { limit: 10 }
    });
    console.log(`✅ Retrieved ${fileListResult.data.tickers?.length || 0} tickers and ${fileListResult.data.strategies?.length || 0} strategies\n`);

    // Test 2: Query portfolios
    console.log('3️⃣ Testing GetPortfolios query...');
    const portfoliosResult = await client.query({
      query: GetPortfoliosDocument,
      variables: { filter: { limit: 5 } }
    });
    console.log(`✅ Retrieved ${portfoliosResult.data.portfolios?.length || 0} portfolios\n`);

    // Test 3: Execute MA Cross Analysis
    console.log('4️⃣ Testing MA Cross Analysis mutation...');
    const analysisResult = await client.mutate({
      mutation: ExecuteMaCrossAnalysisDocument,
      variables: {
        input: {
          ticker: ['BTC-USD'],
          windows: 50,
          direction: DirectionType.Long,
          strategyTypes: [StrategyType.MaCross],
          timeframe: TimeframeType.OneDay,
          asyncExecution: false
        }
      }
    });

    if ('portfolios' in analysisResult.data.executeMaCrossAnalysis) {
      const response = analysisResult.data.executeMaCrossAnalysis;
      console.log(`✅ Analysis completed:`);
      console.log(`   - Status: ${response.status}`);
      console.log(`   - Portfolios analyzed: ${response.totalPortfoliosAnalyzed}`);
      console.log(`   - Execution time: ${response.executionTime}ms\n`);
    } else {
      console.log('✅ Async analysis started\n');
    }

    // Test 4: Cache persistence
    console.log('5️⃣ Testing cache persistence...');
    const cache = client.cache.extract();
    console.log(`✅ Cache contains ${Object.keys(cache).length} entries\n`);

    console.log('🎉 All GraphQL integration tests passed!');
  } catch (error) {
    console.error('❌ GraphQL integration test failed:', error);
    process.exit(1);
  }
}

// Run the test
if (import.meta.url === `file://${process.argv[1]}`) {
  testGraphQLIntegration();
}