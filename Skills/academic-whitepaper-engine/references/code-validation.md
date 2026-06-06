# Code Validation Framework

Comprehensive testing and validation practices for academic whitepaper code examples.

## Testing Philosophy

**Executable truth:** Every code example must run successfully in isolation. Theoretical descriptions without working implementations undermine credibility.

**Reproducibility:** Virtual environment isolation ensures code works on fresh systems, not just your development machine.

**Documentation through tests:** Well-written tests serve as executable documentation showing intended usage.

## Virtual Environment Setup

### Creating Isolated Environment

```bash
# Python virtual environment
python3 -m venv .venv

# Activation (Unix/macOS)
source .venv/bin/activate

# Activation (Windows)
.venv\Scripts\activate

# Verify isolation
which python  # Should point to .venv/bin/python
```

### Dependency Management (No Version Pins)

**requirements.txt format:**
```
# CORRECT - flexibility for reproducibility
numpy
scipy
matplotlib
pytest
```

**Install dependencies:**
```bash
pip install -r requirements.txt

# Verify installation
pip list
```

**Why no version pins?**
- Allows users to integrate with existing projects
- Avoids dependency conflicts
- Prioritizes compatibility over strict reproducibility
- Trust in package maintainers' backward compatibility

**Exception:** Document minimum versions in README if absolutely necessary:
```markdown
## Requirements
- Python 3.9+
- NumPy (tested with 1.24+)
- SciPy (tested with 1.10+)
```

## Testing Framework: pytest

### Basic Test Structure

```python
# src/code-examples/test_fixed_point.py
import pytest
from fixed_point_combinator import fixed_point

def test_convergence_simple():
    """Test fixed point converges for simple function."""
    def f(x):
        return 0.5 * x + 1
    
    result = fixed_point(f, initial=0.0)
    assert abs(result - 2.0) < 1e-6, "Should converge to x=2"

def test_convergence_nonlinear():
    """Test fixed point for nonlinear function."""
    def f(x):
        return x**0.5 + 0.5
    
    result = fixed_point(f, initial=1.0)
    # Verify x = sqrt(x) + 0.5 solution
    assert abs(result - f(result)) < 1e-6

def test_max_iterations():
    """Test that max_iter prevents infinite loops."""
    def f(x):
        return x + 1  # Never converges
    
    result = fixed_point(f, initial=0.0, max_iter=100)
    # Should terminate after max_iter
    assert result is not None

def test_input_validation():
    """Test proper error handling."""
    with pytest.raises(TypeError):
        fixed_point("not a function", initial=0.0)
```

### Running Tests

```bash
# Run all tests
pytest src/code-examples/ -v

# Run specific test file
pytest src/code-examples/test_fixed_point.py -v

# Run with coverage
pytest src/code-examples/ --cov --cov-report=html

# Output:
# ============================= test session starts ==============================
# collected 4 items
#
# test_fixed_point.py::test_convergence_simple PASSED              [ 25%]
# test_fixed_point.py::test_convergence_nonlinear PASSED           [ 50%]
# test_fixed_point.py::test_max_iterations PASSED                  [ 75%]
# test_fixed_point.py::test_input_validation PASSED                [100%]
#
# ============================= 4 passed in 0.12s ================================
```

## Coverage Requirements

**Target: 90%+ coverage** for all code examples.

```bash
# Generate coverage report
pytest --cov=src/code-examples --cov-report=term-missing

# Sample output:
# Name                           Stmts   Miss  Cover   Missing
# ------------------------------------------------------------
# fixed_point_combinator.py         23      2    91%   45-46
# tensor_operations.py              31      0   100%
# frequency_encoder.py              18      3    83%   12, 28-29
# ------------------------------------------------------------
# TOTAL                             72      5    93%
```

**Improving coverage:**
```python
# Add tests for edge cases
def test_edge_case_zero():
    """Test behavior with zero initial value."""
    def f(x):
        return 0.1 * x
    result = fixed_point(f, initial=0.0)
    assert result == 0.0

def test_edge_case_negative():
    """Test with negative initial values."""
    def f(x):
        return -0.5 * x + 1
    result = fixed_point(f, initial=-10.0)
    assert abs(result - 0.666) < 1e-3
```

## Testing Tensor Operations

### Example: TGP Tensor Tests

```python
# src/code-examples/test_tensors.py
import pytest
import numpy as np
from tensor_operations import TensorGuidedOp, frechet_derivative

class TestTensorGuidedOp:
    def test_initialization(self):
        """Test TGP operator initialization."""
        op = TensorGuidedOp(dim=10, operation='frechet')
        assert op.dim == 10
        assert op.weights.shape == (10, 10)
    
    def test_forward_pass(self):
        """Test tensor operation forward pass."""
        op = TensorGuidedOp(dim=5)
        x = np.random.randn(5)
        result = op.forward(x)
        
        assert result.shape == (5,)
        assert not np.isnan(result).any()
    
    def test_frechet_derivative(self):
        """Test Fréchet derivative computation."""
        def f(x):
            return x**2
        
        x = np.array([1.0, 2.0, 3.0])
        h = np.array([0.1, 0.1, 0.1])
        
        deriv = frechet_derivative(f, x, h)
        expected = 2 * x * h  # Derivative of x^2
        
        np.testing.assert_allclose(deriv, expected, rtol=1e-5)
    
    @pytest.mark.parametrize("dim", [2, 5, 10, 20])
    def test_dimensionality_scaling(self, dim):
        """Test operation scales correctly across dimensions."""
        op = TensorGuidedOp(dim=dim)
        x = np.random.randn(dim)
        result = op.forward(x)
        assert result.shape == (dim,)
```

