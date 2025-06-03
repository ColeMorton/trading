"""
GraphQL Testing Script

This script provides basic testing for the GraphQL implementation.
"""

import asyncio
import json
from typing import Any, Dict

import httpx


class GraphQLTester:
    """Test client for GraphQL endpoints."""

    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.graphql_url = f"{base_url}/graphql"

    async def execute_query(
        self, query: str, variables: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Execute a GraphQL query."""
        payload = {"query": query, "variables": variables or {}}

        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.graphql_url,
                json=payload,
                headers={"Content-Type": "application/json"},
            )

            return response.json()

    async def test_introspection(self) -> Dict[str, Any]:
        """Test GraphQL introspection."""
        query = """
        query IntrospectionQuery {
            __schema {
                types {
                    name
                    kind
                }
                queryType {
                    name
                }
                mutationType {
                    name
                }
            }
        }
        """

        return await self.execute_query(query)

    async def test_tickers_query(self) -> Dict[str, Any]:
        """Test tickers query."""
        query = """
        query GetTickers {
            tickers(limit: 5) {
                id
                symbol
                name
                assetClass
                createdAt
            }
        }
        """

        return await self.execute_query(query)

    async def test_strategies_query(self) -> Dict[str, Any]:
        """Test strategies query."""
        query = """
        query GetStrategies {
            strategies(limit: 5) {
                id
                name
                type
                description
                createdAt
            }
        }
        """

        return await self.execute_query(query)

    async def test_portfolios_query(self) -> Dict[str, Any]:
        """Test portfolios query."""
        query = """
        query GetPortfolios {
            portfolios(limit: 5) {
                id
                name
                description
                type
                createdAt
            }
        }
        """

        return await self.execute_query(query)

    async def test_create_portfolio_mutation(self) -> Dict[str, Any]:
        """Test create portfolio mutation."""
        query = """
        mutation CreatePortfolio($input: PortfolioInput!) {
            createPortfolio(input: $input) {
                id
                name
                description
                type
                createdAt
            }
        }
        """

        variables = {
            "input": {
                "name": "Test Portfolio",
                "description": "A test portfolio created via GraphQL",
                "type": "STANDARD",
            }
        }

        return await self.execute_query(query, variables)

    async def test_ma_cross_analysis_mutation(self) -> Dict[str, Any]:
        """Test MA Cross analysis mutation."""
        query = """
        mutation ExecuteMACrossAnalysis($input: MACrossAnalysisInput!) {
            executeMaCrossAnalysis(input: $input) {
                ... on MACrossAnalysisResponse {
                    requestId
                    status
                    ticker
                    strategyTypes
                    totalPortfoliosAnalyzed
                    totalPortfoliosFiltered
                    executionTime
                }
                ... on AsyncAnalysisResponse {
                    executionId
                    status
                    message
                    statusUrl
                    streamUrl
                }
            }
        }
        """

        variables = {
            "input": {
                "ticker": "BTC-USD",
                "windows": 12,
                "direction": "LONG",
                "strategyTypes": ["MA_CROSS"],
                "asyncExecution": False,
            }
        }

        return await self.execute_query(query, variables)

    async def run_all_tests(self):
        """Run all GraphQL tests."""
        print("🚀 Starting GraphQL Tests...")
        print("=" * 50)

        tests = [
            ("Introspection", self.test_introspection),
            ("Tickers Query", self.test_tickers_query),
            ("Strategies Query", self.test_strategies_query),
            ("Portfolios Query", self.test_portfolios_query),
            ("Create Portfolio Mutation", self.test_create_portfolio_mutation),
            ("MA Cross Analysis Mutation", self.test_ma_cross_analysis_mutation),
        ]

        results = {}

        for test_name, test_func in tests:
            print(f"\n📝 Running {test_name}...")
            try:
                result = await test_func()

                if "errors" in result:
                    print(f"❌ {test_name} FAILED")
                    print(f"   Errors: {result['errors']}")
                    results[test_name] = {
                        "status": "FAILED",
                        "errors": result["errors"],
                    }
                else:
                    print(f"✅ {test_name} PASSED")
                    results[test_name] = {
                        "status": "PASSED",
                        "data": result.get("data"),
                    }

            except Exception as e:
                print(f"💥 {test_name} ERROR: {str(e)}")
                results[test_name] = {"status": "ERROR", "error": str(e)}

        print("\n" + "=" * 50)
        print("📊 Test Results Summary:")

        passed = sum(1 for r in results.values() if r["status"] == "PASSED")
        failed = sum(1 for r in results.values() if r["status"] == "FAILED")
        errors = sum(1 for r in results.values() if r["status"] == "ERROR")

        print(f"   ✅ Passed: {passed}")
        print(f"   ❌ Failed: {failed}")
        print(f"   💥 Errors: {errors}")
        print(f"   📊 Total: {len(results)}")

        if failed == 0 and errors == 0:
            print("\n🎉 All tests passed! GraphQL implementation is working correctly.")
        else:
            print("\n⚠️  Some tests failed. Check the output above for details.")

        return results


async def main():
    """Main test function."""
    tester = GraphQLTester()
    await tester.run_all_tests()


if __name__ == "__main__":
    asyncio.run(main())
