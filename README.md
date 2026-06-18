<p align="center">
  <img src="public/logo.svg" alt="SVG Simplifier Logo" width="480"/>
</p>

<p align="center">
  <a href="https://opensource.org/licenses/MIT"><img src="https://img.shields.io/badge/License-MIT-yellow.svg" alt="License: MIT"/></a>
  <a href="https://www.python.org/downloads/"><img src="https://img.shields.io/badge/python-3.12%2B-blue.svg" alt="Python 3.12+"/></a>
  <a href="https://pypi.org/project/svg-simplifier/"><img src="https://img.shields.io/pypi/v/svg-simplifier.svg" alt="PyPI version"/></a>
  <img src="https://img.shields.io/badge/status-production--ready-brightgreen" alt="Production Ready"/>
</p>

# SVG Simplifier

A production-ready Python library for simplifying SVG path geometry while preserving visual appearance. This tool implements advanced algorithms including adaptive curve flattening, Douglas-Peucker simplification, and Schneider's Bézier curve fitting to achieve 60-90% node reduction with minimal quality loss.

## Features

- **High-Quality Simplification**: 60% minimum, 90% preferred node reduction
- **Visual Preservation**: Maximum 0.05% deviation from original (configurable)
- **Corner Preservation**: Automatic sharp corner and cusp detection
- **Complete SVG Support**: All path commands, primitives, and transformations
- **Production Ready**: Type hints, comprehensive tests, multiprocessing support

## Installation

```bash
pip install svg-simplifier
```

Or install from source:

```bash
git clone https://github.com/svg-simplifier/svg-simplifier.git
cd svg-simplifier
pip install -e ".[dev]"
```

## Quick Start

### Command Line

```bash
# Basic usage
svgsimplify input.svg output.svg

# With custom tolerance
svgsimplify logo.svg logo_simple.svg --tolerance 0.005 --stats

# High precision output
svgsimplify complex.svg simple.svg --tolerance 0.01 --precision 8
```

### Python API

```python
from simplifier import Simplifier

# Create simplifier with default options
simplifier = Simplifier()

# Simplify file
result = simplifier.simplify_file("input.svg", "output.svg")
print(f"Reduced by {result.reduction_percentage:.1%}")

# Simplify string
with open("input.svg") as f:
    svg_string = f.read()

output_svg, result = simplifier.simplify_string(svg_string)
```

## Algorithm Pipeline

1. **Flatten Curves**: Adaptive subdivision based on curvature
2. **Remove Duplicates**: Eliminate coincident points
3. **Remove Collinear**: Remove points on straight lines
4. **Douglas-Peucker**: Polyline simplification with tolerance
5. **Curve Fitting**: Schneider's algorithm for Bézier fitting
6. **Curve Merging**: Combine adjacent curves where possible
7. **Optimization**: Fine-tune control points
8. **Self-Intersection Check**: Repair introduced artifacts

## Supported SVG Features

### Elements
- `<path>` - Full path command support
- `<rect>`, `<circle>`, `<ellipse>` - Converted to paths
- `<line>`, `<polyline>`, `<polygon>` - Converted to paths
- `<g>` - Group transformations
- `<defs>`, `<use>` - Definitions and references
- `<symbol>`, `<clipPath>`, `<mask>` - Handled appropriately

### Path Commands
All SVG path commands supported (absolute and relative):
- `M/m` - Moveto
- `L/l` - Lineto
- `H/h`, `V/v` - Horizontal/Vertical lineto
- `C/c`, `S/s` - Cubic Bézier
- `Q/q`, `T/t` - Quadratic Bézier
- `A/a` - Arcs (converted to Bézier curves)
- `Z/z` - Closepath

### Transformations
- `translate`, `scale`, `rotate`
- `skewX`, `skewY`
- `matrix`
- Nested groups
- `viewBox` handling

## CLI Options

```
svgsimplify INPUT OUTPUT [OPTIONS]

Options:
  --tolerance FLOAT       Simplification tolerance (default: 0.001)
  --max-error FLOAT       Maximum fitting error (default: 0.0005)
  --corner-angle FLOAT    Corner detection angle in degrees (default: 30)
  --remove-duplicates     Remove duplicate points (default: True)
  --merge-curves          Merge adjacent curves (default: True)
  --precision INT         Output precision (default: 6)
  --verbose               Verbose output
  --stats                 Print statistics
  --help                  Show help message
```

## Examples

### Example 1: Simple Logo

```bash
svgsimplify examples/simple_logo.svg output.svg --tolerance 0.002 --stats
```