## Testing Frequency-Based Substrates

```python
# src/code-examples/test_frequency.py
import pytest
import numpy as np
from frequency_encoder import FrequencyBasedTokenizer, harmonic_signature

class TestFrequencyEncoder:
    def test_tokenization(self):
        """Test basic frequency-based tokenization."""
        tokenizer = FrequencyBasedTokenizer(phi_base=1.618)
        text = "recursive categorical framework"
        
        tokens = tokenizer.encode(text)
        assert len(tokens) > 0
        assert all(isinstance(t, complex) for t in tokens)
    
    def test_reconstruction(self):
        """Test that decoding recovers original text."""
        tokenizer = FrequencyBasedTokenizer()
        original = "tensor guided programming"
        
        encoded = tokenizer.encode(original)
        decoded = tokenizer.decode(encoded)
        
        # Allow minor differences due to floating-point
        assert decoded.lower() == original.lower()
    
    def test_harmonic_signature(self):
        """Test PHI-based harmonic signatures."""
        sig1 = harmonic_signature("test")
        sig2 = harmonic_signature("test")
        sig3 = harmonic_signature("different")
        
        # Same input -> same signature
        np.testing.assert_array_equal(sig1, sig2)
        # Different input -> different signature
        assert not np.array_equal(sig1, sig3)
```

## Performance Benchmarking

### Basic Timing

```python
import time

def test_performance_convergence():
    """Benchmark convergence speed."""
    def f(x):
        return 0.9 * x + 1
    
    start = time.time()
    result = fixed_point(f, initial=0.0, max_iter=1000)
    elapsed = time.time() - start
    
    assert elapsed < 0.01, f"Too slow: {elapsed:.4f}s"
    assert result is not None
```

### Using pytest-benchmark

```python
# Install: pip install pytest-benchmark

def test_benchmark_tensor_op(benchmark):
    """Benchmark tensor operation performance."""
    op = TensorGuidedOp(dim=100)
    x = np.random.randn(100)
    
    result = benchmark(op.forward, x)
    assert result.shape == (100,)

# Run with: pytest --benchmark-only
```

## Validation Scripts

### Automated Test Runner

```bash
#!/bin/bash
# scripts/run_tests.sh

set -e

echo "Creating virtual environment..."
python3 -m venv .venv
source .venv/bin/activate

echo "Installing dependencies..."
pip install -r requirements.txt

echo "Running tests..."
pytest src/code-examples/ -v --cov --cov-report=html

echo "Coverage report: htmlcov/index.html"

echo "Testing complete!"
```

### Pre-commit Hook

```bash
#!/bin/bash
# .git/hooks/pre-commit

# Run tests before allowing commit
pytest src/code-examples/ -q
if [ $? -ne 0 ]; then
    echo "Tests failed. Commit aborted."
    exit 1
fi
```

## Continuous Integration Example

```yaml
# .github/workflows/test.yml
name: Test Code Examples

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
      - name: Run tests
        run: |
          pytest src/code-examples/ --cov --cov-report=xml
      - name: Upload coverage
        uses: codecov/codecov-action@v3
```

## Documentation Testing

### Doctest Integration

```python
def fixed_point(f, initial, max_iter=100):
    """
    Compute least fixed point of function f.
    
    Args:
        f: Function to find fixed point for
        initial: Starting approximation
        max_iter: Maximum iterations
    
    Returns:
        X* such that f(X*) == X*
    
    Examples:
        >>> def f(x): return 0.5 * x + 1
        >>> result = fixed_point(f, 0.0)
        >>> abs(result - 2.0) < 1e-6
        True
        
        >>> def g(x): return x**0.5 + 0.5
        >>> result = fixed_point(g, 1.0)
        >>> abs(g(result) - result) < 1e-6
        True
    """
    x = initial
    for _ in range(max_iter):
        x_next = f(x)
        if abs(x_next - x) < 1e-9:
            return x
        x = x_next
    return x

# Run doctests
# python -m doctest fixed_point_combinator.py -v
```

## Quality Gates

Before finalizing whitepaper code:

1. **All tests pass:** `pytest src/code-examples/ -v`
2. **Coverage ≥90%:** `pytest --cov --cov-report=term`
3. **No linting errors:** `pylint src/code-examples/`
4. **Type checking:** `mypy src/code-examples/`
5. **Documentation complete:** All functions have docstrings

## Common Pitfalls

**Avoid:**
- Tests that depend on external network (mock APIs instead)
- Hard-coded file paths (use `pathlib` and relative paths)
- Floating-point exact equality (use `np.testing.assert_allclose`)
- Tests that modify global state
- Missing cleanup in fixtures (use `pytest.fixture` with `yield`)

**Example of proper fixture cleanup:**
```python
@pytest.fixture
def temp_directory():
    """Create temporary directory for test."""
    import tempfile
    import shutil
    
    tmpdir = tempfile.mkdtemp()
    yield tmpdir
    shutil.rmtree(tmpdir)  # Cleanup after test

def test_file_operations(temp_directory):
    """Test using temporary directory."""
    filepath = os.path.join(temp_directory, "test.txt")
    # ... test code ...
```
