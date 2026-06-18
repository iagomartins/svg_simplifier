"""Core geometric utilities for SVG simplification.

This module provides fundamental geometric operations including point manipulation,
line calculations, angle measurements, and polygon operations.
"""

from __future__ import annotations

import math
from typing import TYPE_CHECKING

import numpy as np
from numpy.typing import NDArray

if TYPE_CHECKING:
    from typing import Sequence


Point = NDArray[np.float64]
PointSequence = NDArray[np.float64]


def create_point(x: float, y: float) -> Point:
    """Create a 2D point as numpy array.

    Args:
        x: X coordinate.
        y: Y coordinate.

    Returns:
        Numpy array with shape (2,) containing [x, y].
    """
    return np.array([x, y], dtype=np.float64)


def point_distance(p1: Point, p2: Point) -> float:
    """Calculate Euclidean distance between two points.

    Args:
        p1: First point.
        p2: Second point.

    Returns:
        Euclidean distance.
    """
    return float(np.linalg.norm(p1 - p2))


def point_distance_squared(p1: Point, p2: Point) -> float:
    """Calculate squared Euclidean distance between two points.

    Args:
        p1: First point.
        p2: Second point.

    Returns:
        Squared Euclidean distance (faster than distance for comparisons).
    """
    diff = p1 - p2
    return float(np.dot(diff, diff))


def line_point_distance(line_start: Point, line_end: Point, point: Point) -> float:
    """Calculate perpendicular distance from point to line segment.

    Args:
        line_start: Start point of line segment.
        line_end: End point of line segment.
        point: Point to measure distance from.

    Returns:
        Perpendicular distance from point to line.
    """
    line_vec = line_end - line_start
    point_vec = point - line_start

    line_len_sq = np.dot(line_vec, line_vec)

    if line_len_sq == 0:
        return point_distance(point, line_start)

    t = np.clip(np.dot(point_vec, line_vec) / line_len_sq, 0.0, 1.0)
    projection = line_start + t * line_vec
    return point_distance(point, projection)


def angle_between_vectors(v1: Point, v2: Point) -> float:
    """Calculate angle between two vectors in radians.

    Args:
        v1: First vector.
        v2: Second vector.

    Returns:
        Angle in radians between 0 and π.
    """
    norm1 = np.linalg.norm(v1)
    norm2 = np.linalg.norm(v2)

    if norm1 == 0 or norm2 == 0:
        return 0.0

    cos_angle = np.clip(np.dot(v1, v2) / (norm1 * norm2), -1.0, 1.0)
    return math.acos(float(cos_angle))


def is_collinear(p1: Point, p2: Point, p3: Point, tolerance: float = 1e-10) -> bool:
    """Check if three points are collinear.

    Args:
        p1: First point.
        p2: Second point.
        p3: Third point.
        tolerance: Maximum area of triangle formed by points to be considered collinear.

    Returns:
        True if points are collinear within tolerance.
    """
    v1 = p2 - p1
    v2 = p3 - p2
    cross = float(v1[0] * v2[1] - v1[1] * v2[0])
    return abs(cross) < tolerance


def remove_duplicate_points(
    points: PointSequence, tolerance: float = 1e-10
) -> PointSequence:
    """Remove consecutive duplicate points from a sequence.

    Args:
        points: Array of points with shape (n, 2).
        tolerance: Minimum distance between points to not be considered duplicates.

    Returns:
        Array with duplicates removed.
    """
    if len(points) == 0:
        return points

    mask = np.ones(len(points), dtype=bool)
    prev = points[0]

    for i in range(1, len(points)):
        if point_distance_squared(points[i], prev) < tolerance * tolerance:
            mask[i] = False
        else:
            prev = points[i]

    return points[mask]


def remove_collinear_points(
    points: PointSequence, angle_tolerance: float = 0.01
) -> PointSequence:
    """Remove points that lie on straight lines between neighbors.

    Args:
        points: Array of points with shape (n, 2).
        angle_tolerance: Maximum angle deviation from straight line in radians.

    Returns:
        Array with collinear middle points removed.
    """
    if len(points) < 3:
        return points

    result = [points[0]]

    for i in range(1, len(points) - 1):
        v1 = points[i] - points[i - 1]
        v2 = points[i + 1] - points[i]
        angle = angle_between_vectors(v1, v2)

        if angle > angle_tolerance:
            result.append(points[i])

    result.append(points[-1])
    return np.array(result, dtype=np.float64)


def douglas_peucker(
    points: PointSequence, tolerance: float
) -> PointSequence:
    """Simplify polyline using Douglas-Peucker algorithm.

    Args:
        points: Array of points with shape (n, 2).
        tolerance: Maximum perpendicular distance allowed.

    Returns:
        Simplified array of points.
    """
    if len(points) <= 2:
        return points

    def simplify_segment(start_idx: int, end_idx: int) -> list[int]:
        if end_idx <= start_idx + 1:
            return []

        start_point = points[start_idx]
        end_point = points[end_idx]
        line_vec = end_point - start_point
        line_len_sq = np.dot(line_vec, line_vec)

        max_dist = 0.0
        max_idx = start_idx

        for i in range(start_idx + 1, end_idx):
            point_vec = points[i] - start_point

            if line_len_sq == 0:
                dist = point_distance(points[i], start_point)
            else:
                t = np.clip(np.dot(point_vec, line_vec) / line_len_sq, 0.0, 1.0)
                projection = start_point + t * line_vec
                dist = point_distance(points[i], projection)

            if dist > max_dist:
                max_dist = dist
                max_idx = i

        if max_dist > tolerance:
            left = simplify_segment(start_idx, max_idx)
            right = simplify_segment(max_idx, end_idx)
            return left + [max_idx] + right

        return []

    indices = [0] + simplify_segment(0, len(points) - 1) + [len(points) - 1]
    return points[indices]


