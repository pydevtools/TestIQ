#!/bin/bash
# Complete TestIQ Analysis - Get both coverage metrics and duplicate detection
# Usage: ./run_complete_analysis.sh [test_directory]

set -e  # Exit on error

TEST_DIR="${1:-tests/}"
COVERAGE_FILE="coverage.json"
TESTIQ_FILE="testiq_coverage.json"
REPORT_DIR="reports"

echo ""
echo "╔═══════════════════════════════════════════════════════════════════════════════╗"
echo "║                  TestIQ Complete Analysis Runner                              ║"
echo "╚═══════════════════════════════════════════════════════════════════════════════╝"
echo ""

# Step 1: Run tests with coverage measurement
echo "📊 Step 1/3: Measuring code coverage..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
pytest "$TEST_DIR" \
  --cov=src/testiq \
  --cov-report=term \
  --cov-report=json \
  --cov-report=html \
  -q

echo ""
echo "✓ Coverage report saved to: htmlcov/index.html"
echo ""

# Step 2: Run tests with TestIQ plugin for per-test coverage
echo "🔍 Step 2/3: Collecting per-test coverage data..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
pytest "$TEST_DIR" \
  --testiq-output="$TESTIQ_FILE" \
  -q

echo ""

# Step 3: Run TestIQ analysis
echo "🎯 Step 3/3: Analyzing for duplicate tests..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
mkdir -p "$REPORT_DIR"

testiq analyze "$TESTIQ_FILE" \
  --format html \
  --output "$REPORT_DIR/duplicate_analysis.html"

testiq quality-score "$TESTIQ_FILE" | tee "$REPORT_DIR/quality_score.txt"

echo ""
echo "╔═══════════════════════════════════════════════════════════════════════════════╗"
echo "║                           ✅ Analysis Complete!                                ║"
echo "╚═══════════════════════════════════════════════════════════════════════════════╝"
echo ""
echo "📊 Reports Generated:"
echo "   • Coverage Report:      htmlcov/index.html"
echo "   • Duplicate Analysis:   $REPORT_DIR/duplicate_analysis.html"
echo "   • Quality Score:        $REPORT_DIR/quality_score.txt"
echo ""
echo "🚀 Open reports:"
echo "   open htmlcov/index.html"
echo "   open $REPORT_DIR/duplicate_analysis.html"
echo ""
