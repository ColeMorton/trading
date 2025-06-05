# CSV Schema Standardization Implementation Plan

_Systems Architecture Document_

## Executive Summary

<summary>
  <objective>Standardize all CSV export functionality to use the 59-column reference schema as the single source of truth</objective>
  <approach>Systematic migration from multiple schemas (14-column, 58-column, 59-column) to unified 59-column standard with comprehensive validation</approach>
  <value>100% schema consistency, elimination of data discrepancies, improved API reliability, and enhanced data analysis capabilities</value>
</summary>

## Architecture Design

### Current State Analysis

**Schema Variants Identified:**

1. **14-Column API Schema** (`app/api/routers/ma_cross.py`) - Simplified export for web interface
2. **58-Column Base Schema** - Raw portfolio analysis without `Metric Type` column
3. **59-Column Extended Schema** - Complete schema with `Metric Type` classification (REFERENCE STANDARD)

**Critical Discrepancies:**

- Column name inconsistency: `Expectancy per Trade` vs `Expectancy (per trade)`
- Missing 45 columns in API exports (risk metrics, trade analysis, extended fields)
- Multiple export paths generating different schemas
- No centralized schema validation

### Target State Architecture

**Unified 59-Column Standard:**

```
Ticker, Allocation [%], Strategy Type, Short Window, Long Window, Signal Window, Stop Loss [%],
Signal Entry, Signal Exit, Total Open Trades, Total Trades, Metric Type, Score, Win Rate [%],
Profit Factor, Expectancy per Trade, Sortino Ratio, Beats BNH [%], Avg Trade Duration,
Trades Per Day, Trades per Month, Signals per Month, Expectancy per Month, Start, End, Period,
Start Value, End Value, Total Return [%], Benchmark Return [%], Max Gross Exposure [%],
Total Fees Paid, Max Drawdown [%], Max Drawdown Duration, Total Closed Trades, Open Trade PnL,
Best Trade [%], Worst Trade [%], Avg Winning Trade [%], Avg Losing Trade [%],
Avg Winning Trade Duration, Avg Losing Trade Duration, Expectancy, Sharpe Ratio, Calmar Ratio,
Omega Ratio, Skew, Kurtosis, Tail Ratio, Common Sense Ratio, Value at Risk, Daily Returns,
Annual Returns, Cumulative Returns, Annualized Return, Annualized Volatility, Signal Count,
Position Count, Total Period
```

**Transformation Path:**

1. Establish 59-column schema as canonical reference
2. Update all export functions to use unified schema validation
3. Migrate API endpoints to full schema support
4. Implement comprehensive testing and validation
5. Remove deprecated schema variants

## Implementation Phases

<phase number="1" estimated_effort="2 days">
  <objective>Establish Schema Foundation and Validation Framework</objective>
  <scope>
    Included: Schema validation utilities, reference schema definition, validation testing
    Excluded: Actual migration of export functions (Phase 2)
  </scope>
  <dependencies>Access to test data, understanding of current schema detection logic</dependencies>

  <implementation>
    <step>Create canonical 59-column schema definition in `app/tools/portfolio/canonical_schema.py`</step>
    <step>Implement schema validation functions with comprehensive column and type checking</step>
    <step>Create test fixtures with reference data for validation testing</step>
    <validation>Unit tests for schema validation, integration tests with sample data</validation>
    <rollback>Isolated utilities with no impact on existing exports</rollback>
  </implementation>

  <deliverables>
    <deliverable>Canonical schema definition class with column ordering and type specifications</deliverable>
    <deliverable>Schema validation utility functions with detailed error reporting</deliverable>
    <deliverable>Comprehensive test suite for schema validation</deliverable>
  </deliverables>

  <risks>
    <risk>Incomplete understanding of data types → Analyze existing CSV files for type patterns</risk>
    <risk>Schema complexity causing performance issues → Optimize validation for production use</risk>
  </risks>

<completion_summary>
<status>✅ COMPLETED - 2024-01-06</status>
<files_created>
<file>app/tools/portfolio/canonical_schema.py - Authoritative 59-column schema definition</file>
<file>app/tools/portfolio/schema_validation.py - Comprehensive validation functions</file>
<file>tests/fixtures/schema_validation_fixtures.py - Test data and fixtures</file>
<file>tests/test_schema_validation.py - Complete test suite with 100+ test cases</file>
</files_created>
<features_implemented>
<feature>CanonicalPortfolioSchema class with 59 column definitions and type specifications</feature>
<feature>SchemaValidator with strict/lenient modes and detailed error reporting</feature>
<feature>Comprehensive validation covering column count, order, types, and required fields</feature>
<feature>Batch validation functions for multiple CSV files</feature>
<feature>Human-readable compliance report generation</feature>
<feature>Test fixtures with 7 different validation scenarios</feature>
</features_implemented>
<testing_results>
<result>✅ All validation tests pass successfully</result>
<result>✅ Reference CSV files validated as compliant with canonical schema</result>
<result>✅ Error detection working for missing columns, wrong order, and type mismatches</result>
<result>✅ Performance tested with large DataFrames (1000+ rows)</result>
</testing_results>
<known_issues>
<issue>None - Phase 1 completed successfully with all deliverables</issue>
</known_issues>
<next_steps>
<step>Proceed to Phase 2: Update Core Export Infrastructure</step>
<step>Apply schema validation to stats_converter.py and export_csv.py</step>
<step>Ensure all CSV exports generate compliant 59-column outputs</step>
</next_steps>
</completion_summary>
</phase>

