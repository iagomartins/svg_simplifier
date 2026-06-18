"""SVG output writer.

This module handles writing optimized SVG files with proper formatting
and precision control.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np
from lxml import etree

from simplifier.bezier import CubicBezier
from simplifier.parser import ParseResult, ParsedPath, SVG_NAMESPACE

if TYPE_CHECKING:
    from numpy.typing import NDArray


class SVGWriter:
    """Writer for optimized SVG files."""

    def __init__(self, precision: int = 6) -> None:
        """Initialize writer.

        Args:
            precision: Decimal precision for coordinates.
        """
        self.precision = precision

    def write_file(
        self, paths: list[ParsedPath], output_path: str, parse_result: ParseResult
    ) -> None:
        """Write paths to SVG file.

        Args:
            paths: Simplified paths.
            output_path: Output file path.
            parse_result: Original parse result for metadata.
        """
        svg_string = self.write_string(paths, parse_result)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(svg_string)

    def write_string(
        self, paths: list[ParsedPath], parse_result: ParseResult
    ) -> str:
        """Write paths to SVG string.

        Args:
            paths: Simplified paths.
            parse_result: Original parse result for metadata.

        Returns:
            SVG string.
        """
        nsmap = parse_result.namespaces or {"svg": SVG_NAMESPACE}
        svg_ns = nsmap.get("svg", SVG_NAMESPACE)

        svg = etree.Element(f"{{{svg_ns}}}svg", nsmap=nsmap)

        if parse_result.viewbox:
            vb = parse_result.viewbox
            svg.set("viewBox", f"{vb[0]} {vb[1]} {vb[2]} {vb[3]}")

        if parse_result.width:
            svg.set("width", str(parse_result.width))
        if parse_result.height:
            svg.set("height", str(parse_result.height))

        for path in paths:
            path_elem = self._create_path_element(path, svg_ns)
            svg.append(path_elem)

        return etree.tostring(svg, pretty_print=True, encoding="unicode")

    def _create_path_element(
        self, path: ParsedPath, namespace: str
    ) -> etree._Element:
        """Create path element from ParsedPath.

        Args:
            path: Parsed path.
            namespace: SVG namespace.

        Returns:
            Path element.
        """
        d = self._curves_to_path_data(path.curves, path.is_closed)

        attrs: dict[str, str] = {"d": d}

        if path.id:
            attrs["id"] = path.id
        if path.class_name:
            attrs["class"] = path.class_name

        if path.fill_rule and path.fill_rule != "nonzero":
            attrs["fill-rule"] = path.fill_rule

        if path.style:
            style_str = "; ".join(f"{k}: {v}" for k, v in path.style.items())
            attrs["style"] = style_str

        return etree.Element(f"{{{namespace}}}path", attrs)

    def _curves_to_path_data(
        self, curves: list[CubicBezier], is_closed: bool
    ) -> str:
        """Convert curves to SVG path data string.

        Args:
            curves: List of curves.
            is_closed: Whether path is closed.

        Returns:
            Path data string.
        """
        if not curves:
            return ""

        parts = []

        first = curves[0]
        parts.append(f"M {self._fmt(first.p0[0])} {self._fmt(first.p0[1])}")

        for curve in curves:
            parts.append(self._curve_to_command(curve))

        if is_closed:
            parts.append("Z")

        return " ".join(parts)

    def _curve_to_command(self, curve: CubicBezier) -> str:
        """Convert cubic Bezier to SVG command.

        Args:
            curve: Cubic Bezier curve.

        Returns:
            SVG command string.
        """
        return (
            f"C {self._fmt(curve.p1[0])} {self._fmt(curve.p1[1])}, "
            f"{self._fmt(curve.p2[0])} {self._fmt(curve.p2[1])}, "
            f"{self._fmt(curve.p3[0])} {self._fmt(curve.p3[1])}"
        )

    def _fmt(self, value: float) -> str:
        """Format numeric value.

        Args:
            value: Number to format.

        Returns:
            Formatted string.
        """
        formatted = f"{value:.{self.precision}f}"
        formatted = formatted.rstrip("0").rstrip(".")
        if formatted == "-0":
            formatted = "0"
        return formatted
