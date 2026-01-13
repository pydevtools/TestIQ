"""
Advanced reporting formats for TestIQ.
Generates HTML, CSV, and enhanced reports.
"""

import csv
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from testiq.analyzer import CoverageDuplicateFinder
from testiq.logging_config import get_logger

logger = get_logger(__name__)


class HTMLReportGenerator:
    """Generate beautiful HTML reports with charts and styling."""

    def __init__(self, finder: CoverageDuplicateFinder) -> None:
        """Initialize HTML report generator."""
        self.finder = finder

    def generate(
        self,
        output_path: Path,
        title: str = "TestIQ Analysis Report",
        threshold: float = 0.7,
    ) -> None:
        """
        Generate HTML report.

        Args:
            output_path: Path to save HTML file
            title: Report title
            threshold: Similarity threshold for analysis
        """
        logger.info(f"Generating HTML report: {output_path}")

        exact_dups = self.finder.find_exact_duplicates()
        subset_dups = self.finder.find_subset_duplicates()
        similar = self.finder.find_similar_coverage(threshold)

        html = self._generate_html(title, exact_dups, subset_dups, similar, threshold)

        output_path.write_text(html)
        logger.info(f"HTML report saved: {output_path}")

    def _generate_html(
        self,
        title: str,
        exact_dups: list[list[str]],
        subset_dups: list[tuple[str, str, float]],
        similar: list[tuple[str, str, float]],
        threshold: float,
    ) -> str:
        """Generate HTML content."""
        total_tests = len(self.finder.tests)
        duplicate_count = sum(len(g) - 1 for g in exact_dups)

        # Calculate statistics
        duplicate_percentage = (
            (duplicate_count / total_tests * 100) if total_tests > 0 else 0
        )

        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            line-height: 1.6;
            color: #333;
            background: #f5f7fa;
            padding: 20px;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 8px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            padding: 40px;
        }}
        h1 {{
            color: #2c3e50;
            margin-bottom: 10px;
            font-size: 2.5em;
        }}
        .timestamp {{
            color: #7f8c8d;
            font-size: 0.9em;
            margin-bottom: 30px;
        }}
        .stats {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 40px;
        }}
        .stat-card {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }}
        .stat-card.success {{
            background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        }}
        .stat-card.warning {{
            background: linear-gradient(135deg, #fa709a 0%, #fee140 100%);
        }}
        .stat-card.info {{
            background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
        }}
        .stat-value {{
            font-size: 2.5em;
            font-weight: bold;
            margin-bottom: 5px;
        }}
        .stat-label {{
            font-size: 0.9em;
            opacity: 0.9;
        }}
        h2 {{
            color: #2c3e50;
            margin-top: 40px;
            margin-bottom: 20px;
            padding-bottom: 10px;
            border-bottom: 3px solid #667eea;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-bottom: 30px;
            background: white;
        }}
        th {{
            background: #667eea;
            color: white;
            padding: 12px;
            text-align: left;
            font-weight: 600;
        }}
        td {{
            padding: 12px;
            border-bottom: 1px solid #ecf0f1;
        }}
        tr:hover {{
            background: #f8f9fa;
        }}
        .badge {{
            display: inline-block;
            padding: 4px 12px;
            border-radius: 12px;
            font-size: 0.85em;
            font-weight: 600;
        }}
        .badge-danger {{
            background: #fee;
            color: #c33;
        }}
        .badge-warning {{
            background: #ffeaa7;
            color: #d63031;
        }}
        .badge-info {{
            background: #dfe6e9;
            color: #2d3436;
        }}
        .test-group {{
            background: #f8f9fa;
            padding: 15px;
            border-radius: 6px;
            margin-bottom: 15px;
            border-left: 4px solid #667eea;
        }}
        .test-name {{
            font-family: 'Courier New', monospace;
            font-size: 0.9em;
            background: #ecf0f1;
            padding: 2px 6px;
            border-radius: 3px;
        }}
        .action {{
            color: #27ae60;
            font-weight: 600;
        }}
        .footer {{
            margin-top: 60px;
            padding-top: 20px;
            border-top: 1px solid #ecf0f1;
            text-align: center;
            color: #7f8c8d;
            font-size: 0.9em;
        }}
        .progress-bar {{
            height: 30px;
            background: #ecf0f1;
            border-radius: 15px;
            overflow: hidden;
            margin: 20px 0;
        }}
        .progress-fill {{
            height: 100%;
            background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-weight: 600;
            transition: width 0.3s ease;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🧪 {title}</h1>
        <div class="timestamp">Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</div>
        
        <div class="stats">
            <div class="stat-card">
                <div class="stat-value">{total_tests}</div>
                <div class="stat-label">Total Tests</div>
            </div>
            <div class="stat-card success">
                <div class="stat-value">{duplicate_count}</div>
                <div class="stat-label">Duplicates Found</div>
            </div>
            <div class="stat-card warning">
                <div class="stat-value">{len(subset_dups)}</div>
                <div class="stat-label">Subset Duplicates</div>
            </div>
            <div class="stat-card info">
                <div class="stat-value">{len(similar)}</div>
                <div class="stat-label">Similar Pairs</div>
            </div>
        </div>

        <div class="progress-bar">
            <div class="progress-fill" style="width: {duplicate_percentage:.1f}%">
                {duplicate_percentage:.1f}% Duplicates
            </div>
        </div>

        <h2>🎯 Exact Duplicates</h2>
        <p>Tests with identical code coverage that can be safely removed.</p>
"""

        if exact_dups:
            for i, group in enumerate(exact_dups, 1):
                html += f"""
        <div class="test-group">
            <strong>Group {i}</strong> <span class="badge badge-danger">{len(group)} tests</span>
            <ul style="margin-top: 10px; margin-left: 20px;">
"""
                for test in group:
                    html += f'                <li><span class="test-name">{test}</span></li>\n'
                html += f"""            </ul>
            <div class="action">→ Remove {len(group) - 1} duplicate(s)</div>
        </div>
"""
        else:
            html += '        <p style="color: #27ae60;">✓ No exact duplicates found!</p>\n'

        html += """
        <h2>📊 Subset Duplicates</h2>
        <p>Tests that are subsets of other tests and may be redundant.</p>
"""

        if subset_dups:
            html += """
        <table>
            <thead>
                <tr>
                    <th>Subset Test</th>
                    <th>Superset Test</th>
                    <th>Coverage Ratio</th>
                </tr>
            </thead>
            <tbody>
"""
            for subset_test, superset_test, ratio in subset_dups[:20]:
                html += f"""                <tr>
                    <td><span class="test-name">{subset_test}</span></td>
                    <td><span class="test-name">{superset_test}</span></td>
                    <td><span class="badge badge-warning">{ratio:.1%}</span></td>
                </tr>
"""
            html += """            </tbody>
        </table>
"""
        else:
            html += '        <p style="color: #27ae60;">✓ No subset duplicates found!</p>\n'

        html += f"""
        <h2>🔍 Similar Tests (≥{threshold:.0%} overlap)</h2>
        <p>Test pairs with significant code coverage overlap.</p>
"""

        if similar:
            html += """
        <table>
            <thead>
                <tr>
                    <th>Test 1</th>
                    <th>Test 2</th>
                    <th>Similarity</th>
                </tr>
            </thead>
            <tbody>
"""
            for test1, test2, similarity in similar[:20]:
                html += f"""                <tr>
                    <td><span class="test-name">{test1}</span></td>
                    <td><span class="test-name">{test2}</span></td>
                    <td><span class="badge badge-info">{similarity:.1%}</span></td>
                </tr>
"""
            html += """            </tbody>
        </table>
"""
        else:
            html += '        <p style="color: #27ae60;">✓ No similar tests found!</p>\n'

        html += f"""
        <div class="footer">
            <p>Generated by <strong>TestIQ</strong> - Intelligent Test Analysis</p>
            <p>🔗 <a href="https://github.com/testiq-dev/testiq" style="color: #667eea;">github.com/testiq-dev/testiq</a></p>
        </div>
    </div>
</body>
</html>
"""
        return html


class CSVReportGenerator:
    """Generate CSV reports for data analysis and spreadsheets."""

    def __init__(self, finder: CoverageDuplicateFinder) -> None:
        """Initialize CSV report generator."""
        self.finder = finder

    def generate_exact_duplicates(self, output_path: Path) -> None:
        """Generate CSV of exact duplicates."""
        logger.info(f"Generating exact duplicates CSV: {output_path}")

        exact_dups = self.finder.find_exact_duplicates()

        with open(output_path, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["Group", "Test Name", "Action"])

            for i, group in enumerate(exact_dups, 1):
                for j, test in enumerate(group):
                    action = "Keep" if j == 0 else "Remove"
                    writer.writerow([f"Group {i}", test, action])

        logger.info(f"CSV report saved: {output_path}")

    def generate_subset_duplicates(self, output_path: Path) -> None:
        """Generate CSV of subset duplicates."""
        logger.info(f"Generating subset duplicates CSV: {output_path}")

        subsets = self.finder.find_subset_duplicates()

        with open(output_path, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["Subset Test", "Superset Test", "Coverage Ratio", "Action"])

            for subset_test, superset_test, ratio in subsets:
                writer.writerow(
                    [
                        subset_test,
                        superset_test,
                        f"{ratio:.2%}",
                        "Review for removal",
                    ]
                )

        logger.info(f"CSV report saved: {output_path}")

    def generate_similar_tests(self, output_path: Path, threshold: float = 0.7) -> None:
        """Generate CSV of similar tests."""
        logger.info(f"Generating similar tests CSV: {output_path}")

        similar = self.finder.find_similar_coverage(threshold)

        with open(output_path, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["Test 1", "Test 2", "Similarity", "Action"])

            for test1, test2, similarity in similar:
                writer.writerow(
                    [test1, test2, f"{similarity:.2%}", "Review for merge"]
                )

        logger.info(f"CSV report saved: {output_path}")

    def generate_summary(self, output_path: Path, threshold: float = 0.7) -> None:
        """Generate summary CSV with all data."""
        logger.info(f"Generating summary CSV: {output_path}")

        exact_dups = self.finder.find_exact_duplicates()
        subsets = self.finder.find_subset_duplicates()
        similar = self.finder.find_similar_coverage(threshold)

        with open(output_path, "w", newline="") as f:
            writer = csv.writer(f)

            # Summary statistics
            writer.writerow(["Metric", "Value"])
            writer.writerow(["Total Tests", len(self.finder.tests)])
            writer.writerow(
                ["Exact Duplicates", sum(len(g) - 1 for g in exact_dups)]
            )
            writer.writerow(["Subset Duplicates", len(subsets)])
            writer.writerow(["Similar Test Pairs", len(similar)])
            writer.writerow([])

            # Exact duplicates section
            writer.writerow(["EXACT DUPLICATES"])
            writer.writerow(["Group", "Test Name", "Action"])
            for i, group in enumerate(exact_dups, 1):
                for j, test in enumerate(group):
                    action = "Keep" if j == 0 else "Remove"
                    writer.writerow([f"Group {i}", test, action])
            writer.writerow([])

            # Subset duplicates section
            writer.writerow(["SUBSET DUPLICATES"])
            writer.writerow(["Subset Test", "Superset Test", "Coverage Ratio"])
            for subset_test, superset_test, ratio in subsets[:50]:
                writer.writerow([subset_test, superset_test, f"{ratio:.2%}"])
            writer.writerow([])

            # Similar tests section
            writer.writerow(["SIMILAR TESTS"])
            writer.writerow(["Test 1", "Test 2", "Similarity"])
            for test1, test2, similarity in similar[:50]:
                writer.writerow([test1, test2, f"{similarity:.2%}"])

        logger.info(f"CSV report saved: {output_path}")
