import sys


print(f"Python version: {sys.version}")
print(f"Python executable: {sys.executable}")

try:
    import riskfolio as rp

    print("Successfully imported riskfolio")
    print(
        f"Riskfolio version: {rp.__version__ if hasattr(rp, '__version__') else 'Unknown'}",
    )
    print("Riskfolio contents:")
    print(dir(rp))
except ImportError as e:
    print(f"Failed to import riskfolio: {e}")
    print("Installed packages:")
    import pkg_resources

    installed_packages = pkg_resources.working_set
    installed_packages_list = sorted(
        [f"{i.key}=={i.version}" for i in installed_packages],
    )
    for package in installed_packages_list:
        print(package)
