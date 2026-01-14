#!/bin/bash
# Example: TestIQ Quick Test Script
# Run this to test all main features quickly
#
# Usage from examples/bash:
#   ./quick_test.sh
# Or from project root:
#   bash examples/bash/quick_test.sh
#
# Latest Features Tested:
# - Enhanced quality scoring with refactored recommendation engine
# - Improved code quality (reduced cognitive complexity)
# - Better constant management and maintainability
# - pytest integration (now included in dependencies)

set -e  # Exit on error

# Determine project root (works from examples/bash or project root)
if [ -f "pyproject.toml" ]; then
    PROJECT_ROOT="."
else
    PROJECT_ROOT="../.."
fi

# Navigate to project root
cd "$PROJECT_ROOT"

# Create reports directory
mkdir -p reports

echo "🧪 TestIQ Quick Test Suite"
echo "=" | tr '=' '=' | head -c 50; echo

# 1. Demo
echo "1️⃣  Running demo..."
testiq demo | head -20
echo "✅ Demo complete"
echo

# 2. Basic analysis
echo "2️⃣  Basic analysis..."
testiq analyze examples/sample_coverage.json | head -30
echo "✅ Analysis complete"
echo

# 3. Quality score
echo "3️⃣  Quality scoring..."
testiq quality-score examples/sample_coverage.json | head -20
echo "✅ Quality score complete"
echo

# 4. HTML report
echo "4️⃣  Generating HTML report..."
testiq analyze examples/sample_coverage.json --format html --output reports/quick_report.html
echo "✅ HTML report: reports/quick_report.html"
echo

# 5. Quality gate
echo "5️⃣  Testing quality gate..."
testiq analyze examples/sample_coverage.json --quality-gate --max-duplicates 5 > /dev/null 2>&1
if [ $? -eq 0 ]; then
    echo "✅ Quality gate: PASSED"
else
    echo "⚠️  Quality gate: FAILED (expected for demo data)"
fi
echo

# 6. Baseline
echo "6️⃣  Baseline management..."
testiq analyze examples/sample_coverage.json --save-baseline test-baseline > /dev/null 2>&1
testiq baseline list
echo "✅ Baseline saved"
echo

# 7. Python API
echo "7️⃣  Testing Python API..."
python examples/python/manual_test.py | grep "✓" | head -10
echo "✅ Python API working"
echo

echo "=" | tr '=' '=' | head -c 50; echo
echo "🎉 All quick tests completed!"
echo
echo "📊 Generated files in reports/:"
ls -lh reports/*.html reports/*.csv reports/*.md 2>/dev/null | awk '{print "  •", $9}' || echo "  (run full tests to generate reports)"
echo
echo "🚀 Next steps:"
echo "  • Open reports/quick_report.html in browser"
echo "  • Run: python manual_test.py"
echo "  • Read: docs/manual-testing.md"
