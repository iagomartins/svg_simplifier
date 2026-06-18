"""Tests for optimizer."""

from __future__ import annotations

import numpy as np
import pytest

from simplifier.optimizer import (
    SimplificationOptions,
    SimplificationResult,
    Simplifier,
)
from simplifier.parser import SVGParser


class TestSimplificationOptions:
    """Test simplification options."""

    def test_default_options(self) -> None:
        """Test default options."""
        opts = SimplificationOptions()
        assert opts.tolerance == 0.001
        assert opts.max_error == 0.0005
        assert opts.merge_curves is True

    def test_custom_options(self) -> None:
        """Test custom options."""
        opts = SimplificationOptions(
            tolerance=0.01, max_error=0.005, merge_curves=False
        )
        assert opts.tolerance == 0.01
        assert opts.max_error == 0.005
        assert opts.merge_curves is False


class TestSimplificationResult:
    """Test simplification result."""

    def test_reduction_percentage(self) -> None:
        """Test reduction percentage calculation."""
        result = SimplificationResult(original_nodes=100, optimized_nodes=50)
        assert result.reduction_percentage == 0.5

    def test_reduction_zero_original(self) -> None:
        """Test with zero original nodes."""
        result = SimplificationResult(original_nodes=0, optimized_nodes=0)
        assert result.reduction_percentage == 0.0


class TestSimplifier:
    """Test main simplifier."""

    def test_init(self) -> None:
        """Test initialization."""
        simplifier = Simplifier()
        assert simplifier.options is not None

    def test_init_with_options(self) -> None:
        """Test initialization with options."""
        opts = SimplificationOptions(tolerance=0.01)
        simplifier = Simplifier(opts)
        assert simplifier.options.tolerance == 0.01

    def test_simplify_simple_path(self) -> None:
        """Test simplifying simple path."""
        svg = '''<svg xmlns="http://www.w3.org/2000/svg" width="100" height="100">
            <path d="M 0 0 L 10 0 L 20 0 L 30 0 L 40 0 L 50 0"/>
        </svg>'''
        parser = SVGParser()
        parse_result = parser.parse_string(svg)
        original_count = parse_result.count_total_nodes()

        simplifier = Simplifier(SimplificationOptions(tolerance=0.1))
        result = simplifier._simplify_parse_result(parse_result)

        assert result.optimized_nodes < original_count
        assert result.reduction_percentage > 0

    def test_simplify_straight_line(self) -> None:
        """Test that straight lines are reduced significantly."""
        svg = '''<svg xmlns="http://www.w3.org/2000/svg">
            <path d="M 0 0 L 1 0 L 2 0 L 3 0 L 4 0 L 5 0 L 6 0 L 7 0 L 8 0 L 9 0 L 10 0"/>
        </svg>'''
        simplifier = Simplifier(SimplificationOptions(tolerance=0.01))
        output, result = simplifier.simplify_string(svg)

        assert result.reduction_percentage > 0.5

    def test_simplify_preserves_corners(self) -> None:
        """Test that corners are preserved."""
        svg = '''<svg xmlns="http://www.w3.org/2000/svg">
            <path d="M 0 0 L 50 0 L 50 50"/>
        </svg>'''
        simplifier = Simplifier(SimplificationOptions(tolerance=1.0, corner_angle=0.1))
        output, result = simplifier.simplify_string(svg)

        assert result.reduction_percentage < 0.9

    def test_simplify_closed_path(self) -> None:
        """Test simplifying closed path."""
        svg = '''<svg xmlns="http://www.w3.org/2000/svg">
            <path d="M 0 0 L 100 0 L 100 100 L 0 100 Z"/>
        </svg>'''
        simplifier = Simplifier(SimplificationOptions(tolerance=0.1))
        output, result = simplifier.simplify_string(svg)

        assert "Z" in output

    def test_simplify_circle(self) -> None:
        """Test simplifying circle."""
        svg = '''<svg xmlns="http://www.w3.org/2000/svg">
            <circle cx="100" cy="100" r="50"/>
        </svg>'''
        simplifier = Simplifier(SimplificationOptions(tolerance=0.01))
        output, result = simplifier.simplify_string(svg)

        assert result.original_nodes > 0
        assert result.optimized_nodes > 0

    def test_simplify_rectangle(self) -> None:
        """Test simplifying rectangle."""
        svg = '''<svg xmlns="http://www.w3.org/2000/svg">
            <rect x="10" y="10" width="80" height="60"/>
        </svg>'''
        simplifier = Simplifier(SimplificationOptions(tolerance=0.1))
        output, result = simplifier.simplify_string(svg)

        assert result.paths[0].is_closed

    def test_simplify_empty_svg(self) -> None:
        """Test simplifying empty SVG."""
        svg = '''<svg xmlns="http://www.w3.org/2000/svg">
        </svg>'''
        simplifier = Simplifier()
        output, result = simplifier.simplify_string(svg)

        assert len(result.paths) == 0

    def test_simplify_curved_path(self) -> None:
        """Test simplifying curved path."""
        svg = '''<svg xmlns="http://www.w3.org/2000/svg">
            <path d="M 0 250 C 0 100 400 100 400 250" fill="none"/>
        </svg>'''
        simplifier = Simplifier(SimplificationOptions(tolerance=0.01))
        output, result = simplifier.simplify_string(svg)

        assert len(result.paths) == 1
        assert result.optimized_nodes > 0

    def test_simplify_with_arc(self) -> None:
        """Test simplifying arc path."""
        svg = '''<svg xmlns="http://www.w3.org/2000/svg">
            <path d="M 100 100 A 50 50 0 1 1 150 150" fill="none"/>
        </svg>'''
        simplifier = Simplifier(SimplificationOptions(tolerance=0.01))
        output, result = simplifier.simplify_string(svg)

        assert len(result.paths) == 1


class TestSimplifierOptions:
    """Test simplifier with different options."""

    def test_high_tolerance(self) -> None:
        """Test with high tolerance."""
        svg = '''<svg xmlns="http://www.w3.org/2000/svg">
            <path d="M 0 0 L 1 0 L 2 0 L 3 0 L 4 0"/>
        </svg>'''
        simplifier = Simplifier(SimplificationOptions(tolerance=10.0))
        output, result = simplifier.simplify_string(svg)

        assert result.reduction_percentage > 0.3

    def test_low_tolerance(self) -> None:
        """Test with low tolerance."""
        svg = '''<svg xmlns="http://www.w3.org/2000/svg">
            <path d="M 0 0 L 1 0 L 2 0 L 3 0 L 4 0"/>
        </svg>'''
        simplifier = Simplifier(SimplificationOptions(tolerance=0.001))
        output, result = simplifier.simplify_string(svg)

        assert result.reduction_percentage < 0.8

    def test_no_merge_curves(self) -> None:
        """Test without curve merging."""
        svg = '''<svg xmlns="http://www.w3.org/2000/svg">
            <path d="M 0 0 Q 50 100 100 0 Q 150 100 200 0"/>
        </svg>'''
        opts = SimplificationOptions(merge_curves=False)
        simplifier = Simplifier(opts)
        output, result = simplifier.simplify_string(svg)

        assert len(result.paths) == 1