<phase number="2" estimated_effort="3 days">
  <objective>Update Core Export Infrastructure</objective>
  <scope>
    Included: stats_converter.py, export_csv.py, portfolio schema utilities
    Excluded: API endpoints (Phase 3), strategy-specific exports (Phase 4)
  </scope>
  <dependencies>Phase 1 completion, understanding of data transformation pipeline</dependencies>

  <implementation>
    <step>Update `stats_converter.py` to ensure all 59 columns are generated with proper naming</step>
    <step>Enhance `export_csv.py` to include schema validation before export</step>
    <step>Update `schema_detection.py` to standardize on 59-column extended schema</step>
    <step>Modify `export/formats.py` to enforce canonical schema</step>
    <validation>Integration tests with existing portfolio data, schema compliance verification</validation>
    <rollback>Maintain backward compatibility through feature flags</rollback>
  </implementation>

  <deliverables>
    <deliverable>Updated stats conversion ensuring all 59 columns are properly generated</deliverable>
    <deliverable>Enhanced export functions with mandatory schema validation</deliverable>
    <deliverable>Unified schema detection supporting only extended format</deliverable>
  </deliverables>

  <risks>
    <risk>Breaking existing data pipelines → Implement progressive rollout with validation</risk>
    <risk>Performance degradation from validation → Optimize validation algorithms</risk>
  </risks>

<completion_summary>
<status>✅ COMPLETED - 2024-01-06</status>
<files_modified>
<file>app/tools/stats_converter.py - Added canonical schema compliance function and 59-column enforcement</file>
<file>app/tools/export_csv.py - Integrated schema validation and automatic compliance enforcement</file>
<file>app/tools/portfolio/schema_detection.py - Updated to target canonical schema with migration logic</file>
<file>app/tools/export/formats.py - Enhanced CSVExporter with canonical schema validation</file>
</files_modified>
<features_implemented>
<feature>Canonical schema compliance in stats_converter with automatic column ordering</feature>
<feature>Pre-export schema validation and enforcement in export_csv.py</feature>
<feature>Enhanced schema detection supporting CANONICAL schema version</feature>
<feature>Unified data transformation pipeline to canonical 59-column format</feature>
<feature>Automatic missing column population with appropriate defaults</feature>
<feature>Legacy function preservation for backward compatibility</feature>
</features_implemented>
<testing_results>
<result>✅ Schema validation test: PASS - Real portfolio file (59/59 columns)</result>
<result>✅ Export test: PASS - Minimal data automatically expanded to 59 columns</result>
<result>✅ Schema enforcement: 3 input columns → 59 canonical columns with defaults</result>
<result>✅ Integration test: All core export infrastructure validated</result>
</testing_results>
<known_issues>
<issue>None - All core export infrastructure successfully migrated to canonical schema</issue>
</known_issues>
<next_steps>
<step>Proceed to Phase 3: Fix API Export Schema Compliance</step>
<step>Update ma_cross.py API router to use canonical schema</step>
<step>Replace 14-column hardcoded schema with full 59-column exports</step>
</next_steps>
</completion_summary>
</phase>

<phase number="3" estimated_effort="1 day">
  <objective>Fix API Export Schema Compliance</objective>
  <scope>
    Included: ma_cross.py API router, export endpoint updating
    Excluded: Other API endpoints that may exist (discovered in testing)
  </scope>
  <dependencies>Phase 2 completion, understanding of API data flow</dependencies>

  <implementation>
    <step>Replace hardcoded 14-column schema in `app/api/routers/ma_cross.py` with canonical 59-column schema</step>
    <step>Update `export_results_to_best` function to use full data transformation pipeline</step>
    <step>Fix column name from "Expectancy (per trade)" to "Expectancy per Trade"</step>
    <step>Integrate with updated export infrastructure from Phase 2</step>
    <validation>API endpoint testing, CSV output validation, frontend compatibility checks</validation>
    <rollback>Revert to original endpoint with feature flag for new behavior</rollback>
  </implementation>

  <deliverables>
    <deliverable>Updated API export endpoint using full 59-column schema</deliverable>
    <deliverable>Consistent column naming across all export paths</deliverable>
    <deliverable>API integration tests validating schema compliance</deliverable>
  </deliverables>

  <risks>
    <risk>Frontend incompatibility with expanded schema → Coordinate with frontend team</risk>
    <risk>API response size increase → Implement compression if needed</risk>
  </risks>
