"""SVG transformation handling.

This module provides support for SVG transform attributes including
translate, scale, rotate, matrix, skewX, and skewY.
"""

from __future__ import annotations

import math
import re
from dataclasses import dataclass
from typing import TYPE_CHECKING

import numpy as np
from numpy.typing import NDArray

from simplifier.geometry import Point, create_point

if TYPE_CHECKING:
    from collections.abc import Sequence


@dataclass(frozen=True)
class TransformMatrix:
    """2D transformation matrix.

    Represents an affine transformation as a 3x3 matrix:
    | a  c  e |
    | b  d  f |
    | 0  0  1 |

    Attributes:
        a: X scale/X rotation component.
        b: Y skew/X rotation component.
        c: X skew/Y rotation component.
        d: Y scale/Y rotation component.
        e: X translation component.
        f: Y translation component.
    """

    a: float = 1.0
    b: float = 0.0
    c: float = 0.0
    d: float = 1.0
    e: float = 0.0
    f: float = 0.0

    def to_matrix(self) -> NDArray[np.float64]:
        """Convert to 3x3 numpy matrix.

        Returns:
            3x3 transformation matrix.
        """
        return np.array(
            [[self.a, self.c, self.e], [self.b, self.d, self.f], [0.0, 0.0, 1.0]],
            dtype=np.float64,
        )

    @classmethod
    def from_matrix(cls, matrix: NDArray[np.float64]) -> TransformMatrix:
        """Create from 3x3 numpy matrix.

        Args:
            matrix: 3x3 transformation matrix.

        Returns:
            TransformMatrix instance.
        """
        return cls(
            a=float(matrix[0, 0]),
            b=float(matrix[1, 0]),
            c=float(matrix[0, 1]),
            d=float(matrix[1, 1]),
            e=float(matrix[0, 2]),
            f=float(matrix[1, 2]),
        )

    @classmethod
    def identity(cls) -> TransformMatrix:
        """Create identity transformation.

        Returns:
            Identity matrix.
        """
        return cls()

    @classmethod
    def translate(cls, tx: float, ty: float = 0.0) -> TransformMatrix:
        """Create translation transformation.

        Args:
            tx: X translation.
            ty: Y translation (default 0).

        Returns:
            Translation matrix.
        """
        return cls(a=1.0, b=0.0, c=0.0, d=1.0, e=tx, f=ty)

    @classmethod
    def scale(cls, sx: float, sy: float | None = None) -> TransformMatrix:
        """Create scale transformation.

        Args:
            sx: X scale factor.
            sy: Y scale factor (defaults to sx if None).

        Returns:
            Scale matrix.
        """
        if sy is None:
            sy = sx
        return cls(a=sx, b=0.0, c=0.0, d=sy, e=0.0, f=0.0)

    @classmethod
    def rotate(cls, angle: float, cx: float = 0.0, cy: float = 0.0) -> TransformMatrix:
        """Create rotation transformation.

        Args:
            angle: Rotation angle in degrees.
            cx: Center X coordinate.
            cy: Center Y coordinate.

        Returns:
            Rotation matrix.
        """
        rad = math.radians(angle)
        cos_a = math.cos(rad)
        sin_a = math.sin(rad)

        if cx == 0.0 and cy == 0.0:
            return cls(a=cos_a, b=sin_a, c=-sin_a, d=cos_a, e=0.0, f=0.0)

        translate_to_origin = cls.translate(-cx, -cy)
        rotate = cls.rotate(angle)
        translate_back = cls.translate(cx, cy)

        return translate_back @ rotate @ translate_to_origin

    @classmethod
    def skew_x(cls, angle: float) -> TransformMatrix:
        """Create X skew transformation.

        Args:
            angle: Skew angle in degrees.

        Returns:
            Skew X matrix.
        """
        return cls(a=1.0, b=0.0, c=math.tan(math.radians(angle)), d=1.0, e=0.0, f=0.0)

    @classmethod
    def skew_y(cls, angle: float) -> TransformMatrix:
        """Create Y skew transformation.

        Args:
            angle: Skew angle in degrees.

        Returns:
            Skew Y matrix.
        """
        return cls(a=1.0, b=math.tan(math.radians(angle)), c=0.0, d=1.0, e=0.0, f=0.0)

    @classmethod
    def matrix(
        cls, a: float, b: float, c: float, d: float, e: float, f: float
    ) -> TransformMatrix:
        """Create from explicit matrix values.

        Args:
            a: Element at (0,0).
            b: Element at (1,0).
            c: Element at (0,1).
            d: Element at (1,1).
            e: Element at (0,2).
            f: Element at (1,2).

        Returns:
            Matrix transformation.
        """
        return cls(a=a, b=b, c=c, d=d, e=e, f=f)

    def __matmul__(self, other: TransformMatrix) -> TransformMatrix:
        """Compose two transformations.

        Args:
            other: Right-hand transformation.

        Returns:
            Composed transformation.
        """
        result = self.to_matrix() @ other.to_matrix()
        return TransformMatrix.from_matrix(result)

    def apply_to_point(self, point: Point) -> Point:
        """Apply transformation to a point.

        Args:
            point: Point to transform.

        Returns:
            Transformed point.
        """
        x = self.a * point[0] + self.c * point[1] + self.e
        y = self.b * point[0] + self.d * point[1] + self.f
        return create_point(x, y)

    def apply_to_points(self, points: NDArray[np.float64]) -> NDArray[np.float64]:
        """Apply transformation to array of points.

        Args:
            points: Array of shape (n, 2).

        Returns:
            Transformed points.
        """
        if len(points) == 0:
            return points

        result = np.zeros_like(points)
        result[:, 0] = self.a * points[:, 0] + self.c * points[:, 1] + self.e
        result[:, 1] = self.b * points[:, 0] + self.d * points[:, 1] + self.f
        return result

    def determinant(self) -> float:
        """Compute matrix determinant.

        Returns:
            Determinant value.
        """
        return self.a * self.d - self.c * self.b

    def is_invertible(self) -> bool:
        """Check if matrix is invertible.

        Returns:
            True if invertible.
        """
        return abs(self.determinant()) > 1e-10

    def inverse(self) -> TransformMatrix:
        """Compute inverse transformation.

        Returns:
            Inverse matrix.

        Raises:
            ValueError: If matrix is not invertible.
        """
        det = self.determinant()
        if abs(det) < 1e-10:
            raise ValueError("Matrix is not invertible")

        inv_det = 1.0 / det
        return TransformMatrix(
            a=self.d * inv_det,
            b=-self.b * inv_det,
            c=-self.c * inv_det,
            d=self.a * inv_det,
            e=(self.c * self.f - self.d * self.e) * inv_det,
            f=(self.b * self.e - self.a * self.f) * inv_det,
        )

    def is_identity(self, tolerance: float = 1e-10) -> bool:
        """Check if transformation is approximately identity.

        Args:
            tolerance: Comparison tolerance.

        Returns:
            True if identity transformation.
        """
        return (
            abs(self.a - 1.0) < tolerance
            and abs(self.d - 1.0) < tolerance
            and abs(self.b) < tolerance
            and abs(self.c) < tolerance
            and abs(self.e) < tolerance
            and abs(self.f) < tolerance
        )

    def extract_scale(self) -> tuple[float, float]:
        """Extract scale factors from transformation.

        Returns:
            Tuple of (scale_x, scale_y).
        """
        scale_x = math.hypot(self.a, self.b)
        scale_y = math.hypot(self.c, self.d)
        return (scale_x, scale_y)


