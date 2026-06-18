"""Tests for geometry utilities."""

from __future__ import annotations

import math

import numpy as np
import pytest

from simplifier.geometry import (
    angle_between_vectors,
    compute_bounding_box,
    compute_diagonal,
    create_point,
    douglas_peucker,
    find_corners,
    is_collinear,
    line_point_distance,
    path_length,
    point_distance,
    point_distance_squared,
    polygon_area,
    remove_collinear_points,
    remove_duplicate_points,
)


class TestPoints:
    """Test point operations."""

    def test_create_point(self) -> None:
        """Test point creation."""
        p = create_point(3.0, 4.0)
        assert p[0] == 3.0
        assert p[1] == 4.0

    def test_point_distance(self) -> None:
        """Test distance calculation."""
        p1 = create_point(0, 0)
        p2 = create_point(3, 4)
        assert point_distance(p1, p2) == 5.0

    def test_point_distance_squared(self) -> None:
        """Test squared distance."""
        p1 = create_point(0, 0)
        p2 = create_point(3, 4)
        assert point_distance_squared(p1, p2) == 25.0


class TestLineOperations:
    """Test line operations."""

    def test_line_point_distance_on_line(self) -> None:
        """Test distance for point on line."""
        line_start = create_point(0, 0)
        line_end = create_point(10, 0)
        point = create_point(5, 0)
        assert line_point_distance(line_start, line_end, point) == 0.0

    def test_line_point_distance_off_line(self) -> None:
        """Test distance for point off line."""
        line_start = create_point(0, 0)
        line_end = create_point(10, 0)
        point = create_point(5, 3)
        assert line_point_distance(line_start, line_end, point) == 3.0

    def test_angle_between_vectors(self) -> None:
        """Test angle calculation."""
        v1 = create_point(1, 0)
        v2 = create_point(0, 1)
        angle = angle_between_vectors(v1, v2)
        assert abs(angle - math.pi / 2) < 1e-10

    def test_angle_between_parallel(self) -> None:
        """Test angle for parallel vectors."""
        v1 = create_point(1, 0)
        v2 = create_point(2, 0)
        angle = angle_between_vectors(v1, v2)
        assert abs(angle) < 1e-10


class TestCollinearity:
    """Test collinearity detection."""

    def test_collinear_points(self) -> None:
        """Test collinear points."""
        p1 = create_point(0, 0)
        p2 = create_point(5, 5)
        p3 = create_point(10, 10)
        assert is_collinear(p1, p2, p3)

    def test_non_collinear_points(self) -> None:
        """Test non-collinear points."""
        p1 = create_point(0, 0)
        p2 = create_point(5, 5)
        p3 = create_point(10, 5)
        assert not is_collinear(p1, p2, p3)


class TestDuplicateRemoval:
    """Test duplicate point removal."""

    def test_remove_duplicates(self) -> None:
        """Test duplicate removal."""
        points = np.array([[0, 0], [0, 0], [1, 1], [1, 1], [2, 2]], dtype=np.float64)
        result = remove_duplicate_points(points, tolerance=0.01)
        assert len(result) == 3

    def test_remove_duplicates_empty(self) -> None:
        """Test empty input."""
        points = np.array([], dtype=np.float64).reshape(0, 2)
        result = remove_duplicate_points(points)
        assert len(result) == 0


class TestCollinearRemoval:
    """Test collinear point removal."""

    def test_remove_collinear(self) -> None:
        """Test collinear removal."""
        points = np.array([[0, 0], [1, 0], [2, 0], [3, 0]], dtype=np.float64)
        result = remove_collinear_points(points, angle_tolerance=0.01)
        assert len(result) == 2

    def test_preserve_corners(self) -> None:
        """Test corner preservation."""
        points = np.array([[0, 0], [1, 0], [1, 1]], dtype=np.float64)
        result = remove_collinear_points(points, angle_tolerance=0.01)
        assert len(result) == 3


class TestDouglasPeucker:
    """Test Douglas-Peucker algorithm."""

    def test_simple_line(self) -> None:
        """Test with straight line."""
        points = np.array([[0, 0], [1, 0], [2, 0], [3, 0]], dtype=np.float64)
        result = douglas_peucker(points, tolerance=0.1)
        assert len(result) == 2

    def test_zigzag_line(self) -> None:
        """Test with zigzag pattern."""
        points = np.array([[0, 0], [1, 1], [2, 0], [3, 1], [4, 0]], dtype=np.float64)
        result = douglas_peucker(points, tolerance=0.5)
        assert len(result) >= 2

    def test_empty_input(self) -> None:
        """Test with empty input."""
        points = np.array([], dtype=np.float64).reshape(0, 2)
        result = douglas_peucker(points, tolerance=1.0)
        assert len(result) == 0

    def test_single_point(self) -> None:
        """Test with single point."""
        points = np.array([[0, 0]], dtype=np.float64)
        result = douglas_peucker(points, tolerance=1.0)
        assert len(result) == 1


class TestBoundingBox:
    """Test bounding box calculations."""

    def test_bounding_box(self) -> None:
        """Test bounding box."""
        points = np.array([[1, 2], [3, 4], [0, 5]], dtype=np.float64)
        bbox = compute_bounding_box(points)
        assert bbox == (0.0, 2.0, 3.0, 5.0)

    def test_diagonal(self) -> None:
        """Test diagonal calculation."""
        bbox = (0.0, 0.0, 3.0, 4.0)
        assert compute_diagonal(bbox) == 5.0


class TestPolygonArea:
    """Test polygon area calculations."""

    def test_square_area(self) -> None:
        """Test square area."""
        points = np.array([[0, 0], [1, 0], [1, 1], [0, 1]], dtype=np.float64)
        area = polygon_area(points)
        assert abs(abs(area) - 1.0) < 1e-10

    def test_triangle_area(self) -> None:
        """Test triangle area."""
        points = np.array([[0, 0], [2, 0], [0, 2]], dtype=np.float64)
        area = polygon_area(points)
        assert abs(abs(area) - 2.0) < 1e-10


class TestPathLength:
    """Test path length calculations."""

    def test_straight_path(self) -> None:
        """Test straight path length."""
        points = np.array([[0, 0], [3, 0], [6, 0]], dtype=np.float64)
        length = path_length(points)
        assert abs(length - 6.0) < 1e-10

    def test_diagonal_path(self) -> None:
        """Test diagonal path length."""
        points = np.array([[0, 0], [3, 4]], dtype=np.float64)
        length = path_length(points)
        assert abs(length - 5.0) < 1e-10


class TestCornerDetection:
    """Test corner detection."""

    def test_find_corners(self) -> None:
        """Test corner detection."""
        points = np.array([[0, 0], [5, 0], [5, 5]], dtype=np.float64)
        corners = find_corners(points, angle_threshold=math.pi / 6)
        assert len(corners) == 3
        assert corners[1] == 1
