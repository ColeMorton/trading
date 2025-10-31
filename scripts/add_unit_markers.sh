#!/bin/bash
# Add @pytest.mark.unit to all test classes in specified files

for file in "$@"; do
    echo "Processing $file..."

    # Check if pytest is already imported
    if ! grep -q "^import pytest" "$file"; then
        # Find the first import line and add pytest import after it
        sed -i '' '/^import /a\
import pytest
' "$file"
    fi

    # Add @pytest.mark.unit before all class Test definitions
    sed -i '' 's/^class Test/@pytest.mark.unit\
class Test/g' "$file"

    echo "  ✓ Added markers to $file"
done

echo "Done!"