class TransformParser:
    """Parser for SVG transform attribute strings."""

    @staticmethod
    def parse(transform_string: str | None) -> TransformMatrix:
        """Parse SVG transform attribute string.

        Args:
            transform_string: SVG transform attribute value.

        Returns:
            Combined transformation matrix.
        """
        if not transform_string:
            return TransformMatrix.identity()

        result = TransformMatrix.identity()

        pattern = r"(\w+)\s*\(([^)]+)\)"
        matches = re.findall(pattern, transform_string)

        for name, args_str in matches:
            args = TransformParser._parse_args(args_str)
            transform = TransformParser._create_transform(name, args)
            result = result @ transform

        return result

    @staticmethod
    def _parse_args(args_str: str) -> list[float]:
        """Parse comma or space separated numbers.

        Args:
            args_str: Argument string.

        Returns:
            List of parsed numbers.
        """
        numbers = re.findall(r"-?\d*\.?\d+(?:[eE][+-]?\d+)?", args_str)
        return [float(n) for n in numbers]

    @staticmethod
    def _create_transform(name: str, args: list[float]) -> TransformMatrix:
        """Create transform from name and arguments.

        Args:
            name: Transform function name.
            args: List of numeric arguments.

        Returns:
            Transformation matrix.

        Raises:
            ValueError: If transform name is unknown or args are invalid.
        """
        name_lower = name.lower()

        if name_lower == "translate":
            tx = args[0] if len(args) > 0 else 0.0
            ty = args[1] if len(args) > 1 else 0.0
            return TransformMatrix.translate(tx, ty)

        if name_lower == "scale":
            sx = args[0] if len(args) > 0 else 1.0
            sy = args[1] if len(args) > 1 else sx
            return TransformMatrix.scale(sx, sy)

        if name_lower == "rotate":
            angle = args[0] if len(args) > 0 else 0.0
            cx = args[1] if len(args) > 1 else 0.0
            cy = args[2] if len(args) > 2 else cx
            return TransformMatrix.rotate(angle, cx, cy)

        if name_lower == "skewx":
            angle = args[0] if len(args) > 0 else 0.0
            return TransformMatrix.skew_x(angle)

        if name_lower == "skewy":
            angle = args[0] if len(args) > 0 else 0.0
            return TransformMatrix.skew_y(angle)

        if name_lower == "matrix":
            if len(args) < 6:
                raise ValueError("Matrix transform requires 6 arguments")
            return TransformMatrix.matrix(*args[:6])

        raise ValueError(f"Unknown transform: {name}")


