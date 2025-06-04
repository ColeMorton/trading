# Create Command

Interactive command creator for Claude Code with systematic validation and best practices.

## Purpose

Creates well-structured commands following established patterns with built-in validation and optimization guidance.

## Workflow

### Step 1: Command Definition
**Required Information:**
- **Name**: lowercase, descriptive, unique (validate against existing)
- **Category**: workflow | automation | analysis | utility
- **Objective**: specific problem solved (1-2 sentences)
- **Success criteria**: measurable outcomes

### Step 2: Structure Design
**Core Components:**
- **Prerequisites**: dependencies, setup requirements
- **Parameters**: inputs with types and validation
- **Process steps**: sequential actions with decision points
- **Outputs**: expected results and formats
- **Error handling**: failure modes and recovery

### Step 3: Content Generation
**Template Application:**
```markdown
# [Command Name]

[One-line description]

## Purpose
[Problem solved and when to use - 2-3 sentences]

## Parameters
- `param`: description (type, required/optional, default)

## Process
1. **[Action]**: [specific steps]
2. **[Validation]**: [check criteria]
3. **[Output]**: [deliverable format]

## Usage
```
/project:[command-name] [parameters]
```

## Notes
- [Critical considerations]
- [Limitations or warnings]
```

### Step 4: Quality Assurance
**Validation Checklist:**
- [ ] Name follows conventions and is unique
- [ ] Purpose clearly states value proposition
- [ ] Steps are actionable and measurable
- [ ] Parameters are well-defined
- [ ] Examples demonstrate usage
- [ ] Error cases are addressed

### Step 5: Implementation
- Write to `.claude/commands/[name].md`
- Test with sample parameters
- Document in command registry

## Command Categories

**Workflow**: Multi-step processes with decision points
**Automation**: Repeatable tasks requiring minimal input
**Analysis**: Research, investigation, and reporting tasks
**Utility**: Specific tools for common operations

## Quality Standards

**Clarity**: Each step has clear success criteria
**Completeness**: All necessary information included
**Consistency**: Follows established patterns
**Actionability**: Instructions are executable
**Robustness**: Handles edge cases and errors

## Validation Rules

1. **Naming**: `[a-z0-9_-]+` pattern, max 20 chars
2. **Structure**: Required sections present and complete
3. **Content**: Specific, actionable instructions
4. **Examples**: Realistic usage scenarios included
5. **Testing**: Command works as documented

## Usage

```
/project:create_command
```

Starts interactive command creation session with systematic guidance and validation.

## Best Practices

- Start with user need, not technical capability
- Use action verbs for clarity
- Include realistic examples
- Plan for failure scenarios
- Test before deployment
- Document assumptions and limitations