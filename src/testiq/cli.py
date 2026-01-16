"""
Command-line interface for TestIQ.
"""

import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

import click
from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from testiq import __version__
from testiq.analysis import QualityAnalyzer, RecommendationEngine
from testiq.analyzer import CoverageDuplicateFinder
from testiq.cicd import BaselineManager, QualityGate, QualityGateChecker, TrendTracker, get_exit_code
from testiq.config import Config, load_config
from testiq.exceptions import TestIQError
from testiq.logging_config import get_logger, setup_logging
from testiq.reporting import CSVReportGenerator, HTMLReportGenerator
from testiq.security import (
    check_file_size,
    sanitize_output_path,
    validate_coverage_data,
    validate_file_path,
)

console = Console()
logger = get_logger(__name__)

# Constants
TESTIQ_CONFIG_DIR = ".testiq"
SAMPLE_AUTH_FILE = "auth.py"
SAMPLE_USER_FILE = "user.py"


def _get_grade_color(grade: str) -> str:
    """Get the color for a grade letter."""
    first_letter = grade[0] if grade else 'F'
    if first_letter == 'A':
        return 'green'
    elif first_letter in ('B', 'C'):
        return 'yellow'
    else:
        return 'red'


@click.group()
@click.version_option(version=__version__, prog_name="TestIQ")
@click.option(
    "--config",
    "-c",
    type=click.Path(exists=True, path_type=Path),
    help="Path to configuration file (.yaml, .yml, .toml)",
)
@click.option(
    "--log-level",
    type=click.Choice(["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]),
    help="Set logging level",
)
@click.option(
    "--log-file",
    type=click.Path(path_type=Path),
    help="Log file path",
)
@click.pass_context
def main(
    ctx: click.Context, config: Optional[Path], log_level: Optional[str], log_file: Optional[Path]
) -> None:
    """
    TestIQ - Intelligent Test Analysis

    Find duplicate and redundant tests using coverage analysis.
    """
    # Load configuration
    try:
        cfg = load_config(config)

        # Override with CLI options
        if log_level:
            cfg.log.level = log_level
        if log_file:
            cfg.log.file = str(log_file)

        # Setup logging
        setup_logging(
            level=cfg.log.level,
            log_file=Path(cfg.log.file) if cfg.log.file else None,
            enable_rotation=cfg.log.enable_rotation,
            max_bytes=cfg.log.max_bytes,
            backup_count=cfg.log.backup_count,
        )

        # Store config in context
        ctx.ensure_object(dict)
        ctx.obj["config"] = cfg

        logger.debug(f"TestIQ v{__version__} initialized")
        if config:
            logger.info(f"Loaded configuration from: {config}")

    except Exception as e:
        console.print(f"[red]Configuration error: {e}[/red]")
        sys.exit(1)


def _load_and_validate_coverage(coverage_file: Path, cfg: Config) -> dict:
    """Load and validate coverage data from file."""
    validated_path = validate_file_path(coverage_file)
    check_file_size(validated_path, cfg.security.max_file_size)
    
    with open(validated_path) as f:
        coverage_data = json.load(f)
    
    validate_coverage_data(coverage_data, cfg.security.max_tests)
    logger.info(f"Loaded {len(coverage_data)} tests from coverage file")
    
    return coverage_data


def _create_finder(cfg: Config, coverage_data: dict) -> CoverageDuplicateFinder:
    """Create and populate the coverage duplicate finder."""
    finder = CoverageDuplicateFinder(
        enable_parallel=cfg.performance.enable_parallel,
        max_workers=cfg.performance.max_workers,
        enable_caching=cfg.performance.enable_caching,
        cache_dir=cfg.performance.cache_dir,
    )
    
    for test_name, test_coverage in coverage_data.items():
        finder.add_test_coverage(test_name, test_coverage)
    
    return finder


def _check_quality_gate(
    quality_gate: bool,
    max_duplicates: int,
    baseline: Optional[Path],
    finder: CoverageDuplicateFinder,
    threshold: float,
    console: Console,
) -> int:
    """Check quality gate and return exit code."""
    if not quality_gate:
        return 0
    
    gate = QualityGate(
        max_duplicates=max_duplicates,
        fail_on_increase=baseline is not None,
    )
    checker = QualityGateChecker(gate)
    
    baseline_result = None
    if baseline:
        baseline_mgr = BaselineManager(Path.home() / TESTIQ_CONFIG_DIR / "baselines")
        baseline_result = baseline_mgr.load(baseline.stem)
    
    passed, details = checker.check(finder, threshold, baseline_result)
    
    if not passed:
        console.print("\n[red]✗ Quality Gate FAILED[/red]")
        for failure in details["failures"]:
            console.print(f"  • {failure}")
        return 2
    else:
        console.print("\n[green]✓ Quality Gate PASSED[/green]")
        return 0


def _save_baseline_if_requested(
    save_baseline: Optional[Path],
    finder: CoverageDuplicateFinder,
    threshold: float,
    console: Console,
) -> None:
    """Save baseline file if requested."""
    if not save_baseline:
        return
    
    from testiq.cicd import AnalysisResult
    
    exact_dups = finder.find_exact_duplicates()
    duplicate_count = sum(len(g) - 1 for g in exact_dups)
    total_tests = len(finder.tests)
    
    result = AnalysisResult(
        timestamp=datetime.now().isoformat(),
        total_tests=total_tests,
        exact_duplicates=duplicate_count,
        duplicate_groups=len(exact_dups),
        subset_duplicates=len(finder.find_subset_duplicates()),
        similar_pairs=len(finder.find_similar_coverage(threshold)),
        duplicate_percentage=(duplicate_count / total_tests * 100) if total_tests > 0 else 0,
        threshold=threshold,
    )
    
    baseline_mgr = BaselineManager(Path.home() / TESTIQ_CONFIG_DIR / "baselines")
    baseline_mgr.save(result, save_baseline.stem)
    console.print(f"[green]✓ Baseline saved: {save_baseline}[/green]")


def _generate_output(
    format: str,
    output: Optional[Path],
    finder: CoverageDuplicateFinder,
    threshold: float,
    console: Console,
) -> None:
    """Generate output in the specified format."""
    if format == "html":
        if not output:
            console.print("[red]Error: HTML format requires --output[/red]")
            sys.exit(1)
        html_gen = HTMLReportGenerator(finder)
        html_gen.generate(output, threshold=threshold)
        console.print(f"[green]✓ HTML report saved to {output}[/green]")
    
    elif format == "csv":
        if not output:
            console.print("[red]Error: CSV format requires --output[/red]")
            sys.exit(1)
        csv_gen = CSVReportGenerator(finder)
        csv_gen.generate_summary(output, threshold=threshold)
        console.print(f"[green]✓ CSV report saved to {output}[/green]")
    
    elif format == "json":
        stats = finder.get_statistics(threshold)
        result = {
            "metadata": {
                "timestamp": datetime.now().isoformat(),
                "testiq_version": __version__,
                "threshold": threshold,
                "total_tests": len(finder.tests),
                "total_removable_duplicates": stats["total_removable_duplicates"],
            },
            "exact_duplicates": finder.find_exact_duplicates(),
            "subset_duplicates": [
                {"subset": s, "superset": sup, "ratio": r}
                for s, sup, r in finder.get_sorted_subset_duplicates()
            ],
            "similar_tests": [
                {"test1": t1, "test2": t2, "similarity": sim}
                for t1, t2, sim in finder.find_similar_coverage(threshold)
            ],
            "statistics": stats,
        }
        output_text = json.dumps(result, indent=2)
        
        if output:
            validated_output = sanitize_output_path(output)
            validated_output.write_text(output_text)
            console.print(f"[green]✓ JSON report saved to {validated_output}[/green]")
        else:
            console.print(output_text)
    
    elif format == "markdown":
        output_text = finder.generate_report(threshold)
        
        if output:
            validated_output = sanitize_output_path(output)
            validated_output.write_text(output_text)
            console.print(f"[green]✓ Report saved to {validated_output}[/green]")
        else:
            console.print(output_text)
    
    else:  # text format with rich
        if output:
            console.print("[yellow]Warning: --output ignored for text format[/yellow]")
        display_results(finder, threshold)


@main.command()
@click.argument("coverage_file", type=click.Path(exists=True, path_type=Path))
@click.option(
    "--threshold",
    "-t",
    type=float,
    help="Similarity threshold (0.0-1.0). Default: 0.3 (30%). Tests with ≥30%% overlap are considered similar.",
)
@click.option(
    "--output",
    "-o",
    type=click.Path(path_type=Path),
    help="Output file for the report (default: stdout)",
)
@click.option(
    "--format",
    "-f",
    type=click.Choice(["markdown", "json", "text", "html", "csv"]),
    default="text",
    help="Output format (html and csv require --output)",
)
@click.option(
    "--quality-gate",
    is_flag=True,
    help="Enable quality gate checking (exits with code 2 if failed)",
)
@click.option(
    "--max-duplicates",
    type=int,
    default=0,
    help="Maximum allowed exact duplicates. Default: 0 (no duplicates allowed)",
)
@click.option(
    "--baseline",
    type=click.Path(path_type=Path),
    help="Baseline file for comparison (for quality gate)",
)
@click.option(
    "--save-baseline",
    type=click.Path(path_type=Path),
    help="Save results as baseline for future comparisons",
)
@click.pass_context
def analyze(
    ctx: click.Context,
    coverage_file: Path,
    threshold: Optional[float],
    output: Optional[Path],
    format: str,
    quality_gate: bool,
    max_duplicates: int,
    baseline: Optional[Path],
    save_baseline: Optional[Path],
) -> None:
    """
    Analyze test coverage data to find duplicates.

    COVERAGE_FILE: JSON file containing per-test coverage data
    """
    cfg: Config = ctx.obj["config"]

    # Use config threshold if not provided
    if threshold is None:
        threshold = cfg.analysis.similarity_threshold

    console.print("[cyan]TestIQ Analysis Starting...[/cyan]")
    console.print(f"  • Coverage file: {coverage_file}")
    console.print(f"  • Similarity threshold: {threshold:.1%} (tests with ≥{threshold:.1%} overlap are flagged)")
    console.print(f"  • Max duplicates allowed: {max_duplicates}")
    console.print(f"  • Output format: {format}")
    if output:
        console.print(f"  • Output file: {output}")
    console.print()

    try:
        # Load and validate coverage data
        coverage_data = _load_and_validate_coverage(coverage_file, cfg)
        
        # Create and populate finder
        finder = _create_finder(cfg, coverage_data)
        
        # Check quality gate
        exit_code = _check_quality_gate(
            quality_gate, max_duplicates, baseline, finder, threshold, console
        )
        
        # Save baseline if requested
        _save_baseline_if_requested(save_baseline, finder, threshold, console)
        
        # Generate output
        _generate_output(format, output, finder, threshold, console)
        
        sys.exit(exit_code)

    except TestIQError as e:
        console.print(f"[red]Error: {e}[/red]")
        logger.error(str(e))
        sys.exit(1)
    except json.JSONDecodeError as e:
        console.print(f"[red]Invalid JSON in {coverage_file}: {e}[/red]")
        logger.error(f"JSON decode error: {e}")
        sys.exit(1)
    except Exception as e:
        console.print(f"[red]Unexpected error: {e}[/red]")
        logger.exception("Unexpected error during analysis")
        sys.exit(1)


def display_results(finder: CoverageDuplicateFinder, threshold: float) -> None:
    """Display results in rich formatted text."""
    console.print(
        Panel(
            "[bold cyan]TestIQ Analysis Results[/bold cyan]",
            box=box.DOUBLE,
        )
    )

    # Exact duplicates
    exact_dups = finder.find_exact_duplicates()
    if exact_dups:
        table = Table(title="🎯 Exact Duplicates (Identical Coverage)", show_header=True)
        table.add_column("Group", style="cyan", width=10)
        table.add_column("Tests", style="yellow", no_wrap=False, overflow="fold")
        table.add_column("Action", style="green", width=20)

        for i, group in enumerate(exact_dups, 1):
            tests_str = "\n".join(group)
            action = f"Remove {len(group) - 1} duplicate(s)"
            table.add_row(f"Group {i}", tests_str, action)

        console.print(table)
        console.print()

    # Subset duplicates (sorted by ratio)
    subsets = finder.get_sorted_subset_duplicates()
    if subsets:
        table = Table(title="📊 Subset Duplicates (Sorted by Coverage Ratio)", show_header=True)
        table.add_column("Subset Test", style="yellow", no_wrap=False, overflow="fold")
        table.add_column("Superset Test", style="cyan", no_wrap=False, overflow="fold")
        table.add_column("Coverage Ratio", style="magenta", width=15)

        for subset_test, superset_test, ratio in subsets[:10]:
            table.add_row(subset_test, superset_test, f"{ratio:.1%}")

        if len(subsets) > 10:
            console.print(table)
            console.print(f"[dim]... and {len(subsets) - 10} more subset duplicates[/dim]\n")
        else:
            console.print(table)
            console.print()

    # Similar tests
    similar = finder.find_similar_coverage(threshold)
    if similar:
        table = Table(title=f"🔍 Similar Tests (≥{threshold:.1%} overlap)", show_header=True)
        table.add_column("Test 1", style="yellow", no_wrap=False, overflow="fold")
        table.add_column("Test 2", style="cyan", no_wrap=False, overflow="fold")
        table.add_column("Similarity", style="magenta", width=12)

        for test1, test2, similarity in similar[:10]:
            table.add_row(test1, test2, f"{similarity:.1%}")

        if len(similar) > 10:
            console.print(table)
            console.print(f"[dim]... and {len(similar) - 10} more similar test pairs[/dim]\n")
        else:
            console.print(table)
            console.print()

    # Summary with statistics
    stats = finder.get_statistics(threshold)
    summary_table = Table(title="📈 Summary", show_header=True, box=box.ROUNDED)
    summary_table.add_column("Metric", style="cyan")
    summary_table.add_column("Count", style="bold green")

    summary_table.add_row("Total tests analyzed", str(len(finder.tests)))
    summary_table.add_row("Exact duplicates (can remove)", str(stats["exact_duplicate_count"]))
    summary_table.add_row("Subset duplicates (can optimize)", str(stats["subset_duplicate_count"]))
    summary_table.add_row("Similar test pairs", str(stats["similar_pair_count"]))
    summary_table.add_row("Total removable duplicates", str(stats["total_removable_duplicates"]))

    console.print(summary_table)


@main.command()
def demo() -> None:
    """Run a demonstration with sample data."""
    console.print("[cyan]Running TestIQ demo with sample data...[/cyan]\n")

    finder = CoverageDuplicateFinder()

    # Add sample test data
    finder.add_test_coverage(
        "test_user_login_success_1",
        {SAMPLE_AUTH_FILE: [10, 11, 12, 15, 20, 25], SAMPLE_USER_FILE: [5, 6, 7]},
    )

    finder.add_test_coverage(
        "test_user_login_success_2",
        {SAMPLE_AUTH_FILE: [10, 11, 12, 15, 20, 25], SAMPLE_USER_FILE: [5, 6, 7]},
    )

    finder.add_test_coverage("test_user_login_minimal", {SAMPLE_AUTH_FILE: [10, 11, 12]})

    finder.add_test_coverage(
        "test_user_login_complete",
        {
            SAMPLE_AUTH_FILE: [10, 11, 12, 15, 20, 25, 30, 35],
            SAMPLE_USER_FILE: [5, 6, 7],
            "db.py": [100, 101],
        },
    )

    finder.add_test_coverage(
        "test_admin_login",
        {SAMPLE_AUTH_FILE: [10, 11, 12, 15, 20, 25, 40], SAMPLE_USER_FILE: [5, 6, 7], "admin.py": [50]},
    )

    finder.add_test_coverage(
        "test_password_reset", {"password.py": [1, 2, 3, 4, 5], "email.py": [10, 20]}
    )

    display_results(finder, threshold=0.3)


if __name__ == "__main__":
    main()


@main.command(name="quality-score")
@click.argument("coverage_file", type=click.Path(exists=True, path_type=Path))
@click.option(
    "--threshold",
    "-t",
    type=float,
    help="Similarity threshold (0.0-1.0) for detecting similar tests",
)
@click.option(
    "--output",
    "-o",
    type=click.Path(path_type=Path),
    help="Output file for the report (default: stdout)",
)
@click.pass_context
def quality_score(
    ctx: click.Context,
    coverage_file: Path,
    threshold: Optional[float],
    output: Optional[Path],
) -> None:
    """
    Analyze test quality and get actionable recommendations.

    COVERAGE_FILE: JSON file containing per-test coverage data
    """
    cfg: Config = ctx.obj["config"]

    if threshold is None:
        threshold = cfg.analysis.similarity_threshold

    try:
        # Load and validate coverage data
        validated_path = validate_file_path(coverage_file)
        check_file_size(validated_path, cfg.security.max_file_size)

        with open(validated_path) as f:
            coverage_data = json.load(f)

        validate_coverage_data(coverage_data, cfg.security.max_tests)

        # Create analyzer
        finder = CoverageDuplicateFinder(
            enable_parallel=cfg.performance.enable_parallel,
            max_workers=cfg.performance.max_workers,
        )

        for test_name, test_coverage in coverage_data.items():
            finder.add_test_coverage(test_name, test_coverage)

        # Calculate quality score
        analyzer = QualityAnalyzer(finder)
        score = analyzer.calculate_score(threshold)

        # Display score with rich formatting
        grade_color = _get_grade_color(score.grade)
        console.print(
            Panel(
                f"[bold cyan]Test Quality Score[/bold cyan]\n\n"
                f"Overall Score: [bold yellow]{score.overall_score:.1f}/100[/bold yellow]\n"
                f"Grade: [bold][{grade_color}]{score.grade}[/{grade_color}][/bold]\n\n"
                f"Duplication Score: {score.duplication_score:.1f}/100\n"
                f"Coverage Efficiency: {score.coverage_efficiency_score:.1f}/100\n"
                f"Uniqueness Score: {score.uniqueness_score:.1f}/100",
                box=box.DOUBLE,
            )
        )

        # Generate recommendations
        engine = RecommendationEngine(finder)
        report = engine.generate_report(threshold)

        # Display recommendations
        if report["recommendations"]:
            console.print("\n[bold cyan]📋 Recommendations:[/bold cyan]\n")
            for rec in report["recommendations"]:
                priority_color = {"high": "red", "medium": "yellow", "low": "green"}[rec["priority"]]
                console.print(f"[{priority_color}]• [{rec['priority'].upper()}][/{priority_color}] {rec['message']}")

        # Save to file if requested
        if output:
            validated_output = sanitize_output_path(output)
            output_data = {
                "score": {
                    "overall": score.overall_score,
                    "grade": score.grade,
                    "duplication": score.duplication_score,
                    "efficiency": score.coverage_efficiency_score,
                    "uniqueness": score.uniqueness_score,
                },
                "recommendations": report["recommendations"],
                "statistics": report["statistics"],
            }
            validated_output.write_text(json.dumps(output_data, indent=2))
            console.print(f"\n[green]✓ Quality report saved to {validated_output}[/green]")

    except TestIQError as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)
    except Exception as e:
        console.print(f"[red]Unexpected error: {e}[/red]")
        logger.exception("Error calculating quality score")
        sys.exit(1)


@main.group(name="baseline")
def baseline() -> None:
    """Manage analysis baselines for comparison."""
    pass


@baseline.command(name="list")
def baseline_list() -> None:
    """List all saved baselines."""
    baseline_mgr = BaselineManager(Path.home() / TESTIQ_CONFIG_DIR / "baselines")
    baselines = baseline_mgr.list_baselines()

    if not baselines:
        console.print("[yellow]No baselines found[/yellow]")
        return

    table = Table(title="Saved Baselines", show_header=True)
    table.add_column("Name", style="cyan")
    table.add_column("Tests", style="yellow")
    table.add_column("Duplicates", style="red")
    table.add_column("Date", style="green")

    for bl in baselines:
        table.add_row(
            bl["name"],
            str(bl["result"].total_tests),
            str(bl["result"].exact_duplicates),
            bl["result"].timestamp[:10],
        )

    console.print(table)


@baseline.command(name="show")
@click.argument("name")
def baseline_show(name: str) -> None:
    """Show details of a specific baseline."""
    baseline_mgr = BaselineManager(Path.home() / TESTIQ_CONFIG_DIR / "baselines")
    result = baseline_mgr.load(name)

    if not result:
        console.print(f"[red]Baseline '{name}' not found[/red]")
        sys.exit(1)

    console.print(
        Panel(
            f"[bold cyan]Baseline: {name}[/bold cyan]\n\n"
            f"Date: {result.timestamp[:10]}\n"
            f"Total Tests: {result.total_tests}\n"
            f"Exact Duplicates: {result.exact_duplicates}\n"
            f"Duplicate Groups: {result.duplicate_groups}\n"
            f"Subset Duplicates: {result.subset_duplicates}\n"
            f"Similar Pairs: {result.similar_pairs}\n"
            f"Duplicate %: {result.duplicate_percentage:.2f}%\n"
            f"Threshold: {result.threshold}",
            box=box.DOUBLE,
        )
    )


@baseline.command(name="delete")
@click.argument("name")
@click.option("--force", "-f", is_flag=True, help="Don't ask for confirmation")
def baseline_delete(name: str, force: bool) -> None:
    """Delete a baseline."""
    if not force and not click.confirm(f"Delete baseline '{name}'?"):
        console.print("[yellow]Cancelled[/yellow]")
        return

    baseline_mgr = BaselineManager(Path.home() / TESTIQ_CONFIG_DIR / "baselines")
    baseline_dir = baseline_mgr.baseline_dir / f"{name}.json"

    if baseline_dir.exists():
        baseline_dir.unlink()
        console.print(f"[green]✓ Baseline '{name}' deleted[/green]")
    else:
        console.print(f"[red]Baseline '{name}' not found[/red]")
        sys.exit(1)
