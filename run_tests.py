#!/usr/bin/env python
"""Run all tests for DevPulse."""

import unittest

if __name__ == "__main__":
    # Discover and run all tests
    test_suite = unittest.defaultTestLoader.discover("tests")
    test_runner = unittest.TextTestRunner(verbosity=2)
    test_runner.run(test_suite)