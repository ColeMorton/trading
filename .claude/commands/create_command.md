# Create Command

Create a new Claude Code command with proper structure and best practices.

## Purpose

This command guides you through creating new Claude Code commands with consistent structure, proper formatting, and adherence to best practices. It provides an interactive workflow that ensures all created commands follow the established patterns and include necessary documentation.

## Workflow

### Step 1: Gather Command Information
Ask the user for:
- **Command name**: Validate it doesn't already exist and follows naming conventions
- **Command purpose**: Clear, concise description of what the command does
- **Command type**: Choose from workflow, automation, analysis, or utility
- **Primary use case**: Specific scenario where this command would be used

### Step 2: Define Command Structure
Based on the command type, guide the user through:
- **Core steps**: Main actions the command should perform
- **Parameters**: Any arguments or inputs the command needs
- **Prerequisites**: Dependencies or setup required
- **Expected outputs**: What the command should produce

### Step 3: Create Command Content
Generate the command file with:
- Proper markdown structure following existing patterns
- Clear step-by-step instructions
- Usage examples with `/project:command-name` syntax
- Best practices and notes sections
- Parameter documentation if applicable

### Step 4: Validation and Preview
Before saving:
- Check that command name doesn't conflict with existing commands
- Validate markdown structure and formatting
- Show preview of the generated command
- Allow user to make adjustments if needed

### Step 5: Save and Confirm
- Write the command file to `.claude/commands/` directory
- Provide usage instructions
- Suggest testing the new command

## Template Structure

Use this template structure for all created commands:

```markdown
# [Command Name]

[Brief description of what the command does]

## Purpose

[Detailed explanation of the command's purpose and when to use it]

## Workflow

### Step 1: [First Action]
[Detailed description of what to do]

### Step 2: [Second Action]
[Detailed description of what to do]

[Continue with additional steps as needed]

## Usage

Invoke this command with:
```
/project:[command-name]
```

[Include any parameter examples if applicable]

## Parameters

- `$ARGUMENTS`: [Description of any arguments the command accepts]

## Best Practices

- [Guideline 1]
- [Guideline 2]
- [Additional best practices]

## Notes

- [Important considerations]
- [Warnings or limitations]
- [Additional context]
```

## Command Type Templates

### Workflow Commands
Focus on step-by-step processes with clear sequence and decision points.

### Automation Commands
Emphasize repeatable tasks with minimal user intervention.

### Analysis Commands
Include research, investigation, and reporting steps.

### Utility Commands
Provide specific tools or helpers for common tasks.

## Validation Rules

1. **Command Name**:
   - Must be lowercase with underscores or hyphens
   - Cannot conflict with existing commands
   - Should be descriptive and concise

2. **Structure**:
   - Must include Purpose, Workflow, and Usage sections
   - Steps should be numbered and detailed
   - Include examples where applicable

3. **Content Quality**:
   - Clear, actionable instructions
   - Proper markdown formatting
   - Consistent with existing command patterns

## Usage

Invoke this command with:
```
/project:create_command
```

This will start an interactive session to create a new command.

## Best Practices

- Start with the specific need or problem the command solves
- Keep commands focused on a single responsibility
- Use clear, actionable language in steps
- Include examples and usage patterns
- Test the command after creation
- Follow DRY, SOLID, KISS, and YAGNI principles

## Notes

- Commands are stored in `.claude/commands/` directory
- Command files must have `.md` extension
- Once created, commands are immediately available for use
- Always test new commands before relying on them
- Consider documenting complex commands in the project's command guide