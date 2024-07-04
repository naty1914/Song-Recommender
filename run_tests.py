import unittest
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '.')))

loader = unittest.TestLoader()
tests = loader.discover('tests')
testRunner = unittest.runner.TextTestRunner()
testRunner.run(tests)
