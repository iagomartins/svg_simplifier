"""Tests for SVG parser."""

from __future__ import annotations

import math

import numpy as np
import pytest

from simplifier.parser import SVGParser, ParseResult, ParsedPath
from simplifier.bezier import CubicBezier
from simplifier.geometry import create_point


class TestSVGParser:
    """Test suite for SVG parser."""

    def test_parse_simple_rect(self, parser: SVGParser) -> None:
        """Test parsing simple rectangle."""
        svg = '''<svg xmlns="http://www.w3.org/2000/svg">
            <rect x="10" y="20" width="100" height="50"/>
        </svg>'''
        result = parser.parse_string(svg)
        assert len(result.paths) == 1
        assert result.paths[0].is_closed
        assert len(result.paths[0].curves) > 0

    def test_parse_circle(self, parser: SVGParser) -> None:
        """Test parsing circle element."""
        svg = '''<svg xmlns="http://www.w3.org/2000/svg">
            <circle cx="100" cy="100" r="50"/>
        </svg>'''
        result = parser.parse_string(svg)
        assert len(result.paths) == 1
        assert result.paths[0].is_closed

    def test_parse_ellipse(self, parser: SVGParser) -> None:
        """Test parsing ellipse element."""
        svg = '''<svg xmlns="http://www.w3.org/2000/svg">
            <ellipse cx="100" cy="100" rx="80" ry="40"/>
        </svg>'''
        result = parser.parse_string(svg)
        assert len(result.paths) == 1
        assert result.paths[0].is_closed

    def test_parse_line(self, parser: SVGParser) -> None:
        """Test parsing line element."""
        svg = '''<svg xmlns="http://www.w3.org/2000/svg">
            <line x1="0" y1="0" x2="100" y2="100"/>
        </svg>'''
        result = parser.parse_string(svg)
        assert len(result.paths) == 1
        assert not result.paths[0].is_closed

    def test_parse_polyline(self, parser: SVGParser) -> None:
        """Test parsing polyline element."""
        svg = '''<svg xmlns="http://www.w3.org/2000/svg">
            <polyline points="0,0 50,50 100,0"/>
        </svg>'''
        result = parser.parse_string(svg)
        assert len(result.paths) == 1
        assert not result.paths[0].is_closed
        assert len(result.paths[0].curves) == 2

    def test_parse_polygon(self, parser: SVGParser) -> None:
        """Test parsing polygon element."""
        svg = '''<svg xmlns="http://www.w3.org/2000/svg">
            <polygon points="0,0 100,0 50,100"/>
        </svg>'''
        result = parser.parse_string(svg)
        assert len(result.paths) == 1
        assert result.paths[0].is_closed

    def test_parse_path_with_m_l(self, parser: SVGParser) -> None:
        """Test parsing path with M and L commands."""
        svg = '''<svg xmlns="http://www.w3.org/2000/svg">
            <path d="M 0 0 L 100 0 L 100 100 Z"/>
        </svg>'''
        result = parser.parse_string(svg)
        assert len(result.paths) == 1
        assert result.paths[0].is_closed

    def test_parse_path_with_h_v(self, parser: SVGParser) -> None:
        """Test parsing path with H and V commands."""
        svg = '''<svg xmlns="http://www.w3.org/2000/svg">
            <path d="M 0 0 H 100 V 100 H 0 V 0 Z"/>
        </svg>'''
        result = parser.parse_string(svg)
        assert len(result.paths) == 1
        assert result.paths[0].is_closed

    def test_parse_path_with_cubic_bezier(self, parser: SVGParser) -> None:
        """Test parsing path with cubic Bezier commands."""
        svg = '''<svg xmlns="http://www.w3.org/2000/svg">
            <path d="M 0 0 C 50 0 50 100 100 100"/>
        </svg>'''
        result = parser.parse_string(svg)
        assert len(result.paths) == 1
        assert len(result.paths[0].curves) == 1
        curve = result.paths[0].curves[0]
        assert isinstance(curve, CubicBezier)

    def test_parse_path_with_quadratic_bezier(self, parser: SVGParser) -> None:
        """Test parsing path with quadratic Bezier commands."""
        svg = '''<svg xmlns="http://www.w3.org/2000/svg">
            <path d="M 0 0 Q 50 100 100 0"/>
        </svg>'''
        result = parser.parse_string(svg)
        assert len(result.paths) == 1
        assert len(result.paths[0].curves) == 1

    def test_parse_path_with_smooth_cubic(self, parser: SVGParser) -> None:
        """Test parsing path with smooth cubic commands (S)."""
        svg = '''<svg xmlns="http://www.w3.org/2000/svg">
            <path d="M 0 0 C 50 0 50 100 100 100 S 150 0 200 0"/>
        </svg>'''
        result = parser.parse_string(svg)
        assert len(result.paths) == 1
        assert len(result.paths[0].curves) == 2

    def test_parse_path_with_smooth_quadratic(self, parser: SVGParser) -> None:
        """Test parsing path with smooth quadratic commands (T)."""
        svg = '''<svg xmlns="http://www.w3.org/2000/svg">
            <path d="M 0 0 Q 50 100 100 0 T 200 0"/>
        </svg>'''
        result = parser.parse_string(svg)
        assert len(result.paths) == 1
        assert len(result.paths[0].curves) == 2

    def test_parse_path_with_arc(self, parser: SVGParser) -> None:
        """Test parsing path with arc commands."""
        svg = '''<svg xmlns="http://www.w3.org/2000/svg">
            <path d="M 100 100 A 50 50 0 1 1 150 150"/>
        </svg>'''
        result = parser.parse_string(svg)
        assert len(result.paths) == 1
        assert len(result.paths[0].curves) > 0

    def test_parse_relative_commands(self, parser: SVGParser) -> None:
        """Test parsing relative commands."""
        svg = '''<svg xmlns="http://www.w3.org/2000/svg">
            <path d="M 0 0 l 100 0 l 0 100 l -100 0 Z"/>
        </svg>'''
        result = parser.parse_string(svg)
        assert len(result.paths) == 1
        assert result.paths[0].is_closed

    def test_parse_viewbox(self, parser: SVGParser) -> None:
        """Test parsing viewBox attribute."""
        svg = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 500 300">
            <rect x="0" y="0" width="100" height="100"/>
        </svg>'''
        result = parser.parse_string(svg)
        assert result.viewbox == (0.0, 0.0, 500.0, 300.0)

    def test_parse_group_transform(self, parser: SVGParser) -> None:
        """Test parsing group with transform."""
        svg = '''<svg xmlns="http://www.w3.org/2000/svg">
            <g transform="translate(50, 50)">
                <rect x="0" y="0" width="100" height="100"/>
            </g>
        </svg>'''
        result = parser.parse_string(svg)
        assert len(result.paths) == 1

    def test_parse_multiple_paths(self, parser: SVGParser) -> None:
        """Test parsing multiple paths."""
        svg = '''<svg xmlns="http://www.w3.org/2000/svg">
            <path d="M 0 0 L 100 0" id="line1"/>
            <path d="M 0 50 L 100 50" id="line2"/>
            <path d="M 0 100 L 100 100" id="line3"/>
        </svg>'''
        result = parser.parse_string(svg)
        assert len(result.paths) == 3

    def test_parse_nested_groups(self, parser: SVGParser) -> None:
        """Test parsing nested groups."""
        svg = '''<svg xmlns="http://www.w3.org/2000/svg">
            <g transform="translate(10, 10)">
                <g transform="scale(2)">
                    <rect x="0" y="0" width="10" height="10"/>
                </g>
            </g>
        </svg>'''
        result = parser.parse_string(svg)
        assert len(result.paths) == 1

    def test_parse_empty_path(self, parser: SVGParser) -> None:
        """Test parsing empty path."""
        svg = '''<svg xmlns="http://www.w3.org/2000/svg">
            <path d=""/>
        </svg>'''
        result = parser.parse_string(svg)
        assert len(result.paths) == 0

    def test_count_total_nodes(self, parser: SVGParser) -> None:
        """Test node counting."""
        svg = '''<svg xmlns="http://www.w3.org/2000/svg">
            <path d="M 0 0 L 100 0"/>
        </svg>'''
        result = parser.parse_string(svg)
        assert result.count_total_nodes() == 4

    def test_get_bounding_box(self, parser: SVGParser) -> None:
        """Test bounding box calculation."""
        svg = '''<svg xmlns="http://www.w3.org/2000/svg">
            <rect x="10" y="20" width="100" height="50"/>
        </svg>'''
        result = parser.parse_string(svg)
        bbox = result.get_bounding_box()
        assert bbox[0] <= 10.0
        assert bbox[1] <= 20.0
        assert bbox[2] >= 110.0
        assert bbox[3] >= 70.0


class TestImplicitCommandRepetition:
    """Regression tests for SVG implicit command repetition (SVG spec requirement)."""

    def test_implicit_l_after_m(self, parser: SVGParser) -> None:
        """M followed by extra coords should be treated as implicit L commands."""
        svg = '''<svg xmlns="http://www.w3.org/2000/svg">
            <path d="M 0 0 10 0 10 10 0 10 Z"/>
        </svg>'''
        result = parser.parse_string(svg)
        assert len(result.paths) == 1
        assert result.paths[0].is_closed
        assert len(result.paths[0].curves) >= 4

    def test_implicit_l_repeat(self, parser: SVGParser) -> None:
        """L with multiple coordinate pairs should produce multiple line segments."""
        svg = '''<svg xmlns="http://www.w3.org/2000/svg">
            <path d="M 0 0 L 100 0 100 100 0 100 Z"/>
        </svg>'''
        result = parser.parse_string(svg)
        assert len(result.paths) == 1
        assert len(result.paths[0].curves) >= 4

    def test_implicit_c_repeat(self, parser: SVGParser) -> None:
        """C with multiple 6-value groups should produce multiple cubic curves."""
        svg = '''<svg xmlns="http://www.w3.org/2000/svg">
            <path d="M 0 0 C 50 0 50 100 100 100 150 100 150 0 200 0"/>
        </svg>'''
        result = parser.parse_string(svg)
        assert len(result.paths) == 1
        assert len(result.paths[0].curves) == 2

    def test_implicit_h_repeat(self, parser: SVGParser) -> None:
        """H with multiple values should produce multiple horizontal segments."""
        svg = '''<svg xmlns="http://www.w3.org/2000/svg">
            <path d="M 0 0 H 50 100 150"/>
        </svg>'''
        result = parser.parse_string(svg)
        assert len(result.paths) == 1
        assert len(result.paths[0].curves) == 3

    def test_implicit_v_repeat(self, parser: SVGParser) -> None:
        """V with multiple values should produce multiple vertical segments."""
        svg = '''<svg xmlns="http://www.w3.org/2000/svg">
            <path d="M 0 0 V 50 100 150"/>
        </svg>'''
        result = parser.parse_string(svg)
        assert len(result.paths) == 1
        assert len(result.paths[0].curves) == 3

    def test_implicit_q_repeat(self, parser: SVGParser) -> None:
        """Q with multiple 4-value groups should produce multiple quadratic curves."""
        svg = '''<svg xmlns="http://www.w3.org/2000/svg">
            <path d="M 0 0 Q 50 100 100 0 150 100 200 0"/>
        </svg>'''
        result = parser.parse_string(svg)
        assert len(result.paths) == 1
        assert len(result.paths[0].curves) == 2

    def test_z_after_implicit_coords_no_crash(self, parser: SVGParser) -> None:
        """Z immediately following implicit coordinate repetition must not crash."""
        svg = '''<svg xmlns="http://www.w3.org/2000/svg">
            <path d="M 0 0 L 100 0 100 100 0 100Z"/>
        </svg>'''
        result = parser.parse_string(svg)
        assert len(result.paths) == 1
        assert result.paths[0].is_closed

    def test_mixed_implicit_and_explicit_commands(self, parser: SVGParser) -> None:
        """Complex real-world path mixing implicit repeats and explicit commands."""
        svg = '''<svg xmlns="http://www.w3.org/2000/svg">
            <path d="M 10 10 L 90 10 90 90 C 90 95 85 100 80 100 20 100 10 90 10 80Z"/>
        </svg>'''
        result = parser.parse_string(svg)
        assert len(result.paths) == 1
        assert result.paths[0].is_closed
        assert len(result.paths[0].curves) >= 4


class TestParsedPath:
    """Test suite for ParsedPath class."""

    def test_count_nodes_empty(self) -> None:
        """Test node count for empty path."""
        path = ParsedPath()
        assert path.count_nodes() == 0

    def test_count_nodes_with_curves(self) -> None:
        """Test node count with curves."""
        curve = CubicBezier(
            create_point(0, 0),
            create_point(1, 0),
            create_point(1, 1),
            create_point(0, 1),
        )
        path = ParsedPath(curves=[curve])
        assert path.count_nodes() == 4

    def test_get_all_points(self) -> None:
        """Test getting all points."""
        curve = CubicBezier(
            create_point(0, 0),
            create_point(1, 0),
            create_point(1, 1),
            create_point(0, 1),
        )
        path = ParsedPath(curves=[curve])
        points = path.get_all_points()
        assert len(points) == 4
        assert np.allclose(points[0], [0, 0])
        assert np.allclose(points[3], [0, 1])


class TestParseResult:
    """Test suite for ParseResult class."""

    def test_count_total_nodes(self) -> None:
        """Test total node counting."""
        curve = CubicBezier(
            create_point(0, 0),
            create_point(1, 0),
            create_point(1, 1),
            create_point(0, 1),
        )
        path1 = ParsedPath(curves=[curve])
        path2 = ParsedPath(curves=[curve, curve])
        result = ParseResult(paths=[path1, path2])
        assert result.count_total_nodes() == 12
