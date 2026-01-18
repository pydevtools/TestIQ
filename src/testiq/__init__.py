"""
TestIQ - Intelligent Test Analysis

Find duplicate and redundant tests using coverage analysis.
"""

__version__ = "0.2.2"

from testiq.analyzer import CoverageData, CoverageDuplicateFinder

__all__ = ["CoverageDuplicateFinder", "CoverageData", "__version__"]