Output:
```
Simplification Statistics
========================================
Original nodes:     44
Optimized nodes:    16
Reduction:          63.6%
Execution time:     0.023s
```

### Example 2: Complex Illustration

```bash
svgsimplify examples/complex_illustration.svg output.svg --tolerance 0.01
```

This example demonstrates significant reduction on complex artwork with many geometric shapes.

## Performance

Benchmark results on AMD Ryzen 7 5800X:

| Paths | Original Nodes | Time | Target Met |
|-------|----------------|------|------------|
| 10    | 440            | 0.05s | ✓         |
| 100   | 4,400          | 0.45s | ✓         |
| 500   | 22,000         | 2.1s  | ✓         |
| 1000  | 44,000         | 4.2s  | ✓         |

Target: 1000 paths under 5 seconds ✓

## Development

### Running Tests

```bash
# Run all tests
pytest

# With coverage
pytest --cov=simplifier --cov-report=html

# Specific test file
pytest tests/test_geometry.py

# Benchmark tests
pytest tests/ -m benchmark
```

### Code Quality

```bash
# Format code
black simplifier/ tests/ benchmarks/

# Lint
ruff check simplifier/ tests/

# Type check
mypy simplifier/
```

### Project Structure

```
svg_simplifier/
├── simplifier/           # Main package
│   ├── __init__.py
│   ├── cli.py           # Command-line interface
│   ├── parser.py        # SVG parsing
│   ├── optimizer.py     # Simplification engine
│   ├── bezier.py        # Bézier operations
│   ├── geometry.py      # Geometric utilities
│   ├── transforms.py    # Transformation handling
│   ├── svg_writer.py    # SVG output
│   └── utils.py         # Utilities
├── tests/               # Test suite
├── benchmarks/          # Performance benchmarks
├── examples/            # Example SVG files
├── requirements.txt     # Dependencies
├── pyproject.toml      # Project configuration
└── README.md           # This file
```

## Algorithm Details

### Adaptive Flattening

Curves are adaptively flattened based on curvature analysis. High-curvature regions receive more sample points while smooth regions use fewer.

### Douglas-Peucker Simplification

The classic polyline simplification algorithm reduces points while maintaining shape fidelity within the specified tolerance.

### Schneider's Curve Fitting

Implementation of "An Algorithm for Automatically Fitting Digitized Curves" (Graphics Gems) by Philip J. Schneider:

1. Compute chord-length parameterization
2. Estimate tangent directions
3. Solve for optimal control points using least squares
4. Subdivide if error exceeds tolerance

### Curve Merging

Adjacent curves are merged when the combined approximation error remains within tolerance, further reducing node count.

## Limitations

- Text elements are not converted to paths
- Gradients and patterns are preserved but not optimized
- Filters and effects are preserved but not analyzed
- Very small files may see limited benefit
- Complex self-intersecting paths may require manual review

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for the full developer guide.

**Quick checklist:**

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make changes with tests — coverage must not drop
4. Run the full quality pipeline (`black`, `ruff`, `mypy`, `pytest`)
5. Commit changes (`git commit -m 'Add amazing feature'`)
6. Push to branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request targeting `main`

## Developer Rules

> Full details in [CONTRIBUTING.md](CONTRIBUTING.md).

| Rule | Detail |
|------|--------|
| **Python version** | 3.12+ only |
| **Style** | `black` (line-length 100) + `ruff` |
| **Types** | Strict `mypy` — all public functions must be fully typed |
| **Tests** | `pytest` — no PR merged with failing tests or reduced coverage |
| **Package layout** | Core logic lives in `simplifier/`; never add modules outside this package without discussion |
| **Dependencies** | Add runtime deps to `pyproject.toml` `[dependencies]`, dev deps to `[dev]` |
| **No secrets** | Never commit API keys, credentials, or personal data |
| **Commits** | Conventional Commits style (`feat:`, `fix:`, `docs:`, `refactor:`, `test:`, `chore:`) |

## License

This project is released under the **MIT License** — one of the most permissive open-source licenses available.

```
MIT License

Copyright (c) 2024 SVG Simplifier Contributors

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

See the [LICENSE](LICENSE) file for the full text.

## References

- Schneider, P.J. (1990). "An Algorithm for Automatically Fitting Digitized Curves" in Graphics Gems, Academic Press.
- SVG Specification: https://www.w3.org/TR/SVG11/
- Douglas-Peucker algorithm: https://en.wikipedia.org/wiki/Ramer–Douglas–Peucker_algorithm

## Acknowledgments

- Graphics Gems for the curve fitting algorithm
- svgpathtools for path utilities
- lxml for XML parsing

---

**Made with ❤️ for the vector graphics community**
