"""
Smart fixture dependency injection system for automated resolution.
Phase 3: Testing Infrastructure Consolidation
"""

import inspect
from collections.abc import Callable
from typing import Any


class FixtureRegistry:
    """
    Smart fixture registry that automatically resolves dependencies and optimizes fixture loading.
    """

    def __init__(self):
        self.fixtures: dict[str, dict[str, Any]] = {}
        self.dependencies: dict[str, set[str]] = {}
        self.cached_fixtures: dict[str, Any] = {}
        self.resolution_order: list[str] = []

    def register_fixture(
        self,
        name: str,
        factory: Callable,
        dependencies: list[str] | None = None,
        scope: str = "function",
        cache: bool = False,
    ):
        """
        Register fixture with automatic dependency resolution.

        Args:
            name: Fixture name
            factory: Factory function to create fixture
            dependencies: List of dependency fixture names
            scope: Pytest scope (session, module, function)
            cache: Whether to cache the fixture result
        """
        if dependencies is None:
            dependencies = self._auto_detect_dependencies(factory)

        self.fixtures[name] = {
            "factory": factory,
            "scope": scope,
            "cache": cache,
            "dependencies": set(dependencies),
        }
        self.dependencies[name] = set(dependencies)

    def _auto_detect_dependencies(self, factory: Callable) -> list[str]:
        """Automatically detect fixture dependencies from function signature."""
        signature = inspect.signature(factory)
        dependencies = []

        for param_name in signature.parameters:
            # Skip self parameter
            if param_name == "self":
                continue
            # Check if parameter name matches a registered fixture
            if param_name in self.fixtures:
                dependencies.append(param_name)

        return dependencies

    def resolve_dependencies(self, fixture_name: str) -> dict[str, Any]:
        """
        Automatically resolve and inject fixture dependencies.

        Args:
            fixture_name: Name of the fixture to resolve

        Returns:
            Dictionary of resolved dependency fixtures
        """
        if fixture_name not in self.fixtures:
            msg = f"Fixture '{fixture_name}' not registered"
            raise ValueError(msg)

        resolved_deps = {}
        dependencies = self.dependencies[fixture_name]

        # Resolve dependencies recursively
        for dep_name in dependencies:
            if dep_name in self.cached_fixtures:
                resolved_deps[dep_name] = self.cached_fixtures[dep_name]
            else:
                # Recursively resolve dependencies of dependencies
                nested_deps = self.resolve_dependencies(dep_name)
                dep_fixture = self.create_fixture(dep_name, nested_deps)
                resolved_deps[dep_name] = dep_fixture

                # Cache if configured
                if self.fixtures[dep_name]["cache"]:
                    self.cached_fixtures[dep_name] = dep_fixture

        return resolved_deps

    def create_fixture(
        self,
        fixture_name: str,
        dependencies: dict[str, Any] | None = None,
    ):
        """
        Create fixture instance with resolved dependencies.

        Args:
            fixture_name: Name of fixture to create
            dependencies: Resolved dependency fixtures

        Returns:
            Created fixture instance
        """
        if fixture_name not in self.fixtures:
            msg = f"Fixture '{fixture_name}' not registered"
            raise ValueError(msg)

        fixture_config = self.fixtures[fixture_name]
        factory = fixture_config["factory"]

        if dependencies is None:
            dependencies = self.resolve_dependencies(fixture_name)

        # Call factory with resolved dependencies
        try:
            return factory(**dependencies)
        except Exception as e:
            msg = f"Failed to create fixture '{fixture_name}': {e!s}"
            raise RuntimeError(
                msg,
            ) from e

    def get_resolution_order(self) -> list[str]:
        """
        Get optimal resolution order for fixtures based on dependencies.

        Returns:
            List of fixture names in dependency order
        """
        if self.resolution_order:
            return self.resolution_order

        # Topological sort to determine resolution order
        visited = set()
        temp_visited = set()
        order = []

        def visit(fixture_name: str):
            if fixture_name in temp_visited:
                msg = f"Circular dependency detected involving '{fixture_name}'"
                raise ValueError(
                    msg,
                )
            if fixture_name not in visited:
                temp_visited.add(fixture_name)
                for dep in self.dependencies.get(fixture_name, set()):
                    visit(dep)
                temp_visited.remove(fixture_name)
                visited.add(fixture_name)
                order.append(fixture_name)

        for fixture_name in self.fixtures:
            if fixture_name not in visited:
                visit(fixture_name)

        self.resolution_order = order
        return order

    def clear_cache(self, fixture_names: list[str] | None = None):
        """
        Clear cached fixtures.

        Args:
            fixture_names: Specific fixtures to clear, or None for all
        """
        if fixture_names is None:
            self.cached_fixtures.clear()
        else:
            for name in fixture_names:
                self.cached_fixtures.pop(name, None)

    def validate_dependencies(self) -> dict[str, list[str]]:
        """
        Validate all fixture dependencies and return any issues.

        Returns:
            Dictionary of fixture names with their dependency issues
        """
        issues = {}

        for fixture_name, deps in self.dependencies.items():
            fixture_issues = []

            # Check for missing dependencies
            for dep in deps:
                if dep not in self.fixtures:
                    fixture_issues.append(f"Missing dependency: {dep}")

            # Check for circular dependencies
            try:
                self.get_resolution_order()
            except ValueError as e:
                if fixture_name in str(e):
                    fixture_issues.append(f"Circular dependency: {e!s}")

            if fixture_issues:
                issues[fixture_name] = fixture_issues

        return issues

    def generate_pytest_fixtures(self) -> str:
        """
        Generate pytest fixture code for all registered fixtures.

        Returns:
            String containing pytest fixture definitions
        """
        fixture_code = []
        resolution_order = self.get_resolution_order()

        for fixture_name in resolution_order:
            config = self.fixtures[fixture_name]
            scope = config["scope"]

            # Generate fixture code
            code = f'''
@pytest.fixture(scope="{scope}")
def {fixture_name}({", ".join(config["dependencies"])}):
    """Auto-generated fixture with dependency injection."""
    registry = get_fixture_registry()
    return registry.create_fixture("{fixture_name}")
'''
            fixture_code.append(code)

        return "\n".join(fixture_code)


