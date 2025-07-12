# Migration Guides

This document consolidates all migration guides and deprecated functionality documentation.

## Legacy Documentation Index

### Migration Guides

- [CSV Export Phase 4 Migration](../CSV_EXPORT_PHASE4_MIGRATION_GUIDE.md)
- [Monte Carlo Migration Guide](../monte_carlo_migration_guide.md)
- [MACD Parameter Testing Migration](../MACD_PARAMETER_TESTING_USER_GUIDE.md)

### Architecture Evolution

- [Service Decomposition](../architect/SERVICE_DECOMPOSITION.md) - God module decomposition
- [API Removal](../architect/API_REMOVAL.md) - API/Frontend elimination
- [CLI-First Architecture](../architect/CLI_FIRST_ARCHITECTURE.md) - CLI-first transition

### Tool-Specific Documentation

Located in `/app/tools/` - these should be migrated to the main documentation structure:

#### Signal Processing

- [Signal Metrics](../../app/tools/README_signal_metrics.md)
- [Signal Configuration](../../app/tools/README_signal_config.md)
- [Signal Troubleshooting](../../app/tools/README_signal_troubleshooting.md)
- [Signal Conversion](../../app/tools/README_signal_conversion.md)
- [Signal Filtering](../../app/tools/README_signal_filtering.md)
- [Signal Flowcharts](../../app/tools/README_signal_flowcharts.md)

#### Analysis Tools

- [Statistical Analysis](../../app/tools/statistical_analysis_README.md)
- [CLI Documentation](../../app/tools/CLI_README.md)
- [Expectancy Analysis](../../app/tools/README_expectancy.md)
- [Metric Definitions](../../app/tools/README_metric_definitions.md)
- [Horizon Analysis](../../app/tools/README_horizon_analysis.md)
- [Stop Loss Simulator](../../app/tools/README_stop_loss_simulator.md)

#### Portfolio Management

- [Portfolio Allocation](../../app/tools/portfolio/README_allocation.md)
- [Export Tools](../../app/tools/export/README.md)
- [Strategy Tools](../../app/tools/strategy/README.md)

#### Naming and Conventions

- [Naming Conventions](../../app/tools/README_naming_conventions.md)

### Strategy-Specific Documentation

Located in `/app/strategies/` - these should be consolidated:

#### MACD Strategy

- [MACD Migration Summary](../../app/strategies/macd/MIGRATION_SUMMARY.md)

#### Geometric Brownian Motion

- [GBM Strategy Documentation](../../app/strategies/geometric_brownian_motion/README.md)

### Business Documentation

Located in `/docs/business_analyst/` and `/docs/product_owner/`:

#### Business Analysis

- [Parameter Testing User Stories](../business_analyst/parameter_testing_user_stories.md)

#### Product Owner Documentation

- [Product Owner Analysis](../product_owner/PRODUCT_OWNER_ANALYSIS_20250106.md)
- [Strategy Execution Patterns Audit](../product_owner/STRATEGY_EXECUTION_PATTERNS_AUDIT.md)
- [Test Infrastructure Analysis](../product_owner/TEST_INFRASTRUCTURE_ANALYSIS.md)

### Social Media Content

Located in `/docs/twitter strategy posts/` and `/docs/twitter strategy templates/`:

#### Strategy Posts

- [AAPL Strategy](../twitter%20strategy%20posts/AAPL.md)
- [AMD Strategy](../twitter%20strategy%20posts/AMD.md)
- [COIN Strategy](../twitter%20strategy%20posts/COIN.md)
- [GD Strategy](../twitter%20strategy%20posts/GD.md)
- [GOOGL Strategy](../twitter%20strategy%20posts/GOOGL.md)
- [LMT Strategy](../twitter%20strategy%20posts/LMT.md)

#### Content Templates

- [Master Template](../twitter%20strategy%20templates/master.md)
- [Templates](../twitter%20strategy%20templates/templates.md)
- [Universal Trading Strategy](../twitter%20strategy%20templates/universal_trading_strategy.md)

### Technical Analysis

- [Portfolio Consistency Analysis](../portfolio_consistency_analysis_20250530.md)
- [Strategy Level Fields Analysis](../strategy_level_fields_analysis.md)
- [CSV Schemas](../csv_schemas.md)

## Migration Path

### Phase 1: Immediate Consolidation ✅

- [x] Create structured documentation architecture
- [x] Organize documentation by purpose and audience
- [x] Create navigation and index files

### Phase 2: Content Migration

- [ ] Migrate tool-specific documentation to appropriate sections
- [ ] Consolidate strategy documentation
- [ ] Update cross-references and links

### Phase 3: Cleanup

- [ ] Remove redundant documentation
- [ ] Archive obsolete content
- [ ] Update build processes to reflect new structure

## Migration Strategy

### 1. Content Audit

Review all documentation for:

- **Relevance**: Is the content still applicable?
- **Accuracy**: Is the information up to date?
- **Duplication**: Are there multiple sources for the same information?
- **Organization**: Where should this content live in the new structure?

### 2. Content Classification

Classify content into:

- **Active**: Currently relevant and should be migrated
- **Archive**: Historical value but not actively maintained
- **Deprecated**: Obsolete and should be removed
- **Duplicate**: Content that exists elsewhere

### 3. Migration Process

1. **Identify target location** in new structure
2. **Update content** to match new format and standards
3. **Update cross-references** to point to new locations
4. **Test all links** to ensure they work
5. **Remove old content** after successful migration

### 4. Link Update Strategy

- Use find/replace for systematic link updates
- Check all internal references
- Validate external links
- Update any automated processes that reference old paths

## Deprecated Features

### Removed Components

- **API Server**: Removed as part of CLI-first architecture
- **Frontend**: Removed as part of CLI-first architecture
- **GraphQL Integration**: Removed with API elimination

### Deprecated Commands

- Direct script execution (replaced with CLI commands)
- Legacy configuration formats
- Hardcoded parameter dictionaries

### Legacy Configuration

- Old YAML formats without validation
- Hardcoded constants in source files
- Environment-specific configurations

## Maintenance Guidelines

### Documentation Standards

- Use consistent formatting and structure
- Include examples and code snippets
- Keep language clear and concise
- Update alongside code changes

### Review Process

- All documentation changes go through code review
- Validate all links and references
- Test all examples and code snippets
- Ensure consistency with existing documentation

### Archival Policy

- Archive obsolete content rather than deleting
- Maintain historical context for architectural decisions
- Document reasons for deprecation
- Provide migration paths for deprecated features

---

_This migration guide was created as part of the documentation architecture consolidation in 2025. For current documentation, see the [main documentation index](../README.md)._
