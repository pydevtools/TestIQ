# TestIQ API Documentation

## Core Classes

### CoverageDuplicateFinder

The main class for analyzing test coverage and finding duplicates.

```python
from testiq.analyzer import CoverageDuplicateFinder

finder = CoverageDuplicateFinder(
    enable_parallel=True,    # Enable parallel processing
    max_workers=4,           # Number of worker threads
    enable_caching=True      # Enable result caching
)
```

#### Constructor Parameters

- **enable_parallel** (`bool`, default: `False`) - Enable parallel processing for large test suites
- **max_workers** (`int`, default: `4`) - Number of worker threads when parallel processing is enabled
- **enable_caching** (`bool`, default: `False`) - Cache analysis results for improved performance

#### Methods

##### add_test_coverage(test_name: str, coverage: Dict[str, List[int]])

Add coverage data for a single test.

**Parameters:**
- `test_name` - Unique identifier for the test
- `coverage` - Dictionary mapping file paths to lists of covered line numbers

**Example:**
```python
finder.add_test_coverage("test_login", {
    "auth.py": [10, 11, 12, 15, 20],
    "user.py": [5, 6, 7]
})
```

##### find_exact_duplicates() → List[List[str]]

Find tests with identical coverage.

**Returns:** List of groups, where each group contains test names with identical coverage

**Example:**
```python
exact = finder.find_exact_duplicates()
# [["test_login_1", "test_login_2"], ["test_auth_a", "test_auth_b", "test_auth_c"]]
```

##### find_subset_duplicates() → List[Tuple[str, str]]

Find tests that are subsets of other tests.

print(coverage.test_name)  # "test_login"
print(len(coverage.covered_lines))  # 3
```

---

## Class: CoverageDuplicateFinder

Main class for finding duplicate tests based on coverage analysis.

```python
from testiq import CoverageDuplicateFinder
```

### Constructor

```python
finder = CoverageDuplicateFinder()
```

Creates a new duplicate finder instance.

---

### Methods

#### add_test_coverage

Add coverage data for a single test.

**Signature:**

```python
def add_test_coverage(
    self,
    test_name: str,
    coverage: Dict[str, List[int]]
) -> None
```

**Parameters:**

- `test_name` (str): Name/identifier of the test
- `coverage` (Dict[str, List[int]]): Dictionary mapping filenames to lists of covered line numbers

**Returns:** None

**Example:**

```python
finder = CoverageDuplicateFinder()

finder.add_test_coverage("test_user_login", {
    "auth.py": [10, 11, 12, 15, 20],
    "user.py": [5, 6, 7]
})

finder.add_test_coverage("test_admin_login", {
    "auth.py": [10, 11, 12, 15, 20, 30],
    "user.py": [5, 6, 7],
    "admin.py": [100]
})
```

---

#### find_exact_duplicates

Find tests with identical coverage.

**Signature:**

```python
def find_exact_duplicates(self) -> List[List[str]]
```

**Returns:** List of test groups where each group has identical coverage.

**Example:**

```python
finder = CoverageDuplicateFinder()

finder.add_test_coverage("test_v1", {"file.py": [1, 2, 3]})
finder.add_test_coverage("test_v2", {"file.py": [1, 2, 3]})
finder.add_test_coverage("test_v3", {"file.py": [1, 2, 3]})
finder.add_test_coverage("test_different", {"file.py": [10, 20]})

duplicates = finder.find_exact_duplicates()
# [['test_v1', 'test_v2', 'test_v3']]
```

**Use Case:**

Tests with identical coverage are strong candidates for removal. Keep one test and remove the others to reduce redundancy.

---

#### find_subset_duplicates

Find tests where one test's coverage is completely contained in another.

**Signature:**

```python
def find_subset_duplicates(self) -> List[Tuple[str, str, float]]
```

**Returns:** List of tuples containing:
- `str`: Subset test name
- `str`: Superset test name
- `float`: Coverage ratio (0.0 to 1.0)

**Example:**

```python
finder = CoverageDuplicateFinder()

finder.add_test_coverage("test_minimal", {"file.py": [1, 2, 3]})
finder.add_test_coverage("test_complete", {"file.py": [1, 2, 3, 4, 5, 6, 7, 8, 9]})

subsets = finder.find_subset_duplicates()
# [('test_minimal', 'test_complete', 0.33)]
```

**Use Case:**

If a test's coverage is completely contained in another test, it may be redundant unless it tests specific edge cases or uses different inputs.

---

#### find_similar_coverage

Find tests with similar (but not identical) coverage using Jaccard similarity.

**Signature:**

```python
def find_similar_coverage(
    self,
    threshold: float = 0.8
) -> List[Tuple[str, str, float]]
```

**Parameters:**

- `threshold` (float): Minimum similarity ratio (0.0 to 1.0). Default: 0.8

**Returns:** List of tuples containing:
- `str`: First test name
- `str`: Second test name
- `float`: Similarity score (0.0 to 1.0)

Results are sorted by similarity score (descending).

**Example:**

```python
finder = CoverageDuplicateFinder()

