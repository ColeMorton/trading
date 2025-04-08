import os
import riskfolio

# Get the directory of the riskfolio package
riskfolio_dir = os.path.dirname(riskfolio.__file__)

print(f"Riskfolio package directory: {riskfolio_dir}")

# List all files in the riskfolio directory
print("\nFiles in the riskfolio package directory:")
for root, dirs, files in os.walk(riskfolio_dir):
    level = root.replace(riskfolio_dir, '').count(os.sep)
    indent = ' ' * 4 * level
    print(f"{indent}{os.path.basename(root)}/")
    sub_indent = ' ' * 4 * (level + 1)
    for file in files:
        print(f"{sub_indent}{file}")

# Try to import specific modules
modules_to_check = ['Portfolio', 'HCPortfolio', 'RiskFunctions', 'ParamsEstimation']

print("\nTrying to import specific modules:")
for module in modules_to_check:
    try:
        exec(f"from riskfolio import {module}")
        print(f"Successfully imported {module}")
    except ImportError as e:
        print(f"Failed to import {module}: {e}")

# Check if there's an __init__.py file and print its contents
init_file = os.path.join(riskfolio_dir, '__init__.py')
if os.path.exists(init_file):
    print("\nContents of __init__.py:")
    with open(init_file, 'r') as f:
        print(f.read())
else:
    print("\n__init__.py file not found in the riskfolio package directory")
