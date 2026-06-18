"""SVG Simplifier - Production-ready SVG path geometry simplification.

This package provides tools for simplifying SVG path geometry while preserving
visual appearance. It implements advanced algorithms including:

- Adaptive curve flattening
- Douglas-Peucker simplification
- Schneider's Bézier curve fitting
- Curve merging and optimization

Example:
    >>> from simplifier import Simplifier
    >>> simplifier = Simplifier(tolerance=0.001)
    >>> result = simplifier.simplify_file("input.svg", "output.svg")
    >>> print(f"Reduced nodes by {result.reduction_percentage:.1f}%")

Attributes:
    __version__: Package version string.
"""

from simplifier.optimizer import Simplifier
from simplifier.parser import SVGParser
from simplifier.svg_writer import SVGWriter

__version__ = "1.0.0"
__all__ = ["Simplifier", "SVGParser", "SVGWriter"]
