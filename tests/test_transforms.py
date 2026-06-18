"""Tests for transformation handling."""

from __future__ import annotations

import math

import numpy as np
import pytest

from simplifier.transforms import (
    TransformMatrix,
    TransformParser,
    TransformStack,
    apply_viewbox_transform,
)
from simplifier.geometry import create_point


class TestTransformMatrix:
    """Test transformation matrix operations."""

    def test_identity(self) -> None:
        """Test identity matrix."""
        m = TransformMatrix.identity()
        assert m.is_identity()
        p = create_point(5, 10)
        result = m.apply_to_point(p)
        assert np.allclose(result, p)

    def test_translate(self) -> None:
        """Test translation."""
        m = TransformMatrix.translate(10, 20)
        p = create_point(5, 5)
        result = m.apply_to_point(p)
        assert np.allclose(result, [15, 25])

    def test_scale(self) -> None:
        """Test scaling."""
        m = TransformMatrix.scale(2, 3)
        p = create_point(5, 5)
        result = m.apply_to_point(p)
        assert np.allclose(result, [10, 15])

    def test_scale_uniform(self) -> None:
        """Test uniform scaling."""
        m = TransformMatrix.scale(2)
        p = create_point(5, 10)
        result = m.apply_to_point(p)
        assert np.allclose(result, [10, 20])

    def test_rotate(self) -> None:
        """Test rotation."""
        m = TransformMatrix.rotate(90)
        p = create_point(1, 0)
        result = m.apply_to_point(p)
        assert abs(result[0]) < 1e-10
        assert abs(result[1] - 1) < 1e-10

    def test_rotate_around_center(self) -> None:
        """Test rotation around center point."""
        m = TransformMatrix.rotate(90, cx=10, cy=10)
        p = create_point(10, 0)
        result = m.apply_to_point(p)
        assert abs(result[0] - 20) < 1e-10
        assert abs(result[1] - 10) < 1e-10

    def test_skew_x(self) -> None:
        """Test X skew."""
        m = TransformMatrix.skew_x(45)
        p = create_point(1, 1)
        result = m.apply_to_point(p)
        assert abs(result[0] - 2) < 1e-10
        assert abs(result[1] - 1) < 1e-10

    def test_skew_y(self) -> None:
        """Test Y skew."""
        m = TransformMatrix.skew_y(45)
        p = create_point(1, 1)
        result = m.apply_to_point(p)
        assert abs(result[0] - 1) < 1e-10
        assert abs(result[1] - 2) < 1e-10

    def test_compose(self) -> None:
        """Test matrix composition."""
        t = TransformMatrix.translate(10, 0)
        s = TransformMatrix.scale(2)
        composed = t @ s
        p = create_point(5, 5)
        result = composed.apply_to_point(p)
        assert np.allclose(result, [20, 10])

    def test_inverse(self) -> None:
        """Test matrix inversion."""
        m = TransformMatrix.translate(10, 20)
        inv = m.inverse()
        p = create_point(15, 25)
        result = inv.apply_to_point(p)
        assert np.allclose(result, [5, 5])

    def test_determinant(self) -> None:
        """Test determinant calculation."""
        m = TransformMatrix.scale(2, 3)
        assert abs(m.determinant() - 6) < 1e-10

    def test_extract_scale(self) -> None:
        """Test scale extraction."""
        m = TransformMatrix.scale(2, 3)
        sx, sy = m.extract_scale()
        assert abs(sx - 2) < 1e-10
        assert abs(sy - 3) < 1e-10


