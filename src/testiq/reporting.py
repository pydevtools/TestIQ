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
from testiq.source_reader import SourceCodeReader

logger = get_logger(__name__)


class HTMLReportGenerator:
    """Generate beautiful HTML reports with charts and styling."""

    def __init__(self, finder: CoverageDuplicateFinder) -> None:
        """Initialize HTML report generator."""
        self.finder = finder

    def _build_coverage_data_js(self) -> str:
        """Build JavaScript code to populate coverage data."""
        # Group lines by file
        file_coverage = {}
        for test in self.finder.tests:
            for filename, line in test.covered_lines:
                if filename not in file_coverage:
                    file_coverage[filename] = {'lines': set(), 'tests': set()}
                file_coverage[filename]['lines'].add(line)
                file_coverage[filename]['tests'].add(test.test_name)
        
        # Build JS code
        js_lines = []
        for filename, data in sorted(file_coverage.items()):
            lines_count = len(data['lines'])
            tests_count = len(data['tests'])
            js_lines.append(f"coverageByFile[{json.dumps(filename)}] = {{lines: {lines_count}, tests: {tests_count}}};")
        
        return '\n        '.join(js_lines)

    def generate(
        self,
        output_path: Path,
        title: str = "TestIQ Analysis Report",
        threshold: float = 0.3,
    ) -> None:
        """
        Generate HTML report.

        Args:
            output_path: Path to save HTML file
            title: Report title
            threshold: Similarity threshold for analysis (default: 0.3 = 30%)
        """
        from testiq import __version__

        logger.info(f"Generating HTML report: {output_path}")
        logger.info(f"  Threshold: {threshold:.1%}")
        logger.info(f"  Total tests: {len(self.finder.tests)}")

        exact_dups = self.finder.find_exact_duplicates()
        subset_dups = self.finder.get_sorted_subset_duplicates()  # Use sorted version
        similar = self.finder.find_similar_coverage(threshold)
        duplicate_count = self.finder.get_duplicate_count()

        logger.info(f"  Exact duplicate groups: {len(exact_dups)} ({duplicate_count} tests)")
        logger.info(f"  Subset duplicates: {len(subset_dups)}")
        logger.info(f"  Similar pairs: {len(similar)}")

        html = self._generate_html(title, exact_dups, subset_dups, similar, threshold)

        output_path.write_text(html)
        logger.info(f"HTML report saved: {output_path}")

    def _prepare_coverage_data(
        self,
    ) -> tuple[dict[str, dict[int, str]], set[tuple[str, int]], float]:
        """
        Collect and analyze source files for coverage display.
        
        Returns:
            Tuple of (source_code_map, unique_lines_covered, coverage_percentage)
        """
        source_reader = SourceCodeReader()
        all_files = set()
        unique_lines_covered = set()
        
        for test in self.finder.tests:
            for filename, line in test.covered_lines:
                all_files.add(filename)
                unique_lines_covered.add((filename, line))
        
        source_code_map = source_reader.read_multiple(list(all_files))
        
        total_lines_in_files = sum(len(lines) for lines in source_code_map.values())
        lines_covered = len(unique_lines_covered)
        coverage_percentage = (lines_covered / total_lines_in_files * 100) if total_lines_in_files > 0 else 0
        
        return source_code_map, unique_lines_covered, coverage_percentage

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
        duplicate_count = self.finder.get_duplicate_count()
        
        # Collect and read source files for the split-screen view
        source_code_map, unique_lines_covered, coverage_percentage = self._prepare_coverage_data()

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
            max-width: 1600px;
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
            background: linear-gradient(135deg, #4a5568 0%, #2d3748 100%);
            color: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            cursor: pointer;
            transition: transform 0.2s ease, box-shadow 0.2s ease;
        }}
        .stat-card:hover {{
            transform: translateY(-3px);
            box-shadow: 0 6px 12px rgba(0,0,0,0.15);
        }}
        .stat-card.danger {{
            background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        }}
        .stat-card.success {{
            background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
        }}
        .stat-card.warning {{
            background: linear-gradient(135deg, #f7971e 0%, #ffd200 100%);
        }}
        .stat-card.info {{
            background: linear-gradient(135deg, #00c6ff 0%, #0072ff 100%);
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
            border-bottom: 3px solid #00c6ff;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-bottom: 30px;
            background: white;
        }}
        th {{
            background: #00c6ff;
            color: white;
            padding: 12px;
            text-align: left;
            font-weight: 600;
        }}
        td {{
            padding: 12px;
            border-bottom: 1px solid #ecf0f1;
            word-break: break-word;
            overflow-wrap: break-word;
            max-width: 400px;
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
            border-left: 4px solid #00c6ff;
        }}
        .test-name {{
            font-family: 'Courier New', monospace;
            font-size: 0.9em;
            background: #ecf0f1;
            padding: 2px 6px;
            border-radius: 3px;
            display: inline-block;
            max-width: 100%;
            line-height: 1.6;
        }}
        .test-name .test-part {{
            display: inline;
        }}
        .test-name .test-separator {{
            color: #3498db;
            font-weight: bold;
            margin: 0 2px;
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
        .clickable-row {{
            cursor: pointer;
            transition: all 0.2s ease;
        }}
        .clickable-row:hover {{
            background: #e8f4f8 !important;
            transform: translateX(3px);
        }}
        .modal {{
            display: none;
            position: fixed;
            z-index: 1000;
            left: 0;
            top: 0;
            width: 100%;
            height: 100%;
            background-color: rgba(0,0,0,0.7);
            animation: fadeIn 0.3s;
        }}
        .modal-content {{
            background-color: white;
            margin: 10px auto;
            padding: 0;
            width: calc(100% - 20px);
            height: calc(100vh - 20px);
            border-radius: 8px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.3);
            display: flex;
            flex-direction: column;
            overflow: hidden;
        }}
        .modal-header {{
            padding: 20px;
            background: linear-gradient(135deg, #00c6ff 0%, #764ba2 100%);
            color: white;
            border-radius: 8px 8px 0 0;
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-shrink: 0;
        }}
        .close {{
            color: white;
            font-size: 32px;
            font-weight: bold;
            cursor: pointer;
            line-height: 1;
            transition: transform 0.2s;
        }}
        .close:hover {{
            transform: scale(1.2);
        }}
        .split-view {{
            display: flex;
            flex: 1;
            overflow-y: auto;
            overflow-x: hidden;
            min-height: 0;
        }}
        .split-view.independent {{
            overflow: hidden;
        }}
        .file-panel {{
            flex: 1;
            display: flex;
            flex-direction: column;
            border-right: 2px solid #ecf0f1;
            min-width: 0;
        }}
        .file-panel.independent {{
            overflow-y: auto;
        }}
        .file-panel:last-child {{
            border-right: none;
        }}
        .panel-header {{
            padding: 15px;
            background: #f8f9fa;
            border-bottom: 2px solid #ecf0f1;
            font-weight: 600;
            color: #2c3e50;
            position: sticky;
            top: 0;
            z-index: 10;
            flex-shrink: 0;
        }}
        .file-content {{
            padding: 20px;
            font-family: 'Courier New', monospace;
            font-size: 0.9em;
            line-height: 1.8;
            background: #fafafa;
        }}
        .code-line {{
            padding: 2px 8px;
            border-radius: 3px;
            margin: 1px 0;
            white-space: pre;
        }}
        .covered-both {{
            background: #c8e6c9;
            border-left: 3px solid #4caf50;
            font-weight: 600;
        }}
        .covered-single {{
            background: #fff9c4;
            border-left: 3px solid #fbc02d;
            font-weight: 500;
        }}
        .covered {{
            background: #d4edda;
            border-left: 3px solid #28a745;
            font-weight: 600;
        }}
        .not-covered {{
            opacity: 0.6;
        }}
        .file-path {{
            font-family: 'Courier New', monospace;
            font-size: 0.85em;
            color: #7f8c8d;
            font-weight: bold;
            margin-bottom: 10px;
        }}
        .coverage-info {{
            background: #e8f4f8;
            padding: 15px;
            margin: 10px 20px;
            border-left: 4px solid #00c6ff;
            border-radius: 4px;
            display: flex;
            align-items: center;
            gap: 20px;
            flex-wrap: wrap;
            flex-shrink: 0;
        }}
        .filter-section {{
            display: flex;
            align-items: center;
            gap: 5px;
        }}
        .filter-select {{
            padding: 6px 10px;
            border: 1px solid rgba(255,255,255,0.5);
            border-radius: 4px;
            font-size: 0.85em;
            background: rgba(255,255,255,0.95);
            cursor: pointer;
            min-width: 180px;
            color: #2c3e50;
        }}
        .filter-select:hover {{
            background: white;
            border-color: white;
        }}
        .sync-toggle {{
            display: flex;
            align-items: center;
            gap: 6px;
            padding: 6px 12px;
            background: rgba(255,255,255,0.95);
            border: 1px solid rgba(255,255,255,0.5);
            border-radius: 4px;
            cursor: pointer;
            transition: all 0.2s;
            font-size: 0.85em;
            color: #2c3e50;
        }}
        .sync-toggle:hover {{
            background: white;
            border-color: white;
            background: #f0f0ff;
        }}
        .sync-toggle.active {{
            background: #00c6ff;
            color: white;
        }}
        .sync-checkbox {{
            width: 18px;
            height: 18px;
            cursor: pointer;
        }}
            border-left: 4px solid #00c6ff;
            border-radius: 4px;
        }}
        @keyframes fadeIn {{
            from {{ opacity: 0; }}
            to {{ opacity: 1; }}
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
            background: linear-gradient(90deg, #00c6ff 0%, #0072ff 100%);
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-weight: 600;
            transition: width 0.3s ease;
        }}
        .tabs {{
            display: flex;
            gap: 10px;
            margin: 30px 0 20px 0;
            border-bottom: 2px solid #ecf0f1;
        }}
        .tab {{
            padding: 12px 24px;
            background: #f8f9fa;
            border: none;
            border-radius: 8px 8px 0 0;
            cursor: pointer;
            font-weight: 600;
            font-size: 16px;
            color: #7f8c8d;
            transition: all 0.3s ease;
            position: relative;
            bottom: -2px;
        }}
        .tab:hover {{
            background: #e9ecef;
            color: #495057;
        }}
        .tab.active {{
            background: white;
            color: #00c6ff;
            border-bottom: 2px solid #00c6ff;
        }}
        .tab-content {{
            display: none;
            animation: fadeIn 0.3s;
        }}
        .tab-content.active {{
            display: block;
        }}
        .pagination {{
            display: flex;
            justify-content: center;
            align-items: center;
            gap: 10px;
            margin: 20px 0;
        }}
        .pagination-controls {{
            display: flex;
            align-items: center;
            gap: 10px;
            margin-bottom: 20px;
            justify-content: space-between;
            flex-wrap: wrap;
        }}
        .page-size-selector {{
            display: flex;
            align-items: center;
            gap: 8px;
            font-size: 0.9em;
            color: #2c3e50;
        }}
        .page-size-selector label {{
            font-weight: 600;
        }}
        .page-size-selector select {{
            padding: 6px 12px;
            border: 2px solid #3498db;
            border-radius: 6px;
            background: white;
            color: #2c3e50;
            font-size: 0.9em;
            cursor: pointer;
            transition: all 0.2s ease;
        }}
        .page-size-selector select:hover {{
            border-color: #00c6ff;
            box-shadow: 0 2px 8px rgba(0, 198, 255, 0.2);
        }}
        .page-size-selector select:focus {{
            outline: none;
            border-color: #00c6ff;
            box-shadow: 0 0 0 3px rgba(0, 198, 255, 0.1);
        }}
        .page-btn {{
            padding: 8px 12px;
            background: #00c6ff;
            color: white;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            font-weight: 600;
            transition: all 0.2s ease;
        }}
        .page-btn:hover:not(:disabled) {{
            background: #0088cc;
            transform: translateY(-2px);
        }}
        .page-btn:disabled {{
            background: #bdc3c7;
            cursor: not-allowed;
            opacity: 0.6;
        }}
        .page-info {{
            color: #7f8c8d;
            font-weight: 600;
        }}
        .loading {{
            text-align: center;
            padding: 20px;
            color: #00c6ff;
        }}
        .spinner {{
            border: 3px solid #f3f3f3;
            border-top: 3px solid #00c6ff;
            border-radius: 50%;
            width: 40px;
            height: 40px;
            animation: spin 1s linear infinite;
            margin: 20px auto;
        }}
        @keyframes spin {{
            0% {{ transform: rotate(0deg); }}
            100% {{ transform: rotate(360deg); }}
        }}
        
        /* Responsive: Hide text on small screens, keep only icon */
        @media (max-width: 768px) {{
            .view-coverage-text {{
                display: none;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🧪 {title}</h1>
        <div class="timestamp">Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</div>
        
        <div class="stats">
            <div class="stat-card" onclick="switchTab('exact')">
                <div class="stat-value">{total_tests}</div>
                <div class="stat-label">Total Test Methods</div>
            </div>
            <div class="stat-card danger" onclick="switchTab('exact')">
                <div class="stat-value">{duplicate_count}</div>
                <div class="stat-label">Duplicates</div>
            </div>
            <div class="stat-card info" onclick="switchTab('similar')">
                <div class="stat-value">{len(similar)}</div>
                <div class="stat-label">Similar Test Pairs</div>
            </div>
            <div class="stat-card warning" onclick="switchTab('subset')">
                <div class="stat-value">{len(subset_dups)}</div>
                <div class="stat-label">Subset Duplicates</div>
            </div>
        </div>



        <div class="tabs">
            <button class="tab active" onclick="switchTab('exact')">🎯 Exact Duplicates ({len(exact_dups)})</button>
            <button class="tab" onclick="switchTab('similar')">🔍 Similar Tests ({len(similar)})</button>
            <button class="tab" onclick="switchTab('subset')">📊 Subset Duplicates ({len(subset_dups)})</button>
        </div>

        <div id="exact-content" class="tab-content active">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
                <h2 style="margin: 0;">🎯 Exact Duplicates</h2>
                <div style="display: flex; align-items: center; gap: 20px;">
                    <div class="page-size-selector">
                        <label for="exact-page-size">Items per page:</label>
                        <select id="exact-page-size" onchange="changePageSize('exact', parseInt(this.value))">
                            <option value="10">10</option>
                            <option value="20" selected>20</option>
                            <option value="50">50</option>
                            <option value="100">100</option>
                            <option value="999999">All</option>
                        </select>
                    </div>
                    <div id="exact-pagination" class="pagination"></div>
                </div>
            </div>
            <p>Tests with identical code coverage that can be safely removed.</p>
            <div id="exact-table"></div>
        </div>

        <div id="similar-content" class="tab-content">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
                <h2 style="margin: 0;">🔍 Similar Tests (≥{threshold:.0%} overlap)</h2>
                <div style="display: flex; align-items: center; gap: 20px;">
                    <div class="page-size-selector">
                        <label for="similar-page-size">Items per page:</label>
                        <select id="similar-page-size" onchange="changePageSize('similar', parseInt(this.value))">
                            <option value="10">10</option>
                            <option value="20" selected>20</option>
                            <option value="50">50</option>
                            <option value="100">100</option>
                            <option value="999999">All</option>
                        </select>
                    </div>
                    <div id="similar-pagination" class="pagination"></div>
                </div>
            </div>
            <p>Test pairs with significant code coverage overlap that may indicate redundancy.</p>
            <div id="similar-table"></div>
        </div>

        <div id="subset-content" class="tab-content">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
                <h2 style="margin: 0;">📊 Subset Duplicates</h2>
                <div style="display: flex; align-items: center; gap: 20px;">
                    <div class="page-size-selector">
                        <label for="subset-page-size">Items per page:</label>
                        <select id="subset-page-size" onchange="changePageSize('subset', parseInt(this.value))">
                            <option value="10">10</option>
                            <option value="20" selected>20</option>
                            <option value="50">50</option>
                            <option value="100">100</option>
                            <option value="999999">All</option>
                        </select>
                    </div>
                    <div id="subset-pagination" class="pagination"></div>
                </div>
            </div>
            <p>Tests that are subsets of other tests and may be redundant.</p>
            <div id="subset-table"></div>
        </div>

        <script>
        // Utility function for escaping HTML to prevent XSS
        function escapeHtml(text) {{
            const div = document.createElement('div');
            div.textContent = text;
            return div.innerHTML;
        }}
        
        // Utility function to format test names with separators
        function formatTestName(testName) {{
            // Split test name at :: for better readability
            const parts = testName.split('::');
            if (parts.length === 1) return testName;
            
            return parts.map((part, idx) => {{
                if (idx === parts.length - 1) {{
                    return '<span class="test-part">' + part + '</span>';
                }}
                return '<span class="test-part">' + part + '</span><span class="test-separator">::</span><wbr>';
            }}).join('');
        }}
        
        // Data for pagination
        const exactDupsData = {json.dumps([[list(group), i-1] for i, group in enumerate(exact_dups, 1)])};
        const similarData = {json.dumps([[test1, test2, similarity, len(exact_dups) + idx] for idx, (test1, test2, similarity) in enumerate(similar)])};
        const subsetData = {json.dumps([[subset_test, superset_test, ratio, len(exact_dups) + len(similar) + i] for i, (subset_test, superset_test, ratio) in enumerate(subset_dups)])};
        
        // Build coverage data per file
        const coverageByFile = {{}};
        {self._build_coverage_data_js()}
        
        let itemsPerPage = {{ exact: 20, similar: 20, subset: 20 }};
        let currentPages = {{ exact: 1, similar: 1, subset: 1, coverage: 1 }};
        
        function changePageSize(type, newSize) {{
            itemsPerPage[type] = newSize;
            currentPages[type] = 1; // Reset to first page
            
            // Re-render the appropriate section
            if (type === 'exact') {{
                renderExactDuplicates(1);
            }} else if (type === 'similar') {{
                renderSimilarTests(1);
            }} else if (type === 'subset') {{
                renderSubsetDuplicates(1);
            }}
        }}
        
        function truncateTestName(testName) {{
            if (!testName || typeof testName !== 'string') {{
                return '';
            }}
            
            // Extract just the meaningful parts of the test name
            const parts = testName.split('::');
            if (parts.length <= 2) {{
                return testName;
            }}
            
            try {{
                // Get the file name (without path)
                const filePart = parts[0].split('/').pop() || parts[0];
                // Get the class name (if exists) and test name
                const classPart = parts.length > 2 ? parts[parts.length - 2] : '';
                const testPart = parts[parts.length - 1];
                
                // Format: FileName::Class::test_name
                if (classPart) {{
                    return filePart + '::' + classPart + '::' + testPart;
                }} else {{
                    return filePart + '::' + testPart;
                }}
            }} catch (e) {{
                console.error('Error truncating test name:', e);
                return testName;
            }}
        }}
        
        function switchTab(tabName) {{
            // Hide all tabs
            document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
            document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
            
            // Show selected tab
            event.target.classList.add('active');
            document.getElementById(tabName + '-content').classList.add('active');
        }}
        
        function renderExactDuplicates(page) {{
            const pageSize = itemsPerPage['exact'];
            const start = (page - 1) * pageSize;
            const end = start + pageSize;
            const pageData = exactDupsData.slice(start, end);
            
            let html = '';
            if (pageData.length === 0) {{
                html = '<p style="color: #27ae60; text-align: center; padding: 20px;">✓ No exact duplicates found!</p>';
            }} else {{
                html = `
                <table>
                    <thead>
                        <tr>
                            <th>Group</th>
                            <th>Tests</th>
                            <th>Count</th>
                            <th>Action</th>
                        </tr>
                    </thead>
                    <tbody>`;
                
                pageData.forEach(([group, coverageIdx], idx) => {{
                    const groupNum = start + idx + 1;
                    const testList = group.map(test => {{
                        if (!test) return '';
                        const truncated = truncateTestName(test);
                        return `<span class="test-name" title="${{escapeHtml(test)}}" style="cursor: help;">${{escapeHtml(truncated)}}</span>`;
                    }}).filter(t => t).join('<br>');
                    html += `
                        <tr class="clickable-row" onclick="showComparison(${{coverageIdx}})">
                            <td><strong>Group ${{groupNum}}</strong></td>
                            <td>${{testList}}</td>
                            <td><span class="badge badge-danger">${{group.length}} tests</span></td>
                            <td><span style="color: #00c6ff; font-weight: 600;">🔍 <span class="view-coverage-text">View Coverage</span></span></td>
                        </tr>`;
                }});
                
                html += '</tbody></table>';
            }}
            
            document.getElementById('exact-table').innerHTML = html;
            renderPagination('exact', exactDupsData.length, page, pageSize);
            formatTestNames();
        }}
        
        function renderSimilarTests(page) {{
            const pageSize = itemsPerPage['similar'];
            const start = (page - 1) * pageSize;
            const end = start + pageSize;
            const pageData = similarData.slice(start, end);
            
            let html = '';
            if (pageData.length === 0) {{
                html = '<p style="color: #27ae60; text-align: center; padding: 20px;">✓ No similar tests found!</p>';
            }} else {{
                html = `
                <table>
                    <thead>
                        <tr>
                            <th>Test 1</th>
                            <th>Test 2</th>
                            <th>Similarity</th>
                            <th>Action</th>
                        </tr>
                    </thead>
                    <tbody>`;
                
                pageData.forEach(([test1, test2, similarity, coverageIdx]) => {{
                    if (!test1 || !test2) return;
                    const t1 = escapeHtml(truncateTestName(test1));
                    const t2 = escapeHtml(truncateTestName(test2));
                    const simPercent = (similarity * 100).toFixed(1);
                    html += `
                        <tr class="clickable-row" onclick="showComparison(${{coverageIdx}})">
                            <td><span class="test-name" title="${{escapeHtml(test1)}}" style="cursor: help;">${{t1}}</span></td>
                            <td><span class="test-name" title="${{escapeHtml(test2)}}" style="cursor: help;">${{t2}}</span></td>
                            <td><span class="badge badge-info">${{simPercent}}%</span></td>
                            <td><span style="color: #00c6ff; font-weight: 600;">🔍 <span class="view-coverage-text">View Coverage</span></span></td>
                        </tr>`;
                }});
                
                html += '</tbody></table>';
            }}
            
            document.getElementById('similar-table').innerHTML = html;
            renderPagination('similar', similarData.length, page, pageSize);
            formatTestNames();
        }}
        
        function renderSubsetDuplicates(page) {{
            const pageSize = itemsPerPage['subset'];
            const start = (page - 1) * pageSize;
            const end = start + pageSize;
            const pageData = subsetData.slice(start, end);
            
            let html = '';
            if (pageData.length === 0) {{
                html = '<p style="color: #27ae60; text-align: center; padding: 20px;">✓ No subset duplicates found!</p>';
            }} else {{
                html = `
                <table>
                    <thead>
                        <tr>
                            <th>Subset Test</th>
                            <th>Superset Test</th>
                            <th>Coverage Ratio</th>
                            <th>Action</th>
                        </tr>
                    </thead>
                    <tbody>`;
                
                pageData.forEach(([subsetTest, supersetTest, ratio, coverageIdx]) => {{
                    if (!subsetTest || !supersetTest) return;
                    const sub = escapeHtml(truncateTestName(subsetTest));
                    const sup = escapeHtml(truncateTestName(supersetTest));
                    const ratioPercent = (ratio * 100).toFixed(1);
                    html += `
                        <tr class="clickable-row" onclick="showComparison(${{coverageIdx}})">
                            <td><span class="test-name" title="${{escapeHtml(subsetTest)}}" style="cursor: help;">${{sub}}</span></td>
                            <td><span class="test-name" title="${{escapeHtml(supersetTest)}}" style="cursor: help;">${{sup}}</span></td>
                            <td><span class="badge badge-warning">${{ratioPercent}}%</span></td>
                            <td><span style="color: #00c6ff; font-weight: 600;">🔍 <span class="view-coverage-text">View Coverage</span></span></td>
                        </tr>`;
                }});
                
                html += '</tbody></table>';
            }}
            
            document.getElementById('subset-table').innerHTML = html;
            renderPagination('subset', subsetData.length, page, pageSize);
            formatTestNames();
        }}
        
        function renderPagination(type, totalItems, currentPage, pageSize) {{
            const totalPages = Math.ceil(totalItems / pageSize);
            
            if (totalPages <= 1) {{
                document.getElementById(type + '-pagination').innerHTML = '';
                return;
            }}
            
            const start = (currentPage - 1) * pageSize + 1;
            const end = Math.min(currentPage * pageSize, totalItems);
            
            let html = '<button class="page-btn" onclick="changePage(\\'' + type + '\\', ' + (currentPage - 1) + ')" ' +
                (currentPage === 1 ? 'disabled' : '') + '>← Previous</button>' +
                '<span class="page-info">' + start + '-' + end + ' of ' + totalItems + ' | Page ' + currentPage + '/' + totalPages + '</span>' +
                '<button class="page-btn" onclick="changePage(\\'' + type + '\\', ' + (currentPage + 1) + ')" ' +
                (currentPage === totalPages ? 'disabled' : '') + '>Next →</button>';
            
            document.getElementById(type + '-pagination').innerHTML = html;
        }}
        
        function changePage(type, newPage) {{
            currentPages[type] = newPage;
            
            if (type === 'exact') {{
                renderExactDuplicates(newPage);
            }} else if (type === 'similar') {{
                renderSimilarTests(newPage);
            }} else if (type === 'subset') {{
                renderSubsetDuplicates(newPage);
            }}
            
            // Scroll to top of table
            document.getElementById(type + '-content').scrollIntoView({{ behavior: 'smooth', block: 'start' }});
        }}
        
        function formatTestNames() {{
            const testNames = document.querySelectorAll('.test-name');
            testNames.forEach(el => {{
                const originalText = el.textContent;
                if (originalText.includes('::')) {{
                    el.innerHTML = formatTestName(originalText);
                }}
            }});
        }}
        
        // Initialize on page load
        document.addEventListener('DOMContentLoaded', function() {{
            renderExactDuplicates(1);
            renderSimilarTests(1);
            renderSubsetDuplicates(1);
        }});
        </script>
"""
        
        # Add modal and JavaScript for split-screen view
        test_coverage_map = {test.test_name: test.covered_lines for test in self.finder.tests}
        
        coverage_data = []
        
        # Add exact duplicates data (first in order)
        for group in exact_dups:
            if len(group) < 2:
                continue
            # Compare first test with second test in group
            test1 = group[0]
            test2 = group[1]
            test1_cov = test_coverage_map.get(test1, set())
            test2_cov = test_coverage_map.get(test2, set())
            
            # Convert to dict format
            test1_dict = {}
            for filename, line in test1_cov:
                if filename not in test1_dict:
                    test1_dict[filename] = []
                test1_dict[filename].append(line)
            
            test2_dict = {}
            for filename, line in test2_cov:
                if filename not in test2_dict:
                    test2_dict[filename] = []
                test2_dict[filename].append(line)
            
            # Sort line numbers
            for lines in test1_dict.values():
                lines.sort()
            for lines in test2_dict.values():
                lines.sort()
            
            coverage_data.append({
                "subset": test1_dict,
                "superset": test2_dict,
                "ratio": 1.0,
                "subsetName": test1,
                "supersetName": test2
            })
        
        # Add similar tests data (second in order)
        for test1, test2, similarity in similar[:20]:
            test1_cov = test_coverage_map.get(test1, set())
            test2_cov = test_coverage_map.get(test2, set())
            
            # Convert to dict format
            test1_dict = {}
            for filename, line in test1_cov:
                if filename not in test1_dict:
                    test1_dict[filename] = []
                test1_dict[filename].append(line)
            
            test2_dict = {}
            for filename, line in test2_cov:
                if filename not in test2_dict:
                    test2_dict[filename] = []
                test2_dict[filename].append(line)
            
            # Sort line numbers
            for lines in test1_dict.values():
                lines.sort()
            for lines in test2_dict.values():
                lines.sort()
            
            coverage_data.append({
                "subset": test1_dict,
                "superset": test2_dict,
                "ratio": similarity,
                "subsetName": test1,
                "supersetName": test2
            })
        
        # Add subset duplicates data (third in order)
        for subset_test, superset_test, ratio in subset_dups[:20]:
            subset_cov = test_coverage_map.get(subset_test, set())
            superset_cov = test_coverage_map.get(superset_test, set())
            
            # Convert to dict format
            subset_dict = {}
            for filename, line in subset_cov:
                if filename not in subset_dict:
                    subset_dict[filename] = []
                subset_dict[filename].append(line)
            
            superset_dict = {}
            for filename, line in superset_cov:
                if filename not in superset_dict:
                    superset_dict[filename] = []
                superset_dict[filename].append(line)
            
            # Sort line numbers
            for lines in subset_dict.values():
                lines.sort()
            for lines in superset_dict.values():
                lines.sort()
            
            coverage_data.append({
                "subset": subset_dict,
                "superset": superset_dict,
                "ratio": ratio,
                "subsetName": subset_test,
                "supersetName": superset_test
            })

        # Serialize JSON data before embedding
        coverage_data_json = json.dumps(coverage_data, ensure_ascii=True)
        source_code_map_json = json.dumps(source_code_map, ensure_ascii=True)
        
        # Escape HTML-breaking tags in JSON strings
        # Even though it's in JSON, the browser's HTML parser will see </script> and break
        coverage_data_json = coverage_data_json.replace('</script>', '<\\/script>').replace('<script', '<\\script')
        source_code_map_json = source_code_map_json.replace('</script>', '<\\/script>').replace('<script', '<\\script')

        html += """
        <!-- Modal for split-screen coverage view -->
        <div id="comparisonModal" class="modal">
            <div class="modal-content">
                <div class="modal-header">
                    <h2 style="margin: 0;">📊 Coverage Comparison: Execution Paths</h2>
                    <div style="display: flex; align-items: center; gap: 15px;">
                        <div class="filter-section">
                            <label for="fileFilter" style="font-weight: 600; margin-right: 8px;">📁</label>
                            <select id="fileFilter" class="filter-select" onchange="applyFileFilter()">
                                <option value="">All Files</option>
                            </select>
                        </div>
                        <div class="sync-toggle" id="syncToggle" onclick="toggleSync()">
                            <input type="checkbox" id="syncCheckbox" class="sync-checkbox" checked>
                            <label for="syncCheckbox" style="cursor: pointer; user-select: none;">🔗 Sync Scroll</label>
                        </div>
                        <span class="close" onclick="closeModal()">&times;</span>
                    </div>
                </div>
                <div style="background: #e3f2fd; border-left: 4px solid #2196F3; padding: 12px 16px; margin: 0 20px 16px; border-radius: 4px; font-size: 14px;">
                    <strong>ℹ️ Note:</strong> Source code is identical. Highlighting shows <strong>which lines each test executed</strong>. 
                    Different execution paths are normal due to conditional branches (if/elif/else), early returns, and functions called with different parameters.
                </div>
                <div class="coverage-info">
                    <div>
                        <strong>Subset Test:</strong> <span id="subsetName" class="test-name"></span>
                        &nbsp;&nbsp;|&nbsp;&nbsp;
                        <strong>Superset Test:</strong> <span id="supersetName" class="test-name"></span>
                        &nbsp;&nbsp;|&nbsp;&nbsp;
                        <strong>Coverage Ratio:</strong> <span id="coverageRatio" class="badge badge-warning"></span>
                    </div>
                    <div style="margin-top: 10px; padding: 8px; background: #f5f5f5; border-radius: 4px; display: inline-flex; gap: 20px; font-size: 13px;">
                        <span><span style="display: inline-block; width: 16px; height: 16px; background: #c8e6c9; border-radius: 3px; vertical-align: middle;"></span> Both tests executed</span>
                        <span><span style="display: inline-block; width: 16px; height: 16px; background: #fff9c4; border-radius: 3px; vertical-align: middle;"></span> Only one test executed</span>
                        <span><span style="display: inline-block; width: 16px; height: 16px; background: #ffffff; border: 1px solid #ddd; border-radius: 3px; vertical-align: middle;"></span> Neither test executed</span>
                    </div>
                </div>
                <div class="split-view">
                    <div class="file-panel">
                        <div class="panel-header">📄 Subset Test Coverage</div>
                        <div id="subsetContent" class="file-content"></div>
                    </div>
                    <div class="file-panel">
                        <div class="panel-header">📄 Superset Test Coverage</div>
                        <div id="supersetContent" class="file-content"></div>
                    </div>
                </div>
            </div>
        </div>

        <script>
        const coverageData = """ + coverage_data_json + """;\n        const sourceCode = """ + source_code_map_json + """;\n        let currentData = null;
        let syncEnabled = true;
        let isScrolling = false;
        
        function showComparison(index) {{
            const data = coverageData[index];
            if (!data) return;
            
            currentData = data;
            
            document.getElementById('subsetName').innerHTML = formatTestName(data.subsetName);
            document.getElementById('supersetName').innerHTML = formatTestName(data.supersetName);
            document.getElementById('coverageRatio').textContent = (data.ratio * 100).toFixed(1) + '%';
            
            // Populate file filter
            const allFiles = new Set([...Object.keys(data.subset), ...Object.keys(data.superset)]);
            const fileFilter = document.getElementById('fileFilter');
            fileFilter.innerHTML = '<option value="">All Files</option>';
            Array.from(allFiles).sort().forEach(file => {{
                const option = document.createElement('option');
                option.value = file;
                option.textContent = file;
                fileFilter.appendChild(option);
            }});
            
            renderBothPanels();
            
            document.getElementById('comparisonModal').style.display = 'block';
            
            // Scroll to top of the modal
            const splitView = document.querySelector('.split-view');
            if (splitView) {{
                splitView.scrollTop = 0;
            }}
        }}
        
        function renderBothPanels() {{
            const selectedFile = document.getElementById('fileFilter').value;
            
            // Get all unique files from both sides
            const subsetFiles = Object.keys(currentData.subset).sort();
            const supersetFiles = Object.keys(currentData.superset).sort();
            const allFiles = [...new Set([...subsetFiles, ...supersetFiles])].sort();
            
            // Apply file filter
            const filesToRender = selectedFile ? [selectedFile] : allFiles;
            
            let subsetHtml = '';
            let supersetHtml = '';
            
            for (const file of filesToRender) {{
                const subsetLines = currentData.subset[file] || [];
                const supersetLines = currentData.superset[file] || [];
                
                // Get all unique line numbers from both sides
                let allLineNums = [...new Set([...subsetLines, ...supersetLines])].sort((a, b) => a - b);
                
                if (allLineNums.length === 0) continue;
                
                const subsetLineSet = new Set(subsetLines);
                const supersetLineSet = new Set(supersetLines);
                const fileSource = sourceCode[file] || {};
                
                // Find and include method/class definitions for context
                const minLine = Math.min(...allLineNums);
                const maxLine = Math.max(...allLineNums);
                const contextLines = new Set(allLineNums);
                
                // Scan backwards from each covered line to find def/class
                for (const lineNum of allLineNums) {{
                    for (let i = lineNum - 1; i >= Math.max(1, minLine - 20); i--) {{
                        const line = fileSource[i] || '';
                        const trimmed = line.trim();
                        if (trimmed.startsWith('def ') || trimmed.startsWith('class ') || trimmed.startsWith('async def ')) {{
                            contextLines.add(i);
                            break;
                        }}
                        // Stop if we hit another definition or empty line followed by def
                        if (trimmed === '' && i < lineNum - 5) break;
                    }}
                }}
                
                // Convert back to sorted array
                allLineNums = Array.from(contextLines).sort((a, b) => a - b);
                
                // Add file headers
                subsetHtml += '<div class=\"file-section\" style=\"margin-bottom: 30px;\">';
                subsetHtml += '<div class=\"file-path\">📄 ' + escapeHtml(file) + '</div>';
                
                supersetHtml += '<div class=\"file-section\" style=\"margin-bottom: 30px;\">';
                supersetHtml += '<div class=\"file-path\">📄 ' + escapeHtml(file) + '</div>';
                
                // Render each line with gap detection
                let prevLineNum = null;
                let inDocstring = false;
                let docstringDelimiter = '';
                
                for (let idx = 0; idx < allLineNums.length; idx++) {{
                    const lineNum = allLineNums[idx];
                    const sourceLine = fileSource[lineNum] || '';
                    const trimmed = sourceLine.trim();
                    
                    // Track docstring state
                    if (trimmed.startsWith('\"\"\"') || trimmed.startsWith("'''")) {{
                        const delimiter = trimmed.startsWith('\"\"\"') ? '\"\"\"' : "'''";
                        if (!inDocstring) {{
                            // Starting a docstring
                            inDocstring = true;
                            docstringDelimiter = delimiter;
                            // Check if it's a single-line docstring
                            const afterDelimiter = trimmed.substring(3);
                            if (afterDelimiter.includes(delimiter)) {{
                                inDocstring = false; // Single-line docstring
                            }}
                            continue; // Skip docstring opening line
                        }} else if (inDocstring && delimiter === docstringDelimiter) {{
                            // Ending a docstring
                            inDocstring = false;
                            docstringDelimiter = '';
                            continue; // Skip docstring closing line
                        }}
                    }} else if (inDocstring) {{
                        // Skip content inside docstring
                        continue;
                    }}
                    
                    // Handle gap between lines
                    if (prevLineNum !== null && lineNum - prevLineNum > 1) {{
                        const gap = lineNum - prevLineNum - 1;
                        const gapStart = prevLineNum + 1;
                        const gapEnd = lineNum - 1;
                        
                        if (gap > 3) {{
                            // Show collapsible gap for >3 lines
                            const gapId = 'gap_' + file.replace(/[^a-zA-Z0-9]/g, '_') + '_' + gapStart + '_' + gapEnd;
                            const gapText = '... (' + gap + ' line' + (gap > 1 ? 's' : '') + ')';
                            
                            subsetHtml += '<div class=\"code-line gap-line\" style=\"color: #000000; text-align: center; font-style: normal; background: transparent; cursor: pointer; padding: 2px 8px;\" ';
                            subsetHtml += 'data-gap-id=\"' + gapId + '\" data-gap-start=\"' + gapStart + '\" data-gap-end=\"' + gapEnd + '\" data-file=\"' + escapeHtml(file) + '\" ';
                            subsetHtml += 'onclick=\"toggleGap(this, \\'subset\\')\" title=\"Click to expand\">';
                            subsetHtml += '<strong>' + gapText + '</strong>';
                            subsetHtml += '</div>';
                            
                            supersetHtml += '<div class=\"code-line gap-line\" style=\"color: #000000; text-align: center; font-style: normal; background: transparent; cursor: pointer; padding: 2px 8px;\" ';
                            supersetHtml += 'data-gap-id=\"' + gapId + '\" data-gap-start=\"' + gapStart + '\" data-gap-end=\"' + gapEnd + '\" data-file=\"' + escapeHtml(file) + '\" ';
                            supersetHtml += 'onclick=\"toggleGap(this, \\'superset\\')\" title=\"Click to expand\">';
                            supersetHtml += '<strong>' + gapText + '</strong>';
                            supersetHtml += '</div>';
                        }} else {{
                            // Show lines if gap is 3 or less
                            for (let gapLine = gapStart; gapLine <= gapEnd; gapLine++) {{
                                const gapSource = fileSource[gapLine] || '';
                                const gapLineNumStr = String(gapLine).padStart(4, ' ');
                                
                                subsetHtml += '<div class=\"code-line\" style=\"opacity: 0.4; background: #fafafa;\">';
                                subsetHtml += '<span style=\"color: #bbb; margin-right: 10px;\">' + gapLineNumStr + '</span>';
                                subsetHtml += '<span style=\"color: #aaa;\">' + escapeHtml(gapSource) + '</span>';
                                subsetHtml += '</div>';
                                
                                supersetHtml += '<div class=\"code-line\" style=\"opacity: 0.4; background: #fafafa;\">';
                                supersetHtml += '<span style=\"color: #bbb; margin-right: 10px;\">' + gapLineNumStr + '</span>';
                                supersetHtml += '<span style=\"color: #aaa;\">' + escapeHtml(gapSource) + '</span>';
                                supersetHtml += '</div>';
                            }}
                        }}
                    }}
                    
                    prevLineNum = lineNum;
                    const lineNumStr = String(lineNum).padStart(4, ' ');
                    const isDefLine = trimmed.startsWith('def ') || trimmed.startsWith('class ') || trimmed.startsWith('async def ');
                    
                    // Determine coverage status
                    const inSubset = subsetLineSet.has(lineNum);
                    const inSuperset = supersetLineSet.has(lineNum);
                    const inBoth = inSubset && inSuperset;
                    
                    // Render left side (subset)
                    if (inBoth) {{
                        // Both tests executed this line - GREEN
                        subsetHtml += '<div class=\"code-line covered-both\">';
                        subsetHtml += '<span style=\"color: #999; margin-right: 10px;\">' + lineNumStr + '</span>';
                        subsetHtml += escapeHtml(sourceLine) || '&nbsp;';
                        subsetHtml += '</div>';
                    }} else if (inSubset) {{
                        // Only subset executed this line - YELLOW
                        subsetHtml += '<div class=\"code-line covered-single\">';
                        subsetHtml += '<span style=\"color: #999; margin-right: 10px;\">' + lineNumStr + '</span>';
                        subsetHtml += escapeHtml(sourceLine) || '&nbsp;';
                        subsetHtml += '</div>';
                    }} else if (isDefLine) {{
                        // Show def/class lines as context
                        subsetHtml += '<div class=\"code-line\" style=\"background: #e8f4f8; font-weight: 600;\">';
                        subsetHtml += '<span style=\"color: #999; margin-right: 10px;\">' + lineNumStr + '</span>';
                        subsetHtml += escapeHtml(sourceLine);
                        subsetHtml += '</div>';
                    }} else {{
                        // Show actual code dimmed for non-executed lines
                        subsetHtml += '<div class=\"code-line\" style=\"opacity: 0.4; background: #fafafa;\">';
                        subsetHtml += '<span style=\"color: #bbb; margin-right: 10px;\">' + lineNumStr + '</span>';
                        subsetHtml += '<span style=\"color: #999;\">' + escapeHtml(sourceLine) + '</span>';
                        subsetHtml += '</div>';
                    }}
                    
                    // Render right side (superset)
                    if (inBoth) {{
                        // Both tests executed this line - GREEN
                        supersetHtml += '<div class=\"code-line covered-both\">';
                        supersetHtml += '<span style=\"color: #999; margin-right: 10px;\">' + lineNumStr + '</span>';
                        supersetHtml += escapeHtml(sourceLine) || '&nbsp;';
                        supersetHtml += '</div>';
                    }} else if (inSuperset) {{
                        // Only superset executed this line - YELLOW
                        supersetHtml += '<div class=\"code-line covered-single\">';
                        supersetHtml += '<span style=\"color: #999; margin-right: 10px;\">' + lineNumStr + '</span>';
                        supersetHtml += escapeHtml(sourceLine) || '&nbsp;';
                        supersetHtml += '</div>';
                    }} else if (isDefLine) {{
                        // Show def/class lines as context
                        supersetHtml += '<div class=\"code-line\" style=\"background: #e8f4f8; font-weight: 600;\">';
                        supersetHtml += '<span style=\"color: #999; margin-right: 10px;\">' + lineNumStr + '</span>';
                        supersetHtml += escapeHtml(sourceLine);
                        supersetHtml += '</div>';
                    }} else {{
                        // Show actual code dimmed for non-executed lines
                        supersetHtml += '<div class=\"code-line\" style=\"opacity: 0.4; background: #fafafa;\">';
                        supersetHtml += '<span style=\"color: #bbb; margin-right: 10px;\">' + lineNumStr + '</span>';
                        supersetHtml += '<span style=\"color: #999;\">' + escapeHtml(sourceLine) + '</span>';
                        supersetHtml += '</div>';
                    }}
                }}
                
                subsetHtml += '</div>';
                supersetHtml += '</div>';
            }}
            
            document.getElementById('subsetContent').innerHTML = subsetHtml || '<p style=\"padding: 20px; color: #7f8c8d;\">No coverage data</p>';
            document.getElementById('supersetContent').innerHTML = supersetHtml || '<p style=\"padding: 20px; color: #7f8c8d;\">No coverage data</p>';
        }}
        
        function applyFileFilter() {{
            renderBothPanels();
        }}
        
        function toggleSync() {{
            syncEnabled = !syncEnabled;
            const checkbox = document.getElementById('syncCheckbox');
            const toggle = document.getElementById('syncToggle');
            const splitView = document.querySelector('.split-view');
            const filePanels = document.querySelectorAll('.file-panel');
            
            checkbox.checked = syncEnabled;
            if (syncEnabled) {{
                toggle.classList.add('active');
                // Use single scroll - both panels scroll together
                splitView.classList.remove('independent');
                filePanels.forEach(panel => panel.classList.remove('independent'));
            }} else {{
                toggle.classList.remove('active');
                // Enable independent scrolling for each panel
                splitView.classList.add('independent');
                filePanels.forEach(panel => panel.classList.add('independent'));
            }}
        }}
        
        function toggleGap(element, side) {{
            const gapId = element.getAttribute('data-gap-id');
            const gapStart = parseInt(element.getAttribute('data-gap-start'));
            const gapEnd = parseInt(element.getAttribute('data-gap-end'));
            const file = element.getAttribute('data-file');
            
            // Find the corresponding gap in the other panel
            const otherSide = side === 'subset' ? 'superset' : 'subset';
            const otherContent = document.getElementById(otherSide + 'Content');
            const otherGap = otherContent.querySelector('.gap-line[data-gap-id="' + gapId + '"]');
            
            // Check if already expanded
            const isExpanded = element.classList.contains('expanded');
            
            if (isExpanded) {{
                // Collapse both sides - show gap element again
                const expandedLines = element.parentElement.querySelectorAll('.expanded-line[data-gap-id="' + gapId + '"]');
                expandedLines.forEach(line => line.remove());
                element.classList.remove('expanded');
                element.style.display = 'block';
                const gap = gapEnd - gapStart + 1;
                element.innerHTML = '<strong>... (' + gap + ' line' + (gap > 1 ? 's' : '') + ')</strong>';
                
                // Collapse other side
                if (otherGap) {{
                    const otherExpandedLines = otherGap.parentElement.querySelectorAll('.expanded-line[data-gap-id="' + gapId + '"]');
                    otherExpandedLines.forEach(line => line.remove());
                    otherGap.classList.remove('expanded');
                    otherGap.style.display = 'block';
                    otherGap.innerHTML = '<strong>... (' + gap + ' line' + (gap > 1 ? 's' : '') + ')</strong>';
                }}
            }} else {{
                // Expand both sides - hide gap element completely
                element.classList.add('expanded');
                element.style.display = 'none';
                
                const fileSource = sourceCode[file] || {};
                const subsetLineSet = new Set(currentData.subset[file] || []);
                const supersetLineSet = new Set(currentData.superset[file] || []);
                
                let subsetInsertHtml = '';
                let supersetInsertHtml = '';
                
                // Build in ASCENDING order from gapStart to gapEnd
                // Show ALL lines when gap is expanded (including docstrings, comments, etc.)
                for (let lineNum = gapStart; lineNum <= gapEnd; lineNum++) {{
                    const sourceLine = fileSource[lineNum] || '';
                    const lineNumStr = String(lineNum).padStart(4, ' ');
                    
                    const inSubset = subsetLineSet.has(lineNum);
                    const inSuperset = supersetLineSet.has(lineNum);
                    const inBoth = inSubset && inSuperset;
                    
                    // Make all expanded lines clickable to collapse
                    const clickHandler = 'onclick="toggleGap(document.querySelector(\\'.gap-line[data-gap-id=\\\\\\'' + gapId + '\\\\\\']\\'), \\'subset\\')" style="cursor: pointer;" title="Click to collapse"';
                    
                    // Always show actual source code, with color coding for execution status
                    // Build subset side HTML
                    if (inBoth) {{
                        subsetInsertHtml += '<div class="code-line expanded-line covered-both" data-gap-id="' + gapId + '" ' + clickHandler + '>';
                        subsetInsertHtml += '<span style="color: #999; margin-right: 10px;">' + lineNumStr + '</span>';
                        subsetInsertHtml += escapeHtml(sourceLine) || '&nbsp;';
                        subsetInsertHtml += '</div>';
                    }} else if (inSubset) {{
                        subsetInsertHtml += '<div class="code-line expanded-line covered-single" data-gap-id="' + gapId + '" ' + clickHandler + '>';
                        subsetInsertHtml += '<span style="color: #999; margin-right: 10px;">' + lineNumStr + '</span>';
                        subsetInsertHtml += escapeHtml(sourceLine) || '&nbsp;';
                        subsetInsertHtml += '</div>';
                    }} else {{
                        // Show actual code even when not executed, just dimmed
                        subsetInsertHtml += '<div class="code-line expanded-line" data-gap-id="' + gapId + '" style="opacity: 0.4; background: #fafafa; cursor: pointer;" onclick="toggleGap(document.querySelector(\\'.gap-line[data-gap-id=\\\\\\'' + gapId + '\\\\\\']\\'), \\'subset\\')" title="Click to collapse">';
                        subsetInsertHtml += '<span style="color: #bbb; margin-right: 10px;">' + lineNumStr + '</span>';
                        subsetInsertHtml += '<span style="color: #999;">' + escapeHtml(sourceLine) + '</span>';
                        subsetInsertHtml += '</div>';
                    }}
                    
                    // Build superset side HTML
                    if (inBoth) {{
                        supersetInsertHtml += '<div class="code-line expanded-line covered-both" data-gap-id="' + gapId + '" ' + clickHandler + '>';
                        supersetInsertHtml += '<span style="color: #999; margin-right: 10px;">' + lineNumStr + '</span>';
                        supersetInsertHtml += escapeHtml(sourceLine) || '&nbsp;';
                        supersetInsertHtml += '</div>';
                    }} else if (inSuperset) {{
                        supersetInsertHtml += '<div class="code-line expanded-line covered-single" data-gap-id="' + gapId + '" ' + clickHandler + '>';
                        supersetInsertHtml += '<span style="color: #999; margin-right: 10px;">' + lineNumStr + '</span>';
                        supersetInsertHtml += escapeHtml(sourceLine) || '&nbsp;';
                        supersetInsertHtml += '</div>';
                    }} else {{
                        // Show actual code even when not executed, just dimmed
                        supersetInsertHtml += '<div class="code-line expanded-line" data-gap-id="' + gapId + '" style="opacity: 0.4; background: #fafafa; cursor: pointer;" onclick="toggleGap(document.querySelector(\\'.gap-line[data-gap-id=\\\\\\'' + gapId + '\\\\\\']\\'), \\'superset\\')" title="Click to collapse">';
                        supersetInsertHtml += '<span style="color: #bbb; margin-right: 10px;">' + lineNumStr + '</span>';
                        supersetInsertHtml += '<span style="color: #999;">' + escapeHtml(sourceLine) + '</span>';
                        supersetInsertHtml += '</div>';
                    }}
                }}
                
                // Insert in correct order: create elements array first, then insert in REVERSE
                if (side === 'subset') {{
                    const tempDiv = document.createElement('div');
                    tempDiv.innerHTML = subsetInsertHtml;
                    const elementsArray = Array.from(tempDiv.children);
                    // Insert in REVERSE order to maintain ascending line numbers
                    for (let i = elementsArray.length - 1; i >= 0; i--) {{
                        element.parentNode.insertBefore(elementsArray[i], element.nextSibling);
                    }}
                }} else {{
                    const tempDiv = document.createElement('div');
                    tempDiv.innerHTML = supersetInsertHtml;
                    const elementsArray = Array.from(tempDiv.children);
                    // Insert in REVERSE order to maintain ascending line numbers
                    for (let i = elementsArray.length - 1; i >= 0; i--) {{
                        element.parentNode.insertBefore(elementsArray[i], element.nextSibling);
                    }}
                }}
                
                // Expand other side - hide it too
                if (otherGap) {{
                    otherGap.classList.add('expanded');
                    otherGap.style.display = 'none';
                    
                    const tempDiv2 = document.createElement('div');
                    if (otherSide === 'subset') {{
                        tempDiv2.innerHTML = subsetInsertHtml;
                    }} else {{
                        tempDiv2.innerHTML = supersetInsertHtml;
                    }}
                    const elementsArray2 = Array.from(tempDiv2.children);
                    // Insert in REVERSE order to maintain ascending line numbers
                    for (let i = elementsArray2.length - 1; i >= 0; i--) {{
                        otherGap.parentNode.insertBefore(elementsArray2[i], otherGap.nextSibling);
                    }}
                }}
            }}
        }}
        
        function closeModal() {{
            document.getElementById('comparisonModal').style.display = 'none';
            currentData = null;
        }}
        
        window.onclick = function(event) {{
            const modal = document.getElementById('comparisonModal');
            if (event.target == modal) {{
                closeModal();
            }}
        }}
        
        document.addEventListener('keydown', function(event) {{
            if (event.key === 'Escape') {{
                closeModal();
            }}
        }});
        
        // Format all test names on page load
        document.addEventListener('DOMContentLoaded', function() {{
            const testNames = document.querySelectorAll('.test-name');
            testNames.forEach(el => {{
                const originalText = el.textContent;
                if (originalText.includes('::')) {{
                    el.innerHTML = formatTestName(originalText);
                }}
            }});
            
            // Initial render after DOM is loaded and all functions are defined
            renderExactDuplicates(1);
            renderSimilarTests(1);
            renderSubsetDuplicates(1);
        }});
        </script>
        
        <div class="footer">
            <p>Generated by <strong>TestIQ v{version}</strong> on {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
            <p>Analysis threshold: {threshold:.1%} | 🔗 <a href="https://github.com/pydevtools/TestIQ" style="color: #00c6ff;">github.com/pydevtools/TestIQ</a></p>
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
        duplicate_count = self.finder.get_duplicate_count()

        logger.info(f"  Found {len(exact_dups)} groups with {duplicate_count} duplicates")

        with open(output_path, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["Group", "Test Name", "Action"])

            for i, group in enumerate(exact_dups, 1):
                for j, test in enumerate(group):
                    action = "Keep" if j == 0 else "Remove"
                    writer.writerow([f"Group {i}", test, action])

        logger.info(f"CSV report saved: {output_path}")

    def generate_subset_duplicates(self, output_path: Path) -> None:
        """Generate CSV of subset duplicates (sorted by coverage ratio)."""
        logger.info(f"Generating subset duplicates CSV: {output_path}")

        subsets = self.finder.get_sorted_subset_duplicates()  # Use sorted version

        logger.info(f"  Found {len(subsets)} subset duplicates")

        with open(output_path, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["Subset Test", "Superset Test", "Coverage Ratio", "Action"])

            for subset_test, superset_test, ratio in subsets:
                writer.writerow(
                    [
                        subset_test,
                        superset_test,
                        f"{ratio:.1%}",  # Consistent 1 decimal place
                        "Review for removal",
                    ]
                )

        logger.info(f"CSV report saved: {output_path}")

    def generate_similar_tests(self, output_path: Path, threshold: float = 0.3) -> None:
        """
        Generate CSV of similar tests.

        Args:
            output_path: Path to save CSV
            threshold: Similarity threshold (default: 0.3 = 30%)
        """
        logger.info(f"Generating similar tests CSV: {output_path}")
        logger.info(f"  Threshold: {threshold:.1%}")

        similar = self.finder.find_similar_coverage(threshold)

        logger.info(f"  Found {len(similar)} similar test pairs")

        with open(output_path, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["Test 1", "Test 2", "Similarity", "Action"])

            for test1, test2, similarity in similar:
                writer.writerow(
                    [test1, test2, f"{similarity:.1%}", "Review for merge"]  # Consistent 1 decimal
                )

        logger.info(f"CSV report saved: {output_path}")

    def generate_summary(self, output_path: Path, threshold: float = 0.3) -> None:
        """
        Generate summary CSV with all data and metadata.

        Args:
            output_path: Path to save CSV
            threshold: Similarity threshold (default: 0.3 = 30%)
        """
        from testiq import __version__
        from datetime import datetime

        logger.info(f"Generating summary CSV: {output_path}")
        logger.info(f"  Threshold: {threshold:.1%}")

        exact_dups = self.finder.find_exact_duplicates()
        subsets = self.finder.get_sorted_subset_duplicates()  # Use sorted
        similar = self.finder.find_similar_coverage(threshold)
        duplicate_count = self.finder.get_duplicate_count()

        logger.info(f"  Exact duplicates: {duplicate_count}")
        logger.info(f"  Subset duplicates: {len(subsets)}")
        logger.info(f"  Similar pairs: {len(similar)}")

        with open(output_path, "w", newline="") as f:
            writer = csv.writer(f)

            # Metadata section
            writer.writerow(["METADATA"])
            writer.writerow(["Generated", datetime.now().strftime("%Y-%m-%d %H:%M:%S")])
            writer.writerow(["TestIQ Version", __version__])
            writer.writerow(["Similarity Threshold", f"{threshold:.1%}"])
            writer.writerow([])

            # Summary statistics
            writer.writerow(["SUMMARY STATISTICS"])
            writer.writerow(["Metric", "Value"])
            writer.writerow(["Total Tests", len(self.finder.tests)])
            writer.writerow(["Exact Duplicates (can remove)", duplicate_count])
            writer.writerow(["Exact Duplicate Groups", len(exact_dups)])
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

            # Subset duplicates section (all, sorted by ratio)
            writer.writerow(["SUBSET DUPLICATES (sorted by coverage ratio)"])
            writer.writerow(["Subset Test", "Superset Test", "Coverage Ratio"])
            for subset_test, superset_test, ratio in subsets:
                writer.writerow([subset_test, superset_test, f"{ratio:.1%}"])
            writer.writerow([])

            # Similar tests section (all)
            writer.writerow(["SIMILAR TESTS"])
            writer.writerow(["Test 1", "Test 2", "Similarity"])
            for test1, test2, similarity in similar:
                writer.writerow([test1, test2, f"{similarity:.1%}"])

        logger.info(f"CSV report saved: {output_path}")
