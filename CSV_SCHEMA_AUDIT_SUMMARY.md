# CSV Schema Audit Summary - Phase 2 Migration Planning

## Executive Summary

The comprehensive audit of 277 CSV files across the project reveals significant schema inconsistencies that require immediate attention for Phase 2 migration. While 36.1% of files are compliant, the majority (177 files) require schema standardization.

## Key Findings

### 1. Overall Statistics

- **Total files analyzed**: 277
- **Compliant files**: 100 (36.1%)
- **Non-compliant files**: 177 (63.9%)
- **Error files**: 0 (excellent data integrity)

### 2. Directory-Specific Analysis

#### csv/portfolios/ (Base Schema Expected - 58 columns)

- **Files**: 107 total, 0 compliant (0%)
- **Primary Issues**:
  - 105 files incorrectly detected as Extended schema (have `Allocation [%]` and `Stop Loss [%]` columns)
  - 8 files have 60 columns instead of 58
  - 3 files have 59 columns
  - 1 file has only 57 columns
  - 1 file has only 24 columns (malformed)

#### csv/portfolios_filtered/ (Filtered Schema Expected - 61 columns)

- **Files**: 58 total, 0 compliant (0%)
- **Primary Issues**:
  - All files correctly detected as Filtered schema but audit was misconfigured
  - 50 files have 59 columns (missing 2 columns from complete filtered schema)
  - 8 files have correct 61 columns

#### csv/portfolios_best/ (Filtered Schema Expected - 61 columns)

- **Files**: 12 total, 0 compliant (0%)
- **Primary Issues**:
  - 7 files have 59 columns (Extended schema)
  - 5 files have severely reduced columns (21-24 columns) - these appear to be summary files
  - Significant schema variation suggesting different purposes/formats

#### csv/strategies/ (Mixed Schema Expected - Variable)

- **Files**: 100 total, 100 compliant (100%)
- **Status**: No issues - correctly identified as mixed schema with variable column counts

## Schema Type Analysis

### Current Distribution:

- **Base Schema**: 58 files (strategies only)
- **Extended Schema**: 130 files (portfolios with allocation/stop-loss)
- **Filtered Schema**: 59 files (with Metric Type column)
- **Unknown Schema**: 30 files (malformed or special purpose)

### Expected vs Actual:

1. **csv/portfolios/** should be Base (58 cols) but most are Extended (58-60 cols)
2. **csv/portfolios_filtered/** should be Filtered (61 cols) but many are incomplete (59 cols)
3. **csv/portfolios_best/** should be Filtered (61 cols) but has mixed formats

## Critical Migration Issues

### 1. Schema Misalignment

- **Root Cause**: Portfolio files in `csv/portfolios/` contain Extended schema columns (`Allocation [%]`, `Stop Loss [%]`) when they should be Base schema
- **Impact**: 105 files incorrectly classified

### 2. Incomplete Filtered Schema

- **Root Cause**: Files in `csv/portfolios_filtered/` missing required columns for complete Filtered schema
- **Impact**: 50 files with 59 columns instead of 61

### 3. Portfolio Best Format Inconsistency

- **Root Cause**: Multiple distinct formats in `csv/portfolios_best/` including summary-style files
- **Impact**: 5 files with dramatically reduced column counts (21-24)

### 4. Column Count Variations

- **58 columns**: 131 files (mix of actual Base and Extended without optional columns)
- **59 columns**: 57 files (incomplete schemas)
- **60 columns**: 8 files (Extended with partial columns)
- **61 columns**: 8 files (complete Filtered schema)

## Migration Priority Recommendations

### **Priority 1: HIGH - csv/portfolios/ (107 files)**

**Issue**: Schema type mismatch - files contain Extended schema elements but directory expects Base schema

**Recommended Actions**:

1. **Decision Required**: Determine if `csv/portfolios/` should contain:

   - Option A: Pure Base schema (remove `Allocation [%]` and `Stop Loss [%]` columns)
   - Option B: Change expectation to Extended schema (update directory purpose)

2. **If Option A (Base Schema)**:

   - Remove `Allocation [%]` and `Stop Loss [%]` columns from all 105 files
   - Validate remaining files have exactly 58 columns
   - Fix malformed files (1 file with 24 columns, 1 with 57)

3. **If Option B (Extended Schema)**:
   - Update audit expectations
   - Standardize all files to 60 columns (Extended schema)
   - Add missing columns where needed

### **Priority 2: MEDIUM - csv/portfolios_best/ (12 files)**

**Issue**: Severe format inconsistency and purpose unclear

**Recommended Actions**:

1. **Clarify Purpose**: Determine if these are:

   - Filtered schema files (need 61 columns)
   - Summary files (different schema acceptable)
   - Mixed purpose directory

2. **If Filtered Schema Target**:

   - Migrate 7 Extended files to Filtered (add `Metric Type` column)
   - Address 5 summary files (migrate or relocate)

3. **If Summary Files Acceptable**:
   - Create separate subdirectories for different formats
   - Document schema variations

### **Priority 3: MEDIUM - csv/portfolios_filtered/ (58 files)**

**Issue**: Incomplete Filtered schema - missing columns

**Recommended Actions**:

1. **Complete Filtered Schema**:

   - Add missing columns to 50 files with 59 columns
   - Likely missing: `Alpha`, `Beta`, or other extended metrics
   - Validate 8 complete files as template

2. **Column Mapping**:
   - Identify specific missing columns via comparison with complete files
   - Implement systematic column addition with appropriate defaults

## Technical Implementation Notes

### Schema Detection Works Correctly

- The SchemaTransformer from Phase 1 correctly identifies schema types
- Issues are primarily in directory organization and completeness, not detection

### Data Integrity Excellent

- Zero error files encountered
- All files readable and processable
- Issues are structural, not data corruption

### Standardization Feasible

- Clear patterns in schema variations
- Systematic approach can resolve most issues
- Existing tools (SchemaTransformer) support migration

## Next Steps for Phase 2

1. **Stakeholder Decision**: Clarify intended schema for each directory
2. **Migration Strategy**: Develop automated migration scripts using SchemaTransformer
3. **Validation Framework**: Create ongoing compliance monitoring
4. **Documentation**: Update schema specifications based on decisions
5. **Testing**: Validate migrations maintain data integrity and functionality

## Files Generated

- **Detailed Report**: `/Users/colemorton/Projects/trading/csv_schema_audit_report.md`
- **Raw Data**: `/Users/colemorton/Projects/trading/csv_schema_audit_results.json`
- **Audit Tool**: `/Users/colemorton/Projects/trading/csv_schema_audit.py`

This audit provides the foundation for systematic CSV schema standardization in Phase 2.
