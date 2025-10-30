---
title: Documentation Index with Metadata
version: 1.0
last_updated: 2025-10-30
owner: Documentation Team
status: Active
audience: All
---

# Documentation Index with Metadata

Comprehensive index of all trading system documentation with categorization, metadata, and quick access links.

**Last Generated**: 2025-10-30
**Total Documents**: 164 markdown files
**Total Directories**: 25+

---

## Quick Navigation

- [Core Documentation](#core-documentation)
- [Getting Started](#getting-started)
- [API Documentation](#api-documentation)
- [Development](#development-documentation)
- [Architecture](#architecture-documentation)
- [Testing](#testing-documentation)
- [Reference](#reference-documentation)
- [Research](#research-documentation)
- [Archive](#archived-documentation)

---

## Core Documentation

### Essential Reading

| Document                                         | Version | Status | Audience              | Last Updated |
| ------------------------------------------------ | ------- | ------ | --------------------- | ------------ |
| [README.md](README.md)                           | 2.0     | Active | All                   | 2025-10-29   |
| [USER_MANUAL.md](USER_MANUAL.md)                 | 3.0     | Active | Users, Developers     | 2025-09-10   |
| [USER_GUIDE.md](USER_GUIDE.md)                   | 1.5     | Active | End Users             | 2025-09-10   |
| [CHANGELOG.md](CHANGELOG.md)                     | 1.0     | Active | All                   | 2025-10-30   |
| [CONFIGURATION_GUIDE.md](CONFIGURATION_GUIDE.md) | 1.2     | Active | Developers, Operators | 2025-10-30   |

### System-Wide

| Document                                                               | Purpose                   | Status    |
| ---------------------------------------------------------------------- | ------------------------- | --------- |
| [PERFORMANCE_OPTIMIZATION_GUIDE.md](PERFORMANCE_OPTIMIZATION_GUIDE.md) | Performance tuning        | Active    |
| [NAMING_CONVENTIONS_PLAN.md](NAMING_CONVENTIONS_PLAN.md)               | Codebase naming standards | Active    |
| [TYPEDDICT_AUDIT.md](TYPEDDICT_AUDIT.md)                               | TypedDict usage audit     | Reference |

---

## Getting Started

| Document                                            | Purpose              | Time Required | Status |
| --------------------------------------------------- | -------------------- | ------------- | ------ |
| [Quick Start Guide](getting-started/QUICK_START.md) | 5-minute setup       | 5 min         | Active |
| [Docker Setup](getting-started/DOCKER_SETUP.md)     | Container deployment | 15 min        | Active |

**Target Audience**: New users, operators
**Prerequisites**: Python 3.10+, Poetry, Docker (optional)

---

## API Documentation

### Core API Docs

| Document                                      | Version | Status | Audience      |
| --------------------------------------------- | ------- | ------ | ------------- |
| [API README](api/README.md)                   | 1.0.0   | Active | API Consumers |
| [API Getting Started](api/GETTING_STARTED.md) | 1.0     | Active | Developers    |
| [Sweep Results API](api/SWEEP_RESULTS_API.md) | 1.0     | Active | API Users     |
| [API Data Flow](api/API_DATA_FLOW.md)         | 1.0     | Active | Architects    |
| [Integration Guide](api/INTEGRATION_GUIDE.md) | 1.0     | Active | Integrators   |

### API Specialized

| Document                                  | Purpose               | Status |
| ----------------------------------------- | --------------------- | ------ |
| [SSE Proxy Guide](api/SSE_PROXY_GUIDE.md) | Server-Sent Events    | Active |
| [Logging Guide](api/LOGGING_GUIDE.md)     | API logging patterns  | Active |
| [Migration Notes](api/MIGRATION_NOTES.md) | API version migration | Active |

### API Examples

**Location**: `api/examples/`
**Contents**: Code examples, integration scripts, workflow demonstrations

---

## Development Documentation

### Core Development Guides

| Document                                                            | Version | Status | Audience   |
| ------------------------------------------------------------------- | ------- | ------ | ---------- |
| [Development Guide](development/DEVELOPMENT_GUIDE.md)               | 2.0     | Active | Developers |
| [Code Quality](development/CODE_QUALITY.md)                         | 2.0     | Active | Developers |
| [Code Quality Improvement](development/CODE_QUALITY_IMPROVEMENT.md) | 1.0     | Active | Developers |
| [SSH Guide](development/SSH_GUIDE.md)                               | 1.0     | Active | DevOps     |
| [AI Assistant Guide](development/AI_ASSISTANT_GUIDE.md)             | 1.0     | Active | Developers |

**Total Development Docs**: 8 files
**Focus Areas**: Setup, standards, tools, remote development

---

## Architecture Documentation

### System Design

| Document                                                                    | Version | Status    | Audience               |
| --------------------------------------------------------------------------- | ------- | --------- | ---------------------- |
| [System Architecture](architecture/SYSTEM_ARCHITECTURE.md)                  | 3.0     | Active    | Architects, Developers |
| [Data Loader Extraction](architecture/data_loader_extraction_summary.md)    | 1.0     | Reference | Architects             |
| [Formatter Extraction](architecture/formatter_extraction_summary.md)        | 1.0     | Reference | Architects             |
| [Refactoring Results](architecture/refactoring_integration_test_results.md) | 1.0     | Reference | QA                     |

**Key Concepts**:

- Dependency Injection framework
- Event-driven architecture
- Service decomposition patterns
- Clean architecture principles

---

## Testing Documentation

### Core Testing Guides

| Document                                                    | Version | Status | Audience       |
| ----------------------------------------------------------- | ------- | ------ | -------------- |
| [Testing Best Practices](testing/TESTING_BEST_PRACTICES.md) | 2.1     | Active | Developers, QA |
| [TDD Guidelines](testing/TDD_GUIDELINES.md)                 | 2.0     | Active | Developers     |
| [TDD Workflow](testing/DEVELOPER_TDD_WORKFLOW.md)           | 1.0     | Active | Developers     |
| [Test Organization](testing/TEST_ORGANIZATION.md)           | 1.5     | Active | QA Team        |

### Specialized Testing

| Document                                                              | Purpose             | Status |
| --------------------------------------------------------------------- | ------------------- | ------ |
| [Test Suite Overview](testing/TEST_SUITE_OVERVIEW.md)                 | Suite architecture  | Active |
| [Test Architecture Details](testing/TEST_ARCHITECTURE_DETAILS.md)     | Technical details   | Active |
| [API Test Guide](testing/API_TEST_GUIDE.md)                           | API testing         | Active |
| [Integration Test Guide](testing/INTEGRATION_TEST_GUIDE.md)           | Integration testing | Active |
| [Portfolio Integration Tests](testing/PORTFOLIO_INTEGRATION_TESTS.md) | Portfolio testing   | Active |
| [Portfolio Synthesis Tests](testing/PORTFOLIO_SYNTHESIS_TESTS.md)     | Synthesis testing   | Active |

**Total Testing Docs**: 10 comprehensive guides
**Coverage**: Unit, Integration, API, E2E, Performance

---

## Reference Documentation

### Command Reference

| Document                                                        | Purpose                  | Status |
| --------------------------------------------------------------- | ------------------------ | ------ |
| [Command Reference](reference/COMMAND_REFERENCE.md)             | Complete CLI reference   | Active |
| [Data Organization](reference/DATA_ORGANIZATION.md)             | Data directory structure | Active |
| [TradingView Integration](reference/TRADINGVIEW_INTEGRATION.md) | TradingView setup        | Active |

### Specialized References

**Tools**: `reference/tools/README.md`

- Export tools
- Signal analysis
- Troubleshooting guides

**Concurrency**: `reference/concurrency/README.md`

- Concurrency analysis
- Portfolio construction
- Optimization techniques

**Strategies**: `reference/strategies/README.md`

- Strategy implementations
- Parameter guides
- Performance analysis

---

## Database Documentation

### Database Guides

| Document                                                       | Purpose          | Status    |
| -------------------------------------------------------------- | ---------------- | --------- |
| [Database README](database/README.md)                          | Overview         | Active    |
| [Schema Documentation](database/SCHEMA.md)                     | Database schema  | Active    |
| [SQL Views Guide](database/SQL_VIEWS_GUIDE.md)                 | View definitions | Active    |
| [Implementation Complete](database/IMPLEMENTATION_COMPLETE.md) | Migration status | Reference |

### Database Tracking

| Document                                                               | Purpose           |
| ---------------------------------------------------------------------- | ----------------- |
| [Changelog](database/CHANGELOG.md)                                     | Database changes  |
| [Integration Test Results](database/INTEGRATION_TEST_RESULTS.md)       | Test outcomes     |
| [Before/After Comparison](database/BEFORE_AFTER_COMPARISON.md)         | Migration impact  |
| [Output Improvements](database/OUTPUT_IMPROVEMENTS.md)                 | Performance gains |
| [Metric Types Implementation](database/METRIC_TYPES_IMPLEMENTATION.md) | Metric system     |

**Total Database Docs**: 9 files

---

## Research Documentation

### SBC DeFi Research

**Location**: `research/sbc/`
**Total Documents**: 11 whitepapers and research reports

| Document                                                                                            | Type      | Status |
| --------------------------------------------------------------------------------------------------- | --------- | ------ |
| [SBC Technical Specification](research/sbc/SBC_Technical_Specification.md)                          | Technical | Active |
| [SBC Product Specification](research/sbc/SBC_Product_Specification.md)                              | Product   | Active |
| [SBC Statistical Treasury Whitepaper](research/sbc/SBC_Statistical_Treasury_Whitepaper.md)          | Research  | Active |
| [SBC Security Analysis](research/sbc/SBC_Security_Analysis.md)                                      | Security  | Active |
| [SBC vs Bitcoin Treasury Analysis](research/sbc/SBC_vs_Bitcoin_Treasury_DeFi_Protocols_Analysis.md) | Analysis  | Active |

**Additional Research**:

- Yield curve mathematical validation
- Strategic DeFi integration roadmap
- Collateral opportunities report
- BTC monthly consistency report
- BTC 1093-day hold profitability
- POL comprehensive research report 2025

**Note**: All SBC research documents use YAML frontmatter standards.

---

## Archived Documentation

### Implementation Logs

**Location**: `archive/implementation-logs/`
**Total Logs**: 30+ session summaries
**Date Range**: 2025-10 to present

**Categories**:

- Test implementation logs
- E2E test analysis
- Webhook setup documentation
- Performance optimization
- SQL implementation
- Logging recovery
- Session summaries

**Index**: [Implementation Logs README](archive/implementation-logs/README.md)

**Purpose**: Historical record of development sessions, implementation decisions, and troubleshooting solutions.

---

## Features Documentation

| Document                                           | Purpose                       | Status |
| -------------------------------------------------- | ----------------------------- | ------ |
| [Strategy Analysis](features/STRATEGY_ANALYSIS.md) | Trading strategy capabilities | Active |

**Future Features**: Additional feature documentation as capabilities expand

---

## Logging Documentation

| Document                                  | Purpose           | Status |
| ----------------------------------------- | ----------------- | ------ |
| [Logging Guide](logging/LOGGING_GUIDE.md) | Logging framework | Active |

---

## AI/Prompts Documentation

**Location**: `ai/prompts/`

### Subdirectories

- `ai/prompts/BBLEAM/` - BBLEAM-specific prompts
- `ai/prompts/coding/` - Coding assistance prompts

**Purpose**: AI assistant templates and structured prompts for development tasks

---

## Specialized Topics

### CSV and Data Formats

| Document                                                             | Purpose                    | Status |
| -------------------------------------------------------------------- | -------------------------- | ------ |
| [CSV Schemas](csv_schemas.md)                                        | Data format specifications | Active |
| [CSV Export Phase 4 Migration](CSV_EXPORT_PHASE4_MIGRATION_GUIDE.md) | Schema migration           | Active |

### Trading Analysis

| Document                                                                     | Purpose             | Status    |
| ---------------------------------------------------------------------------- | ------------------- | --------- |
| [Monte Carlo Migration Guide](monte_carlo_migration_guide.md)                | Monte Carlo updates | Active    |
| [Portfolio Consistency Analysis](portfolio_consistency_analysis_20250530.md) | Analysis report     | Reference |
| [Bitcoin Portfolio Analysis](bitcoin_portfolio_analysis_report.md)           | BTC analysis        | Reference |
| [Investment Optimization](investment_portfolio_optimization_analysis.md)     | Optimization        | Reference |

### Specifications

| Document                                                                     | Purpose           | Status |
| ---------------------------------------------------------------------------- | ----------------- | ------ |
| [Position Sizing Specification](POSITION_SIZING_SPECIFICATION.md)            | Position sizing   | Active |
| [Position Sizing Executive Spec](Position_Sizing_Executive_Specification.md) | Executive summary | Active |
| [Equity Data Export Spec](EQUITY_DATA_EXPORT_SPECIFICATION.md)               | Export features   | Active |
| [MACD Parameter Testing Guide](MACD_PARAMETER_TESTING_USER_GUIDE.md)         | MACD parameters   | Active |

### Legacy Documentation

| Document                                                                 | Purpose               | Status    |
| ------------------------------------------------------------------------ | --------------------- | --------- |
| [Claude Commands Guide](Claude Commands Guide.md)                        | AI assistant commands | Reference |
| [VectorBT Metrics](VectorBT Metrics.md)                                  | VectorBT integration  | Reference |
| [Trading Process Optimization](Trading_Process_Optimization_Report.md)   | Process report        | Reference |
| [Trade History Executive Spec](Trade_History_Executive_Specification.md) | Trade history         | Reference |

---

## Troubleshooting Documentation

| Document                                          | Purpose           | Status |
| ------------------------------------------------- | ----------------- | ------ |
| [Common Issues](troubleshooting/COMMON_ISSUES.md) | FAQ and solutions | Active |

---

## Document Statistics

### By Category

| Category        | Document Count | Status Distribution |
| --------------- | -------------- | ------------------- |
| Getting Started | 2              | 100% Active         |
| API             | 10+            | 95% Active          |
| Development     | 8              | 100% Active         |
| Architecture    | 4              | 75% Active          |
| Testing         | 10             | 100% Active         |
| Reference       | 10+            | 90% Active          |
| Research        | 11             | 100% Active         |
| Database        | 9              | 89% Active          |
| Archive         | 30+            | 100% Reference      |
| Core            | 5              | 100% Active         |

### By Audience

| Audience      | Document Count | Primary Locations                     |
| ------------- | -------------- | ------------------------------------- |
| Developers    | 60+            | development/, testing/, architecture/ |
| API Consumers | 15+            | api/, reference/                      |
| End Users     | 10+            | getting-started/, features/           |
| Architects    | 10+            | architecture/, research/              |
| QA Engineers  | 15+            | testing/                              |
| DevOps        | 5+             | development/, getting-started/        |

### By Status

| Status    | Count | Percentage |
| --------- | ----- | ---------- |
| Active    | 95+   | 58%        |
| Reference | 40+   | 24%        |
| Archived  | 30+   | 18%        |

---

## Documentation Standards

### Frontmatter Template

```yaml
---
title: Document Title
version: X.Y
last_updated: YYYY-MM-DD
owner: Team Name
status: Active|Reference|Deprecated
audience: Primary, Secondary
---
```

**Status Values**:

- **Active** - Current, actively maintained
- **Reference** - Historical, useful reference
- **Deprecated** - To be removed or archived

### Link Standards

- **Internal**: Use relative paths `[Link](./path/to/file.md)`
- **External**: Use full URLs `[Link](https://example.com)`
- **Anchors**: Include section anchors `[Link](./file.md#section)`

---

## Maintenance Tasks

### Regular Reviews

- **Quarterly**: Update version numbers and last_updated dates
- **Monthly**: Validate all internal links
- **Continuous**: Update CHANGELOG.md with significant changes

### Audit Results (2025-10-30)

- ✅ Link Integrity: 150/161 links valid (93.2%)
- ⚠️ Outdated Markers: 9 documents flagged
- ⚠️ Broken Links: 11 identified for remediation
- ✅ Frontmatter: Applied to 5+ core documents

### Known Issues

1. **Broken Links** (11 total):

   - Missing performance guide reference
   - Incorrect INDEX.md paths
   - Missing RUFF_REFERENCE.md
   - Missing API_REFERENCE.md
   - Missing DEBUGGING.md
   - Missing webhook implementation docs

2. **Documentation Gaps**:
   - ROADMAP.md (referenced but doesn't exist)
   - Some migration guides incomplete
   - Ruff reference guide needed

---

## Contributing to Documentation

1. **Follow frontmatter standards** for new documents
2. **Update README.md** when adding major sections
3. **Maintain link integrity** - validate after changes
4. **Update CHANGELOG.md** for significant updates
5. **Follow audience-based organization**

**Documentation Contribution Workflow**:

1. Create/update documentation
2. Add proper frontmatter
3. Update navigation files (README.md, DOCUMENTATION_INDEX.md)
4. Validate links
5. Update CHANGELOG.md
6. Submit for review

---

## Quick Links

### Most Frequently Accessed

1. [User Manual](USER_MANUAL.md) - Comprehensive system guide
2. [API Documentation](api/README.md) - API reference
3. [Development Guide](development/DEVELOPMENT_GUIDE.md) - Dev setup
4. [Testing Best Practices](testing/TESTING_BEST_PRACTICES.md) - Testing standards
5. [System Architecture](architecture/SYSTEM_ARCHITECTURE.md) - Architecture overview

### For New Team Members

1. [Quick Start Guide](getting-started/QUICK_START.md)
2. [Development Guide](development/DEVELOPMENT_GUIDE.md)
3. [Code Quality](development/CODE_QUALITY.md)
4. [Testing Best Practices](testing/TESTING_BEST_PRACTICES.md)
5. [API Getting Started](api/GETTING_STARTED.md)

---

**Navigation**: [Main README](README.md) | [Changelog](CHANGELOG.md) | [User Manual](USER_MANUAL.md)

**Last Updated**: 2025-10-30
**Maintained By**: Documentation Team
**Auto-Generated**: This index is manually maintained. Last audit: 2025-10-30
