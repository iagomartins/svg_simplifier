"""Tests for Bezier curve operations."""

from __future__ import annotations

import math

import numpy as np
import pytest

from simplifier.bezier import (
    CubicBezier,
    QuadraticBezier,
    EllipticalArc,
    arc_to_beziers,
    fit_bezier_curve,
    fit_single_curve,
    split_curve,
)
from simplifier.geometry import create_point


class TestCubicBezier:
    """Test cubic Bezier curves."""

    def test_evaluate_start(self) -> None:
        """Test evaluation at start point."""
        curve = CubicBezier(
            create_point(0, 0),
            create_point(0.33, 0),
            create_point(0.67, 1),
            create_point(1, 1),
        )
        p = curve.evaluate(0)
        assert np.allclose(p, [0, 0])

    def test_evaluate_end(self) -> None:
        """Test evaluation at end point."""
        curve = CubicBezier(
            create_point(0, 0),
            create_point(0.33, 0),
            create_point(0.67, 1),
            create_point(1, 1),
        )
        p = curve.evaluate(1)
        assert np.allclose(p, [1, 1])

    def test_evaluate_midpoint(self) -> None:
        """Test evaluation at midpoint."""
        curve = CubicBezier(
            create_point(0, 0),
            create_point(0.5, 0),
            create_point(0.5, 1),
            create_point(1, 1),
        )
        p = curve.evaluate(0.5)
        assert 0 < p[0] < 1
        assert 0 < p[1] < 1

    def test_derivative(self) -> None:
        """Test derivative calculation."""
        curve = CubicBezier(
            create_point(0, 0),
            create_point(1, 0),
            create_point(1, 1),
            create_point(1, 1),
        )
        d = curve.derivative(0)
        assert d[0] > 0
        assert abs(d[1]) < 0.1

    def test_to_polyline(self) -> None:
        """Test polyline conversion."""
        curve = CubicBezier(
            create_point(0, 0),
            create_point(0.33, 0),
            create_point(0.67, 1),
            create_point(1, 1),
        )
        points = curve.to_polyline(4)
        assert len(points) == 5

    def test_reverse(self) -> None:
        """Test curve reversal."""
        curve = CubicBezier(
            create_point(0, 0),
            create_point(0.33, 0),
            create_point(0.67, 1),
            create_point(1, 1),
        )
        reversed_curve = curve.reverse()
        assert np.allclose(reversed_curve.p0, curve.p3)
        assert np.allclose(reversed_curve.p3, curve.p0)

    def test_is_degenerate(self) -> None:
        """Test degenerate curve detection."""
        curve = CubicBezier(
            create_point(0, 0),
            create_point(0, 0),
            create_point(0, 0),
            create_point(0, 0),
        )
        assert curve.is_degenerate()


class TestQuadraticBezier:
    """Test quadratic Bezier curves."""

    def test_to_cubic(self) -> None:
        """Test conversion to cubic."""
        quad = QuadraticBezier(
            create_point(0, 0),
            create_point(0.5, 1),
            create_point(1, 0),
        )
        cubic = quad.to_cubic()
        assert np.allclose(cubic.p0, quad.p0)
        assert np.allclose(cubic.p3, quad.p2)

    def test_evaluate(self) -> None:
        """Test evaluation."""
        quad = QuadraticBezier(
            create_point(0, 0),
            create_point(0.5, 1),
            create_point(1, 0),
        )
        p = quad.evaluate(0.5)
        assert 0 < p[0] < 1
        assert p[1] > 0


class TestArcConversion:
    """Test arc to Bezier conversion."""

    def test_arc_to_beziers_circle(self) -> None:
        """Test conversion of circular arc."""
        arc = EllipticalArc(
            cx=0, cy=0, rx=100, ry=100,
            phi=0, start_angle=0, delta_angle=math.pi / 2
        )
        curves = arc_to_beziers(arc)
        assert len(curves) > 0

    def test_arc_to_beziers_ellipse(self) -> None:
        """Test conversion of elliptical arc."""
        arc = EllipticalArc(
            cx=0, cy=0, rx=100, ry=50,
            phi=0, start_angle=0, delta_angle=math.pi
        )
        curves = arc_to_beziers(arc)
        assert len(curves) > 0

    def test_arc_full_circle(self) -> None:
        """Test full circle conversion."""
        arc = EllipticalArc(
            cx=0, cy=0, rx=50, ry=50,
            phi=0, start_angle=0, delta_angle=2 * math.pi
        )
        curves = arc_to_beziers(arc)
        assert len(curves) >= 4


class TestCurveFitting:
    """Test curve fitting algorithms."""

    def test_fit_single_curve_line(self) -> None:
        """Test fitting straight line."""
        points = np.array([[0, 0], [1, 0], [2, 0], [3, 0]], dtype=np.float64)
        curve = fit_single_curve(points)
        assert curve is not None
        assert np.allclose(curve.p0, [0, 0], atol=0.1)
        assert np.allclose(curve.p3, [3, 0], atol=0.1)

    def test_fit_bezier_curve_simple(self) -> None:
        """Test simple curve fitting."""
        points = np.array([[0, 0], [0.5, 0.5], [1, 0]], dtype=np.float64)
        curves = fit_bezier_curve(points, max_error=0.01)
        assert len(curves) >= 1

    def test_fit_bezier_curve_multiple(self) -> None:
        """Test fitting with multiple curves."""
        t = np.linspace(0, 2 * np.pi, 50)
        x = np.cos(t)
        y = np.sin(t)
        points = np.column_stack([x, y])
        curves = fit_bezier_curve(points, max_error=0.1)
        assert len(curves) >= 2


class TestCurveOperations:
    """Test curve operations."""

    def test_split_curve(self) -> None:
        """Test curve splitting."""
        curve = CubicBezier(
            create_point(0, 0),
            create_point(0.33, 0),
            create_point(0.67, 1),
            create_point(1, 1),
        )
        left, right = split_curve(curve, 0.5)
        assert np.allclose(left.p0, curve.p0)
        assert np.allclose(left.p3, right.p0)
        assert np.allclose(right.p3, curve.p3)

    def test_split_curve_at_start(self) -> None:
        """Test split at t=0."""
        curve = CubicBezier(
            create_point(0, 0),
            create_point(0.33, 0),
            create_point(0.67, 1),
            create_point(1, 1),
        )
        left, right = split_curve(curve, 0)
        assert np.allclose(left.p0, left.p3)