finder.add_test_coverage("test_a", {"file.py": [1, 2, 3, 4, 5]})
finder.add_test_coverage("test_b", {"file.py": [1, 2, 3, 4, 10]})

similar = finder.find_similar_coverage(threshold=0.7)
# [('test_a', 'test_b', 0.67)]  # 4 common / 6 total = 0.67
```

**Similarity Calculation:**

Uses Jaccard similarity coefficient:

```
similarity = |A ∩ B| / |A ∪ B|
```

Where:
- `A` = lines covered by test A
- `B` = lines covered by test B
- `∩` = intersection (common lines)
- `∪` = union (all unique lines)

**Threshold Guidelines:**

- `0.9-1.0`: Very similar (likely duplicates)
- `0.7-0.9`: Similar (review for consolidation)
- `0.5-0.7`: Some overlap (may share common setup)
- `< 0.5`: Different tests

---

#### generate_report

Generate a comprehensive markdown report of all duplicate findings.

**Signature:**

```python
def generate_report(self) -> str
```

**Returns:** Markdown-formatted string containing:
- Exact duplicates
- Subset duplicates (top 10)
- Similar tests (top 10, threshold 0.7)
- Summary statistics

**Example:**

```python
finder = CoverageDuplicateFinder()

# Add tests...
finder.add_test_coverage("test1", {"file.py": [1, 2]})
finder.add_test_coverage("test2", {"file.py": [1, 2]})

report = finder.generate_report()
print(report)
```

**Output Example:**

```markdown
# Test Duplication Report

## Exact Duplicates (Identical Coverage)

Found 1 groups of tests with identical coverage:

### Group 1 (2 tests):
  - test1
  - test2

  **Action**: Keep one test, remove 1 duplicates

## Summary

- Total tests analyzed: 2
- Exact duplicates: 1 tests can be removed
- Subset duplicates: 0 tests may be redundant
- Similar tests: 0 pairs need review
```

---

## Complete Example

```python
from testiq import CoverageDuplicateFinder
import json

# Load coverage data
with open('coverage_data.json') as f:
    coverage_data = json.load(f)

# Create finder
finder = CoverageDuplicateFinder()

# Add all tests
for test_name, test_coverage in coverage_data.items():
    finder.add_test_coverage(test_name, test_coverage)

# Find duplicates
exact_dups = finder.find_exact_duplicates()
print(f"Found {len(exact_dups)} groups of exact duplicates")

for group in exact_dups:
    print(f"  Group: {', '.join(group)}")

# Find similar tests
similar = finder.find_similar_coverage(threshold=0.8)
print(f"\nFound {len(similar)} pairs of similar tests")

for test1, test2, similarity in similar[:5]:
    print(f"  {test1} ↔ {test2}: {similarity:.1%}")

# Generate full report
report = finder.generate_report()
with open('duplicate_report.md', 'w') as f:
    f.write(report)

print("\nReport saved to duplicate_report.md")
```

---

## Type Hints

TestIQ is fully type-annotated. Use with mypy for type checking:

```bash
mypy your_script.py
```

Example with type hints:

```python
from typing import Dict, List
from testiq import CoverageDuplicateFinder

def analyze_project_tests(coverage_file: str) -> None:
    finder: CoverageDuplicateFinder = CoverageDuplicateFinder()
    
    with open(coverage_file) as f:
        data: Dict[str, Dict[str, List[int]]] = json.load(f)
    
    for test_name, coverage in data.items():
        finder.add_test_coverage(test_name, coverage)
    
    duplicates: List[List[str]] = finder.find_exact_duplicates()
    print(f"Found {len(duplicates)} duplicate groups")
```

---

## Performance Considerations

### Time Complexity

- `add_test_coverage`: O(L) where L is the number of lines
- `find_exact_duplicates`: O(N × L) where N is number of tests
- `find_subset_duplicates`: O(N² × L)
- `find_similar_coverage`: O(N² × L)

### Space Complexity

- O(N × L) for storing all test coverage data

### Optimization Tips

1. **For large test suites** (>1000 tests):
   - Process in batches
   - Use higher similarity thresholds
   - Filter by file/module first

2. **Memory efficiency**:
   - Stream large coverage files
   - Clear finder after processing batches

Example for large suites:

```python
def analyze_large_suite(coverage_file: str, batch_size: int = 100):
    all_tests = load_all_tests(coverage_file)
    
    for i in range(0, len(all_tests), batch_size):
        batch = all_tests[i:i + batch_size]
        
        finder = CoverageDuplicateFinder()
        for test_name, coverage in batch.items():
            finder.add_test_coverage(test_name, coverage)
        
        # Process batch
        yield finder.find_exact_duplicates()
```

---

## See Also

- [CLI Reference](cli-reference.md) - Command-line interface
- [Integration Guide](integration.md) - Framework integration
- [FAQ](faq.md) - Common questions
