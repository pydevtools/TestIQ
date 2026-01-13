"""
TestIQ - Intelligent Test Analysis

Find duplicate and redundant tests using coverage analysis.
"""

__version__ = "0.1.0"

from testiq.analyzer import CoverageDuplicateFinder, TestCoverage

__all__ = ["CoverageDuplicateFinder", "TestCoverage", "__version__"]
