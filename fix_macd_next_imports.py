#!/usr/bin/env python3
"""
Script to fix import statements in app/strategies/macd_next directory.
Replaces 'from app.macd_next' with 'from app.strategies.macd_next'
"""

import os
import re
from pathlib import Path


def fix_imports_in_file(file_path: Path) -> int:
    """Fix imports in a single Python file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Pattern to match 'from app.macd_next' imports
        pattern = r'from app\.macd_next'
        replacement = r'from app.strategies.macd_next'
        
        # Count replacements
        matches = len(re.findall(pattern, content))
        
        if matches > 0:
            # Perform replacement
            new_content = re.sub(pattern, replacement, content)
            
            # Write back to file
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
            
            print(f"Fixed {matches} imports in: {file_path}")
        
        return matches
    
    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        return 0


def main():
    """Main function to process all Python files."""
    # Define the target directory
    target_dir = Path("app/strategies/macd_next")
    
    if not target_dir.exists():
        print(f"Directory {target_dir} does not exist!")
        return
    
    total_files = 0
    total_replacements = 0
    
    # Find all Python files in the directory
    for py_file in target_dir.rglob("*.py"):
        total_files += 1
        replacements = fix_imports_in_file(py_file)
        total_replacements += replacements
    
    print("\nSummary:")
    print(f"Files processed: {total_files}")
    print(f"Total replacements: {total_replacements}")


if __name__ == "__main__":
    main()