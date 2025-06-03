import inspect

import riskfolio as rp

print("Available attributes in riskfolio module:")
for name, obj in inspect.getmembers(rp):
    if not name.startswith("_"):  # Exclude private attributes
        print(f"{name}: {type(obj)}")

print("\nAvailable classes in riskfolio module:")
for name, obj in inspect.getmembers(rp):
    if inspect.isclass(obj):
        print(f"{name}")

print("\nAvailable functions in riskfolio module:")
for name, obj in inspect.getmembers(rp):
    if inspect.isfunction(obj):
        print(f"{name}")

# Try to access some common classes or functions
common_names = ["Portfolio", "HCPortfolio", "RiskFunctions", "ParamsEstimation"]
for name in common_names:
    try:
        obj = getattr(rp, name)
        print(f"\nFound {name}:")
        print(f"Type: {type(obj)}")
        if inspect.isclass(obj):
            print("Methods:")
            for method_name, method_obj in inspect.getmembers(obj):
                if inspect.isfunction(method_obj) and not method_name.startswith("_"):
                    print(f"  - {method_name}")
    except AttributeError:
        print(f"\n{name} not found in riskfolio module")