class TransformStack:
    """Stack of transformations for nested SVG elements."""

    def __init__(self) -> None:
        """Initialize empty transform stack."""
        self._stack: list[TransformMatrix] = []

    def push(self, transform: TransformMatrix) -> None:
        """Push transformation onto stack.

        Args:
            transform: Transformation to push.
        """
        self._stack.append(transform)

    def pop(self) -> TransformMatrix:
        """Pop transformation from stack.

        Returns:
            Popped transformation.

        Raises:
            IndexError: If stack is empty.
        """
        if not self._stack:
            raise IndexError("Transform stack is empty")
        return self._stack.pop()

    def current(self) -> TransformMatrix:
        """Get current combined transformation.

        Returns:
            Combined transformation of all stacked transforms.
        """
        if not self._stack:
            return TransformMatrix.identity()

        result = self._stack[0]
        for transform in self._stack[1:]:
            result = result @ transform

        return result

    def apply_to_point(self, point: Point) -> Point:
        """Apply current transform to point.

        Args:
            point: Point to transform.

        Returns:
            Transformed point.
        """
        return self.current().apply_to_point(point)

    def apply_to_points(self, points: NDArray[np.float64]) -> NDArray[np.float64]:
        """Apply current transform to points.

        Args:
            points: Points to transform.

        Returns:
            Transformed points.
        """
        return self.current().apply_to_points(points)

    def __len__(self) -> int:
        """Return stack depth.

        Returns:
            Number of transforms in stack.
        """
        return len(self._stack)

    def __bool__(self) -> bool:
        """Check if stack has transforms.

        Returns:
            True if stack is non-empty.
        """
        return bool(self._stack)


def apply_viewbox_transform(
    viewbox: tuple[float, float, float, float] | None,
    width: float | None,
    height: float | None,
) -> TransformMatrix:
    """Compute transform from viewBox to viewport.

    Args:
        viewbox: ViewBox (min_x, min_y, width, height).
        width: Viewport width.
        height: Viewport height.

    Returns:
        Transform from viewBox to viewport coordinates.
    """
    if viewbox is None or width is None or height is None:
        return TransformMatrix.identity()

    vb_min_x, vb_min_y, vb_width, vb_height = viewbox

    if vb_width <= 0 or vb_height <= 0:
        return TransformMatrix.identity()

    scale_x = width / vb_width
    scale_y = height / vb_height

    translate_x = -vb_min_x * scale_x
    translate_y = -vb_min_y * scale_y

    return TransformMatrix.translate(translate_x, translate_y) @ TransformMatrix.scale(
        scale_x, scale_y
    )
