"""Bézier curve operations and fitting algorithms.

This module provides cubic and quadratic Bézier curve operations, including
arc approximation, adaptive flattening, and Schneider's curve fitting algorithm.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import TYPE_CHECKING

import numpy as np
from numpy.linalg import lstsq
from numpy.typing import NDArray

from simplifier.geometry import (
    Point,
    PointSequence,
    angle_between_vectors,
    create_point,
    line_point_distance,
    point_distance,
)

if TYPE_CHECKING:
    from collections.abc import Sequence


@dataclass(frozen=True)
class CubicBezier:
    """Cubic Bézier curve.

    Attributes:
        p0: Start point.
        p1: First control point.
        p2: Second control point.
        p3: End point.
    """

    p0: Point
    p1: Point
    p2: Point
    p3: Point

    def evaluate(self, t: float) -> Point:
        """Evaluate curve at parameter t.

        Args:
            t: Parameter value between 0 and 1.

        Returns:
            Point on curve at parameter t.
        """
        t2 = t * t
        t3 = t2 * t
        mt = 1 - t
        mt2 = mt * mt
        mt3 = mt2 * mt

        return mt3 * self.p0 + 3 * mt2 * t * self.p1 + 3 * mt * t2 * self.p2 + t3 * self.p3

    def derivative(self, t: float) -> Point:
        """Evaluate first derivative at parameter t.

        Args:
            t: Parameter value between 0 and 1.

        Returns:
            First derivative vector at parameter t.
        """
        mt = 1 - t
        return (
            3 * mt * mt * (self.p1 - self.p0)
            + 6 * mt * t * (self.p2 - self.p1)
            + 3 * t * t * (self.p3 - self.p2)
        )

    def second_derivative(self, t: float) -> Point:
        """Evaluate second derivative at parameter t.

        Args:
            t: Parameter value between 0 and 1.

        Returns:
            Second derivative vector at parameter t.
        """
        return (
            6 * (1 - t) * (self.p2 - 2 * self.p1 + self.p0)
            + 6 * t * (self.p3 - 2 * self.p2 + self.p1)
        )

    def curvature(self, t: float) -> float:
        """Compute curvature at parameter t.

        Args:
            t: Parameter value between 0 and 1.

        Returns:
            Curvature value.
        """
        d1 = self.derivative(t)
        d2 = self.second_derivative(t)

        cross = abs(d1[0] * d2[1] - d1[1] * d2[0])
        d1_norm = np.linalg.norm(d1)

        if d1_norm < 1e-10:
            return 0.0

        return cross / (d1_norm**3)

    def to_polyline(self, num_segments: int = 100) -> PointSequence:
        """Convert to polyline by sampling.

        Args:
            num_segments: Number of segments to sample.

        Returns:
            Array of sampled points.
        """
        t_values = np.linspace(0, 1, num_segments + 1)
        return np.array([self.evaluate(t) for t in t_values], dtype=np.float64)

    def reverse(self) -> CubicBezier:
        """Return reversed curve.

        Returns:
            Curve with reversed direction.
        """
        return CubicBezier(self.p3, self.p2, self.p1, self.p0)

    def is_degenerate(self, tolerance: float = 1e-10) -> bool:
        """Check if curve is degenerate (all points coincident).

        Args:
            tolerance: Distance tolerance.

        Returns:
            True if curve is degenerate.
        """
        points = [self.p0, self.p1, self.p2, self.p3]
        for i in range(1, len(points)):
            if point_distance(points[i], points[0]) > tolerance:
                return False
        return True


@dataclass(frozen=True)
class QuadraticBezier:
    """Quadratic Bézier curve.

    Attributes:
        p0: Start point.
        p1: Control point.
        p2: End point.
    """

    p0: Point
    p1: Point
    p2: Point

    def to_cubic(self) -> CubicBezier:
        """Convert to equivalent cubic Bézier.

        Returns:
            Equivalent cubic Bézier curve.
        """
        c1 = self.p0 + (2.0 / 3.0) * (self.p1 - self.p0)
        c2 = self.p2 + (2.0 / 3.0) * (self.p1 - self.p2)
        return CubicBezier(self.p0, c1, c2, self.p2)

    def evaluate(self, t: float) -> Point:
        """Evaluate curve at parameter t.

        Args:
            t: Parameter value between 0 and 1.

        Returns:
            Point on curve at parameter t.
        """
        mt = 1 - t
        return mt * mt * self.p0 + 2 * mt * t * self.p1 + t * t * self.p2


@dataclass(frozen=True)
class EllipticalArc:
    """Elliptical arc parameters.

    Attributes:
        cx: Center X coordinate.
        cy: Center Y coordinate.
        rx: X radius.
        ry: Y radius.
        phi: Rotation angle in radians.
        start_angle: Start angle in radians.
        delta_angle: Arc sweep angle in radians.
    """

    cx: float
    cy: float
    rx: float
    ry: float
    phi: float
    start_angle: float
    delta_angle: float


def arc_to_beziers(arc: EllipticalArc) -> list[CubicBezier]:
    """Convert elliptical arc to cubic Bézier curves.

    Implementation based on SVG specification arc approximation.

    Args:
        arc: Elliptical arc parameters.

    Returns:
        List of cubic Bézier curves approximating the arc.
    """
    curves = []

    num_segments = max(
        1, int(math.ceil(abs(arc.delta_angle) / (math.pi / 2)))
    )

    eta1 = arc.start_angle
    eta2 = arc.start_angle + arc.delta_angle

    cos_phi = math.cos(arc.phi)
    sin_phi = math.sin(arc.phi)

    for i in range(num_segments):
        eta_start = eta1 + (eta2 - eta1) * i / num_segments
        eta_end = eta1 + (eta2 - eta1) * (i + 1) / num_segments
        delta_eta = eta_end - eta_start

        alpha = math.sin(delta_eta) * (math.sqrt(4 + 3 * math.tan(delta_eta / 2) ** 2) - 1) / 3

        cos_start = math.cos(eta_start)
        sin_start = math.sin(eta_start)
        cos_end = math.cos(eta_end)
        sin_end = math.sin(eta_end)

        ep1x = arc.cx + arc.rx * cos_phi * cos_start - arc.ry * sin_phi * sin_start
        ep1y = arc.cy + arc.rx * sin_phi * cos_start + arc.ry * cos_phi * sin_start

        ep2x = arc.cx + arc.rx * cos_phi * cos_end - arc.ry * sin_phi * sin_end
        ep2y = arc.cy + arc.rx * sin_phi * cos_end + arc.ry * cos_phi * sin_end

        dpx = -arc.rx * cos_phi * sin_start - arc.ry * sin_phi * cos_start
        dpy = -arc.rx * sin_phi * sin_start + arc.ry * cos_phi * cos_start

        dqx = -arc.rx * cos_phi * sin_end - arc.ry * sin_phi * cos_end
        dqy = -arc.rx * sin_phi * sin_end + arc.ry * cos_phi * cos_end

        alpha_p = math.sin(eta_end - eta_start)
        alpha = (
            math.sin(eta_end - eta_start)
            * (math.sqrt(4 + 3 * math.tan((eta_end - eta_start) / 2) ** 2) - 1)
            / 3
        )

        cp1x = ep1x + alpha * dpx
        cp1y = ep1y + alpha * dpy
        cp2x = ep2x - alpha * dqx
        cp2y = ep2y - alpha * dqy

        curves.append(
            CubicBezier(
                create_point(ep1x, ep1y),
                create_point(cp1x, cp1y),
                create_point(cp2x, cp2y),
                create_point(ep2x, ep2y),
            )
        )

    return curves


def adaptive_flatten(
    curve: CubicBezier, angle_tolerance: float = 0.1, recursion_limit: int = 10
) -> PointSequence:
    """Adaptively flatten curve based on curvature.

    Args:
        curve: Cubic Bézier curve to flatten.
        angle_tolerance: Maximum angle deviation in radians.
        recursion_limit: Maximum recursion depth.

    Returns:
        Array of points approximating the curve.
    """
    points: list[Point] = []

    def flatten_segment(c: CubicBezier, depth: int) -> None:
        if depth >= recursion_limit:
            points.extend([c.p0, c.p3])
            return

        mid_t = 0.5
        mid = c.evaluate(mid_t)

        v1 = c.p1 - c.p0
        v2 = c.p3 - c.p2

        if np.linalg.norm(v1) < 1e-10 or np.linalg.norm(v2) < 1e-10:
            points.extend([c.p0, c.p3])
            return

        angle = angle_between_vectors(v1, v2)

        if angle < angle_tolerance:
            points.extend([c.p0, c.p3])
        else:
            left, right = split_curve(c, 0.5)
            flatten_segment(left, depth + 1)
            flatten_segment(right, depth + 1)

    flatten_segment(curve, 0)

    unique_points = [points[0]]
    for p in points[1:]:
        if point_distance(p, unique_points[-1]) > 1e-10:
            unique_points.append(p)

    return np.array(unique_points, dtype=np.float64)


def split_curve(curve: CubicBezier, t: float) -> tuple[CubicBezier, CubicBezier]:
    """Split curve at parameter t using de Casteljau algorithm.

    Args:
        curve: Cubic Bézier curve to split.
        t: Split parameter between 0 and 1.

    Returns:
        Tuple of (left_curve, right_curve).
    """
    mt = 1 - t

    p01 = mt * curve.p0 + t * curve.p1
    p12 = mt * curve.p1 + t * curve.p2
    p23 = mt * curve.p2 + t * curve.p3

    p012 = mt * p01 + t * p12
    p123 = mt * p12 + t * p23

    p0123 = mt * p012 + t * p123

    left = CubicBezier(curve.p0, p01, p012, p0123)
    right = CubicBezier(p0123, p123, p23, curve.p3)

    return left, right


def fit_bezier_curve(
    points: PointSequence, max_error: float, corner_angle: float = np.pi / 6
) -> list[CubicBezier]:
    """Fit cubic Bézier curves to polyline using Schneider's algorithm.

    Implementation of "An Algorithm for Automatically Fitting Digitized Curves"
    by Philip J. Schneider (Graphics Gems).

    Args:
        points: Array of points to fit.
        max_error: Maximum allowed error.
        corner_angle: Angle threshold for detecting corners.

    Returns:
        List of fitted cubic Bézier curves.
    """
    if len(points) < 2:
        return []

    if len(points) == 2:
        curve = fit_line_segment(points[0], points[-1])
        return [curve] if curve else []

    from simplifier.geometry import split_at_corners

    segments = split_at_corners(points, corner_angle)
    curves = []

    for segment in segments:
        if len(segment) < 2:
            continue

        segment_curves = fit_curve_segment(segment, max_error)
        curves.extend(segment_curves)

    return curves


def fit_line_segment(p1: Point, p2: Point) -> CubicBezier | None:
    """Create degenerate cubic Bézier representing line segment.

    Args:
        p1: Start point.
        p2: End point.

    Returns:
        Cubic Bézier curve representing the line.
    """
    if point_distance(p1, p2) < 1e-10:
        return None

    c1 = p1 + (1.0 / 3.0) * (p2 - p1)
    c2 = p1 + (2.0 / 3.0) * (p2 - p1)

    return CubicBezier(p1, c1, c2, p2)


def fit_curve_segment(points: PointSequence, max_error: float) -> list[CubicBezier]:
    """Fit curve to a smooth segment of points.

    Args:
        points: Array of points (assumed to be a smooth segment).
        max_error: Maximum allowed error.

    Returns:
        List of fitted curves.
    """
    if len(points) < 2:
        return []

    if len(points) == 2:
        curve = fit_line_segment(points[0], points[1])
        return [curve] if curve else []

    curve = fit_single_curve(points)
    max_deviation = compute_max_error(points, curve)

    if max_deviation < max_error:
        return [curve]

    if len(points) == 3:
        curve = fit_line_segment(points[0], points[-1])
        return [curve] if curve else []

    best_split = find_best_split(points)

    left_curves = fit_curve_segment(points[: best_split + 1], max_error)
    right_curves = fit_curve_segment(points[best_split:], max_error)

    return left_curves + right_curves


def fit_single_curve(points: PointSequence) -> CubicBezier:
    """Fit single cubic Bézier to set of points.

    Args:
        points: Array of points to fit.

    Returns:
        Fitted cubic Bézier curve.
    """
    n = len(points) - 1

    if n < 1:
        raise ValueError("Need at least 2 points to fit curve")

    if n == 1:
        return fit_line_segment(points[0], points[1])

    chord = points[-1] - points[0]
    chord_len = np.linalg.norm(chord)

    if chord_len < 1e-10:
        return CubicBezier(points[0], points[0], points[-1], points[-1])

    params = compute_chord_length_params(points)

    tan_left = compute_tangent(points, 0, 3)
    tan_right = compute_tangent(points, n, 3)

    if np.linalg.norm(tan_left) < 1e-10:
        tan_left = chord / chord_len
    else:
        tan_left = tan_left / np.linalg.norm(tan_left)

    if np.linalg.norm(tan_right) < 1e-10:
        tan_right = -chord / chord_len
    else:
        tan_right = tan_right / np.linalg.norm(tan_right)

    alpha_a, alpha_b = compute_control_points(points, params, tan_left, tan_right)

    c1 = points[0] + alpha_a * tan_left
    c2 = points[-1] + alpha_b * tan_right

    return CubicBezier(points[0], c1, c2, points[-1])


def compute_chord_length_params(points: PointSequence) -> NDArray[np.float64]:
    """Compute chord-length parameterization for points.

    Args:
        points: Array of points.

    Returns:
        Array of parameter values in [0, 1].
    """
    n = len(points) - 1
    params = np.zeros(n + 1)

    total_length = 0.0
    for i in range(1, n + 1):
        total_length += point_distance(points[i], points[i - 1])

    if total_length == 0:
        return np.linspace(0, 1, n + 1)

    current_length = 0.0
    for i in range(1, n + 1):
        current_length += point_distance(points[i], points[i - 1])
        params[i] = current_length / total_length

    return params


def compute_tangent(
    points: PointSequence, index: int, neighbor_count: int = 2
) -> Point:
    """Compute tangent at point using neighboring points.

    Args:
        points: Array of points.
        index: Index of point to compute tangent for.
        neighbor_count: Number of neighbors to use on each side.

    Returns:
        Tangent vector (not normalized).
    """
    n = len(points) - 1

    if n < 1:
        return create_point(1, 0)

    if n == 1:
        return points[1] - points[0]

    start = max(0, index - neighbor_count)
    end = min(n, index + neighbor_count)

    if start == end:
        return points[min(index + 1, n)] - points[max(index - 1, 0)]

    weighted_sum = np.zeros(2, dtype=np.float64)
    total_weight = 0.0

    for i in range(start, end):
        if i == index:
            continue
        weight = 1.0 / abs(i - index)
        vec = points[i] - points[index]
        weighted_sum += weight * vec
        total_weight += weight

    if total_weight == 0:
        return points[min(index + 1, n)] - points[max(index - 1, 0)]

    return weighted_sum / total_weight


def compute_control_points(
    points: PointSequence,
    params: NDArray[np.float64],
    tan_left: Point,
    tan_right: Point,
) -> tuple[float, float]:
    """Compute optimal control point distances using least squares.

    Args:
        points: Array of points to fit.
        params: Parameter values for each point.
        tan_left: Left tangent direction (normalized).
        tan_right: Right tangent direction (normalized).

    Returns:
        Tuple of (alpha_a, alpha_b) control point distances.
    """
    n = len(points) - 1

    a = np.zeros((n - 1, 2), dtype=np.float64)
    b = np.zeros((n - 1, 2), dtype=np.float64)
    c = np.zeros((n - 1, 2), dtype=np.float64)

    for i in range(1, n):
        t = params[i]
        mt = 1 - t
        a[i - 1] = 3 * mt * mt * t * tan_left
        b[i - 1] = 3 * mt * t * t * tan_right
        c[i - 1] = (
            points[i]
            - (mt * mt * mt * points[0])
            - (3 * mt * mt * t * points[0])
            - (3 * mt * t * t * points[n])
            - (t * t * t * points[n])
        )

    A = np.zeros((2, 2), dtype=np.float64)
    C = np.zeros(2, dtype=np.float64)

    for i in range(n - 1):
        A[0, 0] += np.dot(a[i], a[i])
        A[0, 1] += np.dot(a[i], b[i])
        A[1, 0] = A[0, 1]
        A[1, 1] += np.dot(b[i], b[i])
        C[0] += np.dot(a[i], c[i])
        C[1] += np.dot(b[i], c[i])

    det = A[0, 0] * A[1, 1] - A[0, 1] * A[1, 0]

    if abs(det) < 1e-10:
        chord = points[-1] - points[0]
        chord_len = np.linalg.norm(chord) / 3.0
        return (chord_len, chord_len)

    alpha_a = (C[0] * A[1, 1] - C[1] * A[0, 1]) / det
    alpha_b = (C[1] * A[0, 0] - C[0] * A[1, 0]) / det

    alpha_a = max(0, alpha_a)
    alpha_b = max(0, alpha_b)

    return (alpha_a, alpha_b)


def compute_max_error(curve: CubicBezier, points: PointSequence) -> float:
    """Compute maximum distance from points to fitted curve.

    Args:
        curve: Fitted curve.
        points: Original points.

    Returns:
        Maximum error distance.
    """
    max_error = 0.0

    params = compute_chord_length_params(points)

    for i in range(1, len(points) - 1):
        t = params[i]
        point_on_curve = curve.evaluate(t)
        error = point_distance(points[i], point_on_curve)
        max_error = max(max_error, error)

    return max_error


def find_best_split(points: PointSequence) -> int:
    """Find best point to split curve for fitting.

    Args:
        points: Array of points.

    Returns:
        Index to split at.
    """
    n = len(points) - 1

    if n <= 2:
        return n // 2

    best_split = n // 2
    best_score = float("inf")

    for i in range(2, n - 1):
        left_curve = fit_single_curve(points[: i + 1])
        right_curve = fit_single_curve(points[i:])

        left_error = compute_max_error(left_curve, points[: i + 1])
        right_error = compute_max_error(right_curve, points[i:])

        score = max(left_error, right_error)
        if score < best_score:
            best_score = score
            best_split = i

    return best_split


def merge_curves(curve1: CubicBezier, curve2: CubicBezier, tolerance: float = 0.01) -> CubicBezier | None:
    """Attempt to merge two adjacent curves into one.

    Args:
        curve1: First curve.
        curve2: Second curve.
        tolerance: Maximum error for merging.

    Returns:
        Merged curve if successful, None otherwise.
    """
    if point_distance(curve1.p3, curve2.p0) > tolerance:
        return None

    points1 = curve1.to_polyline(10)
    points2 = curve2.to_polyline(10)

    all_points = np.vstack([points1[:-1], points2])

    merged = fit_single_curve(all_points)

    max_error = max(
        compute_max_error(merged, all_points),
    )

    if max_error < tolerance:
        return merged

    return None


def optimize_control_points(curve: CubicBezier, points: PointSequence) -> CubicBezier:
    """Optimize control points of fitted curve for better accuracy.

    Args:
        curve: Initial fitted curve.
        points: Original points to match.

    Returns:
        Optimized curve.
    """
    def error_function(control_params: NDArray[np.float64]) -> float:
        optimized = CubicBezier(
            curve.p0,
            create_point(control_params[0], control_params[1]),
            create_point(control_params[2], control_params[3]),
            curve.p3,
        )
        return compute_max_error(optimized, points)

    from scipy.optimize import minimize

    initial = np.array([curve.p1[0], curve.p1[1], curve.p2[0], curve.p2[1]])

    result = minimize(error_function, initial, method="L-BFGS-B")

    if result.success:
        return CubicBezier(
            curve.p0,
            create_point(result.x[0], result.x[1]),
            create_point(result.x[2], result.x[3]),
            curve.p3,
        )

    return curve
