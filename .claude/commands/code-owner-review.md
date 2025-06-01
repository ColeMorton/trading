# Code Owner Review

Perform a comprehensive codebase review from a code owner's perspective, analyzing architecture, technical debt, risks, and providing strategic recommendations.

## Purpose

This command guides you through a systematic review of the codebase as a code owner would perform it. It examines architectural integrity, identifies technical debt, assesses risks, evaluates technology choices, and provides actionable recommendations for maintaining and evolving the codebase. This review is essential for periodic health checks, onboarding, and strategic planning.

## Workflow

### Step 1: Architectural Analysis
Review the overall codebase structure and architecture:
- Examine directory structure and module organization
- Identify architectural patterns and their consistency
- Check for proper separation of concerns
- Evaluate coupling and cohesion between modules
- Document any architectural anti-patterns or violations

### Step 2: Documentation Audit
Assess the state of documentation:
- Review README files and getting started guides
- Check for architectural decision records (ADRs)
- Evaluate inline code documentation and comments
- Verify API documentation completeness
- Identify missing or outdated documentation

### Step 3: Technical Debt Assessment
Identify and categorize technical debt:
- Find code duplication and DRY violations
- Locate overly complex functions or modules
- Identify outdated dependencies or deprecated patterns
- Check for incomplete implementations or TODOs
- Assess test coverage and quality

### Step 4: Risk Identification
Analyze potential risks in the codebase:
- Security vulnerabilities or unsafe practices
- Performance bottlenecks or inefficiencies
- Single points of failure
- Scalability limitations
- Dependency risks (outdated, unmaintained packages)

### Step 5: Technology Stack Evaluation
Review the technology choices:
- Assess if current technologies meet project needs
- Identify opportunities for modernization
- Check for consistent use of libraries and frameworks
- Evaluate build and deployment tooling
- Consider emerging technologies that could benefit the project

### Step 6: Code Quality Analysis
Examine code quality metrics:
- Review coding standards compliance
- Check error handling patterns
- Evaluate logging and monitoring implementation
- Assess configuration management
- Review testing strategies and coverage

### Step 7: Strategic Recommendations
Compile findings into actionable recommendations:
- Prioritize technical debt items by impact and effort
- Suggest architectural improvements
- Recommend documentation updates
- Propose technology migrations or upgrades
- Create a roadmap for addressing identified issues

### Step 8: Generate Summary Report
Create a comprehensive report including:
- Executive summary of key findings
- Detailed analysis by category
- Risk matrix with severity ratings
- Prioritized action items
- Timeline recommendations
- Resource requirements for improvements

## Usage

Invoke this command with:
```
/project:code-owner-review
```

## Parameters

- `$ARGUMENTS`: Optional focus area (e.g., "security", "performance", "architecture") to prioritize specific aspects of the review

## Best Practices

- Perform this review quarterly or before major feature additions
- Use objective metrics where possible (test coverage, complexity scores)
- Balance criticism with recognition of good practices
- Focus on actionable recommendations rather than just problems
- Consider both immediate fixes and long-term improvements
- Involve team members to get different perspectives
- Document all findings for future reference

## Notes

- This review should be thorough but time-boxed to remain practical
- Focus on systemic issues rather than minor code style violations
- Consider the project's maturity and resources when making recommendations
- Use automated tools where available to support manual analysis
- The review should guide strategic decisions, not create busywork
- Remember that perfect is the enemy of good - prioritize high-impact improvements