def compute_bounding_box(points: PointSequence) -> tuple[float, float, float, float]:
    """Compute axis-aligned bounding box of point set.

    Args:
        points: Array of points with shape (n, 2).

    Returns:
        Tuple of (min_x, min_y, max_x, max_y).
    """
    if len(points) == 0:
        return (0.0, 0.0, 0.0, 0.0)

    min_x = float(np.min(points[:, 0]))
    min_y = float(np.min(points[:, 1]))
    max_x = float(np.max(points[:, 0]))
    max_y = float(np.max(points[:, 1]))

    return (min_x, min_y, max_x, max_y)


def compute_diagonal(bbox: tuple[float, float, float, float]) -> float:
    """Compute diagonal length of bounding box.

    Args:
        bbox: Tuple of (min_x, min_y, max_x, max_y).

    Returns:
        Diagonal length.
    """
    width = bbox[2] - bbox[0]
    height = bbox[3] - bbox[1]
    return math.hypot(width, height)


def polygon_area(points: PointSequence) -> float:
    """Compute signed area of polygon using shoelace formula.

    Args:
        points: Array of points with shape (n, 2).

    Returns:
        Signed area (positive for counter-clockwise, negative for clockwise).
    """
    if len(points) < 3:
        return 0.0

    x = points[:, 0]
    y = points[:, 1]
    return 0.5 * float(np.sum(x[:-1] * y[1:] - x[1:] * y[:-1]))


def is_convex_polygon(points: PointSequence) -> bool:
    """Check if polygon is convex.

    Args:
        points: Array of points with shape (n, 2).

    Returns:
        True if polygon is convex.
    """
    if len(points) < 4:
        return True

    n = len(points)
    sign = 0

    for i in range(n):
        p0 = points[i]
        p1 = points[(i + 1) % n]
        p2 = points[(i + 2) % n]

        v1 = p1 - p0
        v2 = p2 - p1
        cross = v1[0] * v2[1] - v1[1] * v2[0]

        if cross != 0:
            current_sign = 1 if cross > 0 else -1
            if sign == 0:
                sign = current_sign
            elif sign != current_sign:
                return False

    return True


def resample_polyline(
    points: PointSequence, num_points: int
) -> PointSequence:
    """Resample polyline to specified number of evenly-spaced points.

    Args:
        points: Array of points with shape (n, 2).
        num_points: Desired number of output points.

    Returns:
        Resampled array of points.
    """
    if len(points) < 2 or num_points < 2:
        return points

    if num_points >= len(points):
        return points

    distances = np.zeros(len(points))
    for i in range(1, len(points)):
        distances[i] = distances[i - 1] + point_distance(points[i - 1], points[i])

    total_length = distances[-1]
    if total_length == 0:
        return points[:num_points]

    target_distances = np.linspace(0, total_length, num_points)
    result = np.zeros((num_points, 2), dtype=np.float64)

    result[0] = points[0]
    result[-1] = points[-1]

    j = 0
    for i in range(1, num_points - 1):
        target_dist = target_distances[i]
        while j < len(distances) - 1 and distances[j + 1] < target_dist:
            j += 1

        if j >= len(points) - 1:
            result[i] = points[-1]
        else:
            segment_length = distances[j + 1] - distances[j]
            if segment_length == 0:
                t = 0
            else:
                t = (target_dist - distances[j]) / segment_length
            result[i] = (1 - t) * points[j] + t * points[j + 1]

    return result


def find_corners(
    points: PointSequence, angle_threshold: float = np.pi / 6
) -> list[int]:
    """Find corner indices in polyline based on angle changes.

    Args:
        points: Array of points with shape (n, 2).
        angle_threshold: Minimum angle change to be considered a corner.

    Returns:
        List of indices where corners occur.
    """
    if len(points) < 3:
        return list(range(len(points)))

    corners = [0]

    for i in range(1, len(points) - 1):
        v1 = points[i] - points[i - 1]
        v2 = points[i + 1] - points[i]
        angle = angle_between_vectors(v1, v2)

        if angle > angle_threshold:
            corners.append(i)

    corners.append(len(points) - 1)
    return corners


def split_at_corners(
    points: PointSequence, angle_threshold: float = np.pi / 6
) -> list[PointSequence]:
    """Split polyline into segments at corner points.

    Args:
        points: Array of points with shape (n, 2).
        angle_threshold: Minimum angle change to be considered a corner.

    Returns:
        List of point arrays, each representing a smooth segment.
    """
    corners = find_corners(points, angle_threshold)

    segments = []
    for i in range(len(corners) - 1):
        start = corners[i]
        end = corners[i + 1]
        if end > start:
            segments.append(points[start : end + 1])

    return segments


def path_length(points: PointSequence) -> float:
    """Compute total length of polyline.

    Args:
        points: Array of points with shape (n, 2).

    Returns:
        Total path length.
    """
    if len(points) < 2:
        return 0.0

    length = 0.0
    for i in range(1, len(points)):
        length += point_distance(points[i - 1], points[i])

    return length


def interpolate_points(p1: Point, p2: Point, t: float) -> Point:
    """Linearly interpolate between two points.

    Args:
        p1: First point.
        p2: Second point.
        t: Interpolation factor (0 = p1, 1 = p2).

    Returns:
        Interpolated point.
    """
    return (1 - t) * p1 + t * p2
