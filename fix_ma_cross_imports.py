#!/usr/bin/env python3
"""Fix import statements in app/strategies/ma_cross directory."""

import os
from pathlib import Path


def fix_imports_in_file(file_path: Path) -> bool:
    """Fix imports in a single file. Returns True if file was modified."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check if the file contains the old import pattern
        if 'from app.ma_cross' not in content:
            return False
        
        # Replace the import statements
        new_content = content.replace('from app.ma_cross', 'from app.strategies.ma_cross')
        
        # Write back only if content changed
        if new_content != content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
            return True
        
        return False
    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        return False


def main():
    """Main function to process all Python files."""
    # Define the target directory
    target_dir = Path('app/strategies/ma_cross')
    
    if not target_dir.exists():
        print(f"Error: Directory {target_dir} does not exist!")
        return
    
    # Find all Python files recursively
    python_files = list(target_dir.rglob('*.py'))
    
    if not python_files:
        print(f"No Python files found in {target_dir}")
        return
    
    print(f"Found {len(python_files)} Python files in {target_dir}")
    print("-" * 50)
    
    # Process each file
    updated_files = []
    for file_path in python_files:
        if fix_imports_in_file(file_path):
            updated_files.append(file_path)
            print(f"✓ Updated: {file_path}")
    
    # Report results
    print("-" * 50)
    print("\nSummary:")
    print(f"Total files scanned: {len(python_files)}")
    print(f"Files updated: {len(updated_files)}")
    
    if updated_files:
        print("\nUpdated files:")
        for file_path in updated_files:
            print(f"  - {file_path}")
    else:
        print("\nNo files needed updating.")


if __name__ == "__main__":
    main()