# Global registry instance
_fixture_registry = None


def get_fixture_registry() -> FixtureRegistry:
    """Get the global fixture registry instance."""
    global _fixture_registry
    if _fixture_registry is None:
        _fixture_registry = FixtureRegistry()
    return _fixture_registry


def register_fixture(
    name: str,
    factory: Callable,
    dependencies: list[str] | None = None,
    scope: str = "function",
    cache: bool = False,
):
    """
    Decorator for registering fixtures with dependency injection.

    Args:
        name: Fixture name
        factory: Factory function
        dependencies: Manual dependency list (auto-detected if None)
        scope: Pytest scope
        cache: Whether to cache results
    """

    def decorator(func):
        registry = get_fixture_registry()
        registry.register_fixture(name, func, dependencies, scope, cache)
        return func

    return decorator


# =============================================================================
# Pre-configured fixture compositions for common scenarios
# =============================================================================


class FixtureComposer:
    """Compose complex fixtures from simpler components."""

    def __init__(self, registry: FixtureRegistry):
        self.registry = registry

    def create_api_test_suite(self) -> dict[str, Any]:
        """Create complete API test suite with all dependencies."""
        return {
            "api_client": self.registry.create_fixture("api_client"),
            "test_data": self.registry.create_fixture("sample_portfolio_data"),
            "performance_monitor": self.registry.create_fixture("performance_metrics"),
            "environment": self.registry.create_fixture("api_environment"),
        }

    def create_strategy_test_suite(self) -> dict[str, Any]:
        """Create complete strategy test suite with market data."""
        return {
            "market_data": self.registry.create_fixture("sample_market_data"),
            "portfolio_config": self.registry.create_fixture("sample_portfolio_config"),
            "strategy_config": self.registry.create_fixture("sample_strategy_config"),
            "signals": self.registry.create_fixture("test_signals"),
        }

    def create_performance_test_suite(self) -> dict[str, Any]:
        """Create performance testing suite with monitoring."""
        return {
            "timer": self.registry.create_fixture("performance_timer"),
            "memory_monitor": self.registry.create_fixture("memory_monitor"),
            "large_dataset": self.registry.create_fixture("sample_market_data"),
        }


def get_fixture_composer() -> FixtureComposer:
    """Get fixture composer instance."""
    return FixtureComposer(get_fixture_registry())