class TestTransformParser:
    """Test transform parsing."""

    def test_parse_translate(self) -> None:
        """Test parsing translate."""
        result = TransformParser.parse("translate(10, 20)")
        p = create_point(0, 0)
        assert np.allclose(result.apply_to_point(p), [10, 20])

    def test_parse_translate_single(self) -> None:
        """Test parsing translate with one argument."""
        result = TransformParser.parse("translate(10)")
        p = create_point(0, 0)
        assert np.allclose(result.apply_to_point(p), [10, 0])

    def test_parse_scale(self) -> None:
        """Test parsing scale."""
        result = TransformParser.parse("scale(2, 3)")
        p = create_point(5, 5)
        assert np.allclose(result.apply_to_point(p), [10, 15])

    def test_parse_rotate(self) -> None:
        """Test parsing rotate."""
        result = TransformParser.parse("rotate(90)")
        p = create_point(1, 0)
        result_p = result.apply_to_point(p)
        assert abs(result_p[0]) < 1e-10
        assert abs(result_p[1] - 1) < 1e-10

    def test_parse_rotate_with_center(self) -> None:
        """Test parsing rotate with center."""
        result = TransformParser.parse("rotate(90, 10, 10)")
        p = create_point(10, 0)
        result_p = result.apply_to_point(p)
        assert abs(result_p[0] - 20) < 1e-10

    def test_parse_skew_x(self) -> None:
        """Test parsing skewX."""
        result = TransformParser.parse("skewX(45)")
        p = create_point(1, 1)
        result_p = result.apply_to_point(p)
        assert abs(result_p[0] - 2) < 1e-10

    def test_parse_skew_y(self) -> None:
        """Test parsing skewY."""
        result = TransformParser.parse("skewY(45)")
        p = create_point(1, 1)
        result_p = result.apply_to_point(p)
        assert abs(result_p[1] - 2) < 1e-10

    def test_parse_matrix(self) -> None:
        """Test parsing matrix."""
        result = TransformParser.parse("matrix(1, 0, 0, 1, 10, 20)")
        p = create_point(0, 0)
        assert np.allclose(result.apply_to_point(p), [10, 20])

    def test_parse_multiple(self) -> None:
        """Test parsing multiple transforms."""
        result = TransformParser.parse("translate(10, 0) scale(2)")
        p = create_point(5, 5)
        result_p = result.apply_to_point(p)
        assert np.allclose(result_p, [20, 10])

    def test_parse_empty(self) -> None:
        """Test parsing empty string."""
        result = TransformParser.parse("")
        assert result.is_identity()

    def test_parse_none(self) -> None:
        """Test parsing None."""
        result = TransformParser.parse(None)
        assert result.is_identity()


class TestTransformStack:
    """Test transform stack."""

    def test_empty_stack(self) -> None:
        """Test empty stack."""
        stack = TransformStack()
        p = create_point(5, 5)
        result = stack.apply_to_point(p)
        assert np.allclose(result, p)

    def test_push_pop(self) -> None:
        """Test push and pop."""
        stack = TransformStack()
        m = TransformMatrix.translate(10, 20)
        stack.push(m)
        p = create_point(0, 0)
        assert np.allclose(stack.apply_to_point(p), [10, 20])
        stack.pop()
        assert np.allclose(stack.apply_to_point(p), [0, 0])

    def test_multiple_transforms(self) -> None:
        """Test multiple transforms."""
        stack = TransformStack()
        stack.push(TransformMatrix.translate(10, 0))
        stack.push(TransformMatrix.scale(2))
        p = create_point(5, 5)
        result = stack.apply_to_point(p)
        assert np.allclose(result, [20, 10])

    def test_len(self) -> None:
        """Test stack length."""
        stack = TransformStack()
        assert len(stack) == 0
        stack.push(TransformMatrix.identity())
        assert len(stack) == 1


class TestViewBoxTransform:
    """Test viewBox transform."""

    def test_viewbox_transform(self) -> None:
        """Test viewBox to viewport transform."""
        viewbox = (0, 0, 100, 100)
        m = apply_viewbox_transform(viewbox, 200, 200)
        p = create_point(50, 50)
        result = m.apply_to_point(p)
        assert np.allclose(result, [100, 100])

    def test_viewbox_with_offset(self) -> None:
        """Test viewBox with offset."""
        viewbox = (10, 10, 100, 100)
        m = apply_viewbox_transform(viewbox, 100, 100)
        p = create_point(10, 10)
        result = m.apply_to_point(p)
        assert np.allclose(result, [0, 0])

    def test_no_viewbox(self) -> None:
        """Test with no viewBox."""
        m = apply_viewbox_transform(None, 100, 100)
        assert m.is_identity()