</phase>

<phase number="4" estimated_effort="2 days">
  <objective>Validate Strategy-Specific Exports</objective>
  <scope>
    Included: All strategy export modules, cross-strategy validation
    Excluded: Historical data migration (Phase 5)
  </scope>
  <dependencies>Phase 3 completion, access to strategy execution pipelines</dependencies>

  <implementation>
    <step>Audit all strategy export functions for schema compliance</step>
    <step>Update strategy-specific export utilities to use canonical schema</step>
    <step>Validate portfolio orchestrator export coordination</step>
    <step>Test cross-strategy aggregation with unified schema</step>
    <validation>End-to-end strategy execution with CSV validation, multi-strategy portfolio generation</validation>
    <rollback>Strategy-specific rollback with individual export function restoration</rollback>
  </implementation>

  <deliverables>
    <deliverable>Validated strategy export compliance across all strategies</deliverable>
    <deliverable>Updated portfolio orchestrator with schema enforcement</deliverable>
    <deliverable>Cross-strategy integration test suite</deliverable>
  </deliverables>

  <risks>
    <risk>Strategy-specific data requirements not captured in canonical schema → Extend schema as needed</risk>
    <risk>Performance impact on strategy execution → Optimize export operations</risk>
  </risks>
</phase>

<phase number="5" estimated_effort="1 day">
  <objective>Implement Comprehensive Testing and Documentation</objective>
  <scope>
    Included: Full system testing, documentation updates, migration guides
    Excluded: None - comprehensive completion phase
  </scope>
  <dependencies>Phases 1-4 completion, access to full test environment</dependencies>

  <implementation>
    <step>Execute comprehensive end-to-end testing across all export paths</step>
    <step>Validate schema consistency across all CSV output directories</step>
    <step>Update documentation reflecting new standardized schema</step>
    <step>Create migration guide for any external consumers</step>
    <validation>Full regression testing, schema compliance verification, performance benchmarking</validation>
    <rollback>Complete system rollback plan with phase-by-phase restoration</rollback>
  </implementation>

  <deliverables>
    <deliverable>Complete test suite validating 59-column schema across all exports</deliverable>
    <deliverable>Updated documentation with canonical schema specification</deliverable>
    <deliverable>Migration guide for external systems consuming CSV exports</deliverable>
    <deliverable>Performance benchmarking report showing impact of changes</deliverable>
  </deliverables>

  <risks>
    <risk>Undiscovered integration points → Comprehensive system scanning for CSV usage</risk>
    <risk>Performance regression → Optimization and rollback procedures</risk>
  </risks>
</phase>

## Risk Mitigation Strategy

### Technical Risks

- **Schema Evolution Complexity**: Implement gradual migration with validation checkpoints
- **Data Pipeline Disruption**: Maintain parallel export paths during migration
- **Performance Degradation**: Optimize validation algorithms and implement caching
- **Integration Breaking**: Comprehensive testing with rollback procedures

### Operational Risks

- **Frontend Compatibility**: Coordinate schema changes with frontend development
- **External Dependencies**: Document schema changes for external consumers
- **Data Loss Prevention**: Implement backup and recovery procedures
- **Testing Coverage**: Ensure comprehensive test coverage across all export paths

## Success Metrics

### Validation Criteria

- **Schema Consistency**: 100% of CSV exports use 59-column canonical schema
- **Column Naming**: Consistent naming across all export paths (`Expectancy per Trade`)
- **Data Completeness**: All 59 columns populated with appropriate data or null values
- **API Compliance**: API endpoints export full schema data
- **Performance**: Export performance within 5% of baseline
- **Test Coverage**: 95%+ test coverage for export functionality

### Quality Gates

- **Phase Completion**: Each phase must pass comprehensive validation before proceeding
- **Rollback Readiness**: Rollback procedures tested and documented for each phase
- **Integration Testing**: End-to-end validation with real data at each phase
- **Performance Benchmarking**: Performance impact measured and documented

## Implementation Timeline

**Phase 1 (Schema Foundation)**: Days 1-2
**Phase 2 (Core Infrastructure)**: Days 3-5
**Phase 3 (API Compliance)**: Day 6
**Phase 4 (Strategy Validation)**: Days 7-8
**Phase 5 (Testing & Documentation)**: Day 9

**Total Duration**: 9 days with 20% buffer for unexpected complexity

---

_This implementation plan follows SOLID, DRY, KISS, and YAGNI principles while ensuring comprehensive standardization of CSV export functionality across the entire trading platform._
