import sys

import pkg_resources

print("Python version:", sys.version)

installed_packages = pkg_resources.working_set
installed_packages_list = sorted(
    ["%s==%s" % (i.key, i.version) for i in installed_packages]
)

print("\nInstalled packages:")
for package in installed_packages_list:
    print(package)

print("\nTrying to import riskfolio:")
try:
    import riskfolio as rp

    print("Riskfolio imported successfully")
    print("Riskfolio version:", rp.__version__)
except ImportError as e:
    print("Failed to import riskfolio:", str(e))
except AttributeError as e:
    print("Riskfolio imported, but couldn't get version:", str(e))

print("\nPython path:")
for path in sys.path:
    print(path)
