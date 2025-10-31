#!/usr/bin/env python3
"""
Find pure unit test candidates from remaining test files.
"""

import re
from pathlib import Path


# Patterns that indicate external dependencies
EXTERNAL_DEPS = [
    r"TestClient",
    r"db_session",
    r"@patch",
    r"@mock",
    r"Mock\(",
    r"MagicMock",
    r"requests\.",
    r"httpx\.",
    r"AsyncClient",
    r"\.get\(",  # HTTP get
    r"\.post\(",  # HTTP post
]


def has_external_deps(filepath: Path) -> bool:
    """Check if file has external dependencies."""
    try:
        content = filepath.read_text()
        return any(re.search(pattern, content) for pattern in EXTERNAL_DEPS)
    except Exception:
        return True  # Assume has deps if can't read


def count_tests(filepath: Path) -> int:
    """Count test functions in file."""
    try:
        content = filepath.read_text()
        return len(re.findall(r"^\s*def test_", content, re.MULTILINE))
    except Exception:
        return 0


def main():
    test_root = Path("tests")

    # Find all test files not in unit/integration/e2e
    all_tests = []
    for test_file in test_root.rglob("test_*.py"):
        if any(
            p in test_file.parts for p in ["unit", "integration", "e2e", "__pycache__"]
        ):
            continue
        all_tests.append(test_file)

    # Analyze each file
    pure_tests = []
    for test_file in all_tests:
        if not has_external_deps(test_file):
            count = count_tests(test_file)
            if count > 0:
                pure_tests.append((count, test_file))

    # Sort by test count
    pure_tests.sort(reverse=True)

    # Print results
    print(
        f"Found {len(pure_tests)} pure test files with {sum(c for c, _ in pure_tests)} tests\n"
    )
    print("Top candidates:")
    print("-" * 80)

    total = 0
    for count, filepath in pure_tests[:50]:
        rel_path = filepath.relative_to(Path())
        print(f"{count:3d}  {rel_path}")
        total += count

    if len(pure_tests) > 50:
        remaining = sum(c for c, _ in pure_tests[50:])
        print(f"\n... and {len(pure_tests) - 50} more files with {remaining} tests")

    print(f"\nTotal in top 50: {total} tests")


if __name__ == "__main__":
    main()
