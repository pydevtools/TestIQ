"""
TestIQ - Intelligent Test Analysis

Find duplicate and redundant tests using coverage analysis.
"""

__version__ = "0.2.0"

from testiq.analyzer import CoverageDuplicateFinder, CoverageData

__all__ = ["CoverageDuplicateFinder", "CoverageData", "__version__"]
