"""SVG path optimization and simplification.

This module implements the full simplification pipeline including flattening,
Douglas-Peucker, curve fitting, and optimization.
"""

from __future__ import annotations

import multiprocessing as mp
from concurrent.futures import ProcessPoolExecutor
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

import numpy as np
from numpy.typing import NDArray

from simplifier.bezier import CubicBezier, fit_bezier_curve
from simplifier.geometry import (
    PointSequence,
    compute_bounding_box,
    compute_diagonal,
    douglas_peucker,
    path_length,
    remove_collinear_points,
    remove_duplicate_points,
)
from simplifier.parser import ParseResult, ParsedPath, SVGParser
from simplifier.svg_writer import SVGWriter
from simplifier.utils import Statistics, Timer

if TYPE_CHECKING:
    from collections.abc import Sequence


@dataclass
class SimplificationOptions:
    """Options for path simplification.

    Attributes:
        tolerance: Douglas-Peucker tolerance.
        max_error: Maximum allowed fitting error.
        corner_angle: Angle threshold for corner detection.
        remove_duplicates: Whether to remove duplicate points.
        merge_curves: Whether to merge adjacent curves.
        precision: Decimal precision for output.
    """

    tolerance: float = 0.001
    max_error: float = 0.0005
    corner_angle: float = np.pi / 6
    remove_duplicates: bool = True
    merge_curves: bool = True
    precision: int = 6


@dataclass
class SimplificationResult:
    """Result of simplification operation.

    Attributes:
        paths: Simplified paths.
        original_nodes: Node count before simplification.
        optimized_nodes: Node count after simplification.
        statistics: Detailed statistics.
    """

    paths: list[ParsedPath] = field(default_factory=list)
    original_nodes: int = 0
    optimized_nodes: int = 0
    statistics: Statistics = field(default_factory=Statistics)

    @property
    def reduction_percentage(self) -> float:
        """Calculate reduction percentage."""
        if self.original_nodes == 0:
            return 0.0
        return (self.original_nodes - self.optimized_nodes) / self.original_nodes


