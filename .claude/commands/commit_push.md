# Commit and Push

Generate a meaningful commit title, create the commit, and push to remote.

## Steps

1. **Stage All Changes**: Add all changes to staging area using `git add -A`
2. **Analyze Changes**: Review git status and diff to understand what has changed
3. **Generate Title**: Create a concise, descriptive commit message that explains the purpose of the changes
4. **Commit**: Create the commit with the generated message
5. **Push**: Push the commit to the remote repository

## Usage

This command will:
- Automatically stage ALL changed files using `git add -A` at the beginning
- Generate an appropriate commit message based on the changes
- Create the commit with Claude Code attribution
- Push the changes to the remote repository

## Notes

- Stages ALL files in the repository using `git add -A` command
- This includes new files, modified files, and deleted files
- Includes proper attribution in commit message
- Handles pre-commit hooks if they modify files
- Be cautious as this will stage everything, including potentially sensitive files