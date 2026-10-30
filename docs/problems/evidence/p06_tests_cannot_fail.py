"""P06: most tests cannot fail, and pytest collects only 2 tests."""
import subprocess, sys
from common import *

print("A) what pytest collects from src/tests")
out = subprocess.run([sys.executable, "-m", "pytest", "--collect-only", "-q", "src/tests"],
                     cwd=ROOT, capture_output=True, text=True).stdout
print("   " + "\n   ".join(out.strip().splitlines()))

print("\nB) ConfiguratorTest with a deliberately WRONG config value")
from src.utils.Configurator import Configurator
from src.tests.ConfiguratorTest import TestConfigurator
Configurator.fetchData = lambda self, t: dict(camera_index="WRONG", combined_width=0,
                                              combined_height=0, preview_width=0)
try:
    TestConfigurator().test_load_camera_config()
    print("   -> returned normally: the test run would still end with 'All tests completed.' and exit code 0")
except AssertionError:
    print("   -> raised (test can fail)")
