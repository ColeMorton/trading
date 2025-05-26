# Commit and Push

Generate a meaningful commit title, create the commit, and push to remote.

## Steps

1. **Analyze Changes**: Review git status and diff to understand what has changed
2. **Generate Title**: Create a concise, descriptive commit message that explains the purpose of the changes
3. **Stage Changes**: Add relevant files to staging area
4. **Commit**: Create the commit with the generated message
5. **Push**: Push the commit to the remote repository

## Usage

This command will:
- Automatically stage relevant changed files
- Generate an appropriate commit message based on the changes
- Create the commit with Claude Code attribution
- Push the changes to the remote repository

## Notes

- Only stages files that are relevant to the current changes
- Skips sensitive or temporary files
- Includes proper attribution in commit message
- Handles pre-commit hooks if they modify files