class Simplifier:
    """Main SVG simplification engine."""

    def __init__(self, options: SimplificationOptions | None = None) -> None:
        """Initialize simplifier.

        Args:
            options: Simplification options or None for defaults.
        """
        self.options = options or SimplificationOptions()
        self.parser = SVGParser()
        self.writer = SVGWriter()

    def simplify_file(
        self, input_path: str, output_path: str, stats: Statistics | None = None
    ) -> SimplificationResult:
        """Simplify SVG file.

        Args:
            input_path: Input SVG file path.
            output_path: Output SVG file path.
            stats: Optional statistics container.

        Returns:
            Simplification result.
        """
        with Timer() as timer:
            parse_result = self.parser.parse_file(input_path)
            result = self._simplify_parse_result(parse_result)
            self.writer.write_file(result.paths, output_path, parse_result)

        if stats:
            stats.execution_time = timer.elapsed
            stats.original_nodes = result.original_nodes
            stats.optimized_nodes = result.optimized_nodes
            stats.reduction_percentage = result.reduction_percentage

        result.statistics = stats or Statistics()
        result.statistics.execution_time = timer.elapsed
        return result

    def simplify_string(
        self, svg_string: str
    ) -> tuple[str, SimplificationResult]:
        """Simplify SVG string.

        Args:
            svg_string: Input SVG string.

        Returns:
            Tuple of (output SVG string, result).
        """
        with Timer() as timer:
            parse_result = self.parser.parse_string(svg_string)
            result = self._simplify_parse_result(parse_result)
            output_string = self.writer.write_string(result.paths, parse_result)

        result.statistics.execution_time = timer.elapsed
        return output_string, result

    def _simplify_parse_result(self, parse_result: ParseResult) -> SimplificationResult:
        """Simplify parsed result.

        Args:
            parse_result: Parse result from SVG.

        Returns:
            Simplification result.
        """
        result = SimplificationResult()
        result.original_nodes = parse_result.count_total_nodes()

        if not parse_result.paths:
            return result

        bbox = parse_result.get_bounding_box()
        diagonal = compute_diagonal(bbox)

        tolerance = self.options.tolerance * diagonal
        max_error = self.options.max_error * diagonal

        if len(parse_result.paths) > 10 and mp.cpu_count() > 1:
            result.paths = self._simplify_parallel(
                parse_result.paths, tolerance, max_error
            )
        else:
            result.paths = [
                self._simplify_path(path, tolerance, max_error)
                for path in parse_result.paths
            ]

        result.optimized_nodes = sum(
            path.count_nodes() for path in result.paths
        )
        return result

    def _simplify_parallel(
        self, paths: list[ParsedPath], tolerance: float, max_error: float
    ) -> list[ParsedPath]:
        """Simplify paths in parallel.

        Args:
            paths: List of paths to simplify.
            tolerance: Simplification tolerance.
            max_error: Maximum fitting error.

        Returns:
            List of simplified paths.
        """
        with ProcessPoolExecutor() as executor:
            futures = [
                executor.submit(self._simplify_path_worker, path, tolerance, max_error)
                for path in paths
            ]
            return [f.result() for f in futures]

    def _simplify_path_worker(
        self, path: ParsedPath, tolerance: float, max_error: float
    ) -> ParsedPath:
        """Worker for parallel simplification.

        Args:
            path: Path to simplify.
            tolerance: Simplification tolerance.
            max_error: Maximum fitting error.

        Returns:
            Simplified path.
        """
        return self._simplify_path(path, tolerance, max_error)

    def _simplify_path(
        self, path: ParsedPath, tolerance: float, max_error: float
    ) -> ParsedPath:
        """Simplify single path.

        Args:
            path: Path to simplify.
            tolerance: Simplification tolerance.
            max_error: Maximum fitting error.

        Returns:
            Simplified path.
        """
        if not path.curves:
            return path

        all_points = self._flatten_curves(path.curves)

        if self.options.remove_duplicates:
            all_points = remove_duplicate_points(all_points)

        all_points = remove_collinear_points(all_points, self.options.corner_angle)

        if len(all_points) < 2:
            return ParsedPath(
                curves=[],
                is_closed=path.is_closed,
                fill_rule=path.fill_rule,
                style=path.style,
            )

        simplified = douglas_peucker(all_points, tolerance)

        if len(simplified) < 2:
            simplified = all_points

        fitted = fit_bezier_curve(
            simplified, max_error, self.options.corner_angle
        )

        if self.options.merge_curves:
            fitted = self._merge_adjacent_curves(fitted, max_error)

        return ParsedPath(
            curves=fitted,
            is_closed=path.is_closed,
            fill_rule=path.fill_rule,
            style=path.style,
        )

    def _flatten_curves(self, curves: list[CubicBezier]) -> PointSequence:
        """Flatten curves to polyline.

        Args:
            curves: List of curves.

        Returns:
            Array of points.
        """
        points = []
        for curve in curves:
            curve_points = curve.to_polyline(20)
            if len(points) > 0 and len(curve_points) > 0:
                if np.allclose(points[-1], curve_points[0], atol=1e-10):
                    curve_points = curve_points[1:]
            points.extend(curve_points)
        return np.array(points, dtype=np.float64)

    def _merge_adjacent_curves(
        self, curves: list[CubicBezier], tolerance: float
    ) -> list[CubicBezier]:
        """Merge adjacent curves where possible.

        Args:
            curves: List of curves.
            tolerance: Error tolerance for merging.

        Returns:
            List with merged curves.
        """
        if len(curves) < 2:
            return curves

        merged = [curves[0]]
        for i in range(1, len(curves)):
            prev = merged[-1]
            curr = curves[i]

            combined_points = np.vstack([prev.to_polyline(10), curr.to_polyline(10)])

            from simplifier.bezier import fit_single_curve, compute_max_error

            try:
                combined_curve = fit_single_curve(combined_points)
                error = compute_max_error(combined_curve, combined_points)

                if error < tolerance:
                    merged[-1] = combined_curve
                else:
                    merged.append(curr)
            except Exception:
                merged.append(curr)

        return merged
