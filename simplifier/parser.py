"""SVG parser and path converter.

This module provides comprehensive SVG parsing including support for all path
commands, shape primitives, transformations, and nested group structures.
"""

from __future__ import annotations

import math
import re
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

import numpy as np
from lxml import etree
from numpy.typing import NDArray

from simplifier.bezier import CubicBezier, EllipticalArc, arc_to_beziers
from simplifier.geometry import Point, create_point, point_distance
from simplifier.transforms import TransformParser, TransformStack

if TYPE_CHECKING:
    from collections.abc import Iterator

SVG_NAMESPACE = "http://www.w3.org/2000/svg"
XLINK_NAMESPACE = "http://www.w3.org/1999/xlink"


@dataclass
class ParsedPath:
    """Represents a parsed SVG path with metadata."""

    curves: list[CubicBezier] = field(default_factory=list)
    is_closed: bool = False
    fill_rule: str = "nonzero"
    stroke_width: float | None = None
    transform: Any = None
    id: str | None = None
    class_name: str | None = None
    style: dict[str, str] = field(default_factory=dict)

    def get_all_points(self) -> NDArray[np.float64]:
        """Get all control points from all curves."""
        if not self.curves:
            return np.array([], dtype=np.float64).reshape(0, 2)
        points = []
        for curve in self.curves:
            points.extend([curve.p0, curve.p1, curve.p2, curve.p3])
        return np.array(points, dtype=np.float64)

    def count_nodes(self) -> int:
        """Count total nodes in path."""
        return len(self.curves) * 4 if self.curves else 0


@dataclass
class ParseResult:
    """Result of SVG parsing."""

    paths: list[ParsedPath] = field(default_factory=list)
    viewbox: tuple[float, float, float, float] | None = None
    width: float | None = None
    height: float | None = None
    namespaces: dict[str, str] = field(default_factory=dict)
    defs: dict[str, Any] = field(default_factory=dict)

    def count_total_nodes(self) -> int:
        """Count total nodes across all paths."""
        return sum(path.count_nodes() for path in self.paths)

    def get_bounding_box(self) -> tuple[float, float, float, float]:
        """Compute bounding box of all paths."""
        all_points = []
        for path in self.paths:
            pts = path.get_all_points()
            if len(pts) > 0:
                all_points.append(pts)
        if not all_points:
            return (0.0, 0.0, 0.0, 0.0)
        combined = np.vstack(all_points)
        return (
            float(np.min(combined[:, 0])),
            float(np.min(combined[:, 1])),
            float(np.max(combined[:, 0])),
            float(np.max(combined[:, 1])),
        )


class SVGParser:
    """Parser for SVG files."""

    def __init__(self) -> None:
        """Initialize parser."""
        self._transform_stack = TransformStack()
        self._defs: dict[str, Any] = {}
        self._result: ParseResult = ParseResult()

    def parse_file(self, filepath: str) -> ParseResult:
        """Parse SVG from file."""
        tree = etree.parse(filepath)
        return self._parse_tree(tree)

    def parse_string(self, svg_string: str) -> ParseResult:
        """Parse SVG from string."""
        tree = etree.fromstring(svg_string.encode("utf-8"))
        if not isinstance(tree, etree._ElementTree):
            tree = etree.ElementTree(tree)
        return self._parse_tree(tree)

    def _parse_tree(self, tree: etree._ElementTree) -> ParseResult:
        """Parse ElementTree."""
        self._transform_stack = TransformStack()
        self._defs = {}
        self._result = ParseResult()
        root = tree.getroot()
        self._parse_svg_element(root)
        self._result.defs = self._defs
        return self._result

    def _parse_svg_element(self, elem: etree._Element) -> None:
        """Parse SVG root element."""
        tag = self._strip_namespace(elem.tag)
        if tag != "svg":
            raise ValueError(f"Expected svg element, got {tag}")
        self._result.namespaces = dict(elem.nsmap)
        self._result.width = self._parse_length(elem.get("width"))
        self._result.height = self._parse_length(elem.get("height"))
        viewbox_str = elem.get("viewBox")
        if viewbox_str:
            self._result.viewbox = self._parse_viewbox(viewbox_str)
        for child in elem:
            self._parse_element(child)

    def _parse_element(self, elem: etree._Element) -> None:
        """Parse any SVG element."""
        tag = self._strip_namespace(elem.tag)
        if tag == "defs":
            self._parse_defs(elem)
        elif tag == "g":
            self._parse_group(elem)
        elif tag == "use":
            self._parse_use(elem)
        elif tag == "symbol":
            return
        elif tag == "clipPath":
            return
        elif tag == "mask":
            return
        elif tag == "path":
            self._parse_path(elem)
        elif tag == "rect":
            self._parse_rect(elem)
        elif tag == "circle":
            self._parse_circle(elem)
        elif tag == "ellipse":
            self._parse_ellipse(elem)
        elif tag == "line":
            self._parse_line(elem)
        elif tag == "polyline":
            self._parse_polyline(elem)
        elif tag == "polygon":
            self._parse_polygon(elem)

    def _parse_defs(self, elem: etree._Element) -> None:
        """Parse defs element."""
        for child in elem:
            elem_id = child.get("id")
            if elem_id:
                self._defs[f"#{elem_id}"] = child
                self._defs[elem_id] = child

    def _parse_group(self, elem: etree._Element) -> None:
        """Parse group element."""
        transform_str = elem.get("transform")
        if transform_str:
            self._transform_stack.push(TransformParser.parse(transform_str))
        for child in elem:
            self._parse_element(child)
        if transform_str:
            self._transform_stack.pop()

    def _parse_use(self, elem: etree._Element) -> None:
        """Parse use element."""
        href = elem.get(f"{{{XLINK_NAMESPACE}}}href") or elem.get("href")
        if not href:
            return
        target = self._defs.get(href)
        if not target:
            return
        transform_str = elem.get("transform")
        if transform_str:
            self._transform_stack.push(TransformParser.parse(transform_str))
        x = self._parse_length(elem.get("x", "0")) or 0.0
        y = self._parse_length(elem.get("y", "0")) or 0.0
        if x != 0 or y != 0:
            self._transform_stack.push(TransformParser.parse(f"translate({x}, {y})"))
        self._parse_element(target)
        if x != 0 or y != 0:
            self._transform_stack.pop()
        if transform_str:
            self._transform_stack.pop()

    def _parse_path(self, elem: etree._Element) -> None:
        """Parse path element."""
        d = elem.get("d")
        if not d:
            return
        parsed = self._parse_path_data(d)
        style = self._parse_style(elem)
        fill_rule = style.get("fill-rule", elem.get("fill-rule", "nonzero"))
        parsed_path = ParsedPath(
            curves=parsed["curves"],
            is_closed=parsed["closed"],
            fill_rule=fill_rule,
            id=elem.get("id"),
            class_name=elem.get("class"),
            style=style,
        )
        self._result.paths.append(parsed_path)

    def _parse_rect(self, elem: etree._Element) -> None:
        """Parse rect element."""
        x = self._parse_length(elem.get("x", "0")) or 0.0
        y = self._parse_length(elem.get("y", "0")) or 0.0
        w = self._parse_length(elem.get("width", "0")) or 0.0
        h = self._parse_length(elem.get("height", "0")) or 0.0
        rx = self._parse_length(elem.get("rx", "0")) or 0.0
        ry = self._parse_length(elem.get("ry", "0")) or 0.0
        if rx == 0:
            rx = ry
        if ry == 0:
            ry = rx
        path_data = self._rect_to_path(x, y, w, h, rx, ry)
        parsed = self._parse_path_data(path_data)
        style = self._parse_style(elem)
        parsed_path = ParsedPath(
            curves=parsed["curves"],
            is_closed=True,
            fill_rule=style.get("fill-rule", "nonzero"),
            id=elem.get("id"),
            class_name=elem.get("class"),
            style=style,
        )
        self._result.paths.append(parsed_path)

    def _parse_circle(self, elem: etree._Element) -> None:
        """Parse circle element."""
        cx = self._parse_length(elem.get("cx", "0")) or 0.0
        cy = self._parse_length(elem.get("cy", "0")) or 0.0
        r = self._parse_length(elem.get("r", "0")) or 0.0
        path_data = self._ellipse_to_path(cx, cy, r, r)
        parsed = self._parse_path_data(path_data)
        style = self._parse_style(elem)
        parsed_path = ParsedPath(
            curves=parsed["curves"],
            is_closed=True,
            fill_rule=style.get("fill-rule", "nonzero"),
            id=elem.get("id"),
            class_name=elem.get("class"),
            style=style,
        )
        self._result.paths.append(parsed_path)

    def _parse_ellipse(self, elem: etree._Element) -> None:
        """Parse ellipse element."""
        cx = self._parse_length(elem.get("cx", "0")) or 0.0
        cy = self._parse_length(elem.get("cy", "0")) or 0.0
        rx = self._parse_length(elem.get("rx", "0")) or 0.0
        ry = self._parse_length(elem.get("ry", "0")) or 0.0
        path_data = self._ellipse_to_path(cx, cy, rx, ry)
        parsed = self._parse_path_data(path_data)
        style = self._parse_style(elem)
        parsed_path = ParsedPath(
            curves=parsed["curves"],
            is_closed=True,
            fill_rule=style.get("fill-rule", "nonzero"),
            id=elem.get("id"),
            class_name=elem.get("class"),
            style=style,
        )
        self._result.paths.append(parsed_path)

    def _parse_line(self, elem: etree._Element) -> None:
        """Parse line element."""
        x1 = self._parse_length(elem.get("x1", "0")) or 0.0
        y1 = self._parse_length(elem.get("y1", "0")) or 0.0
        x2 = self._parse_length(elem.get("x2", "0")) or 0.0
        y2 = self._parse_length(elem.get("y2", "0")) or 0.0
        path_data = f"M {x1} {y1} L {x2} {y2}"
        parsed = self._parse_path_data(path_data)
        style = self._parse_style(elem)
        parsed_path = ParsedPath(
            curves=parsed["curves"],
            is_closed=False,
            fill_rule=style.get("fill-rule", "nonzero"),
            id=elem.get("id"),
            class_name=elem.get("class"),
            style=style,
        )
        self._result.paths.append(parsed_path)

    def _parse_polyline(self, elem: etree._Element) -> None:
        """Parse polyline element."""
        points = elem.get("points", "")
        coords = self._parse_points(points)
        if len(coords) < 2:
            return
        path_data = f"M {coords[0][0]} {coords[0][1]}"
        for x, y in coords[1:]:
            path_data += f" L {x} {y}"
        parsed = self._parse_path_data(path_data)
        style = self._parse_style(elem)
        parsed_path = ParsedPath(
            curves=parsed["curves"],
            is_closed=False,
            fill_rule=style.get("fill-rule", "nonzero"),
            id=elem.get("id"),
            class_name=elem.get("class"),
            style=style,
        )
        self._result.paths.append(parsed_path)

    def _parse_polygon(self, elem: etree._Element) -> None:
        """Parse polygon element."""
        points = elem.get("points", "")
        coords = self._parse_points(points)
        if len(coords) < 3:
            return
        path_data = f"M {coords[0][0]} {coords[0][1]}"
        for x, y in coords[1:]:
            path_data += f" L {x} {y}"
        path_data += " Z"
        parsed = self._parse_path_data(path_data)
        style = self._parse_style(elem)
        parsed_path = ParsedPath(
            curves=parsed["curves"],
            is_closed=True,
            fill_rule=style.get("fill-rule", "nonzero"),
            id=elem.get("id"),
            class_name=elem.get("class"),
            style=style,
        )
        self._result.paths.append(parsed_path)

    def _parse_path_data(self, d: str) -> dict[str, Any]:
        """Parse SVG path data string with full command support."""
        curves: list[CubicBezier] = []
        current_pos = create_point(0.0, 0.0)
        start_pos = create_point(0.0, 0.0)
        last_control: Point | None = None
        is_closed = False
        tokens = self._tokenize_path(d)
        i = 0
        while i < len(tokens):
            cmd = tokens[i]
            i += 1
            if not cmd.isalpha():
                continue
            is_relative = cmd.islower()
            cmd_upper = cmd.upper()
            if cmd_upper == "M":
                x, y = float(tokens[i]), float(tokens[i + 1])
                i += 2
                current_pos = current_pos + create_point(x, y) if is_relative else create_point(x, y)
                start_pos = current_pos
                while i < len(tokens) and not tokens[i][0].isalpha():
                    x, y = float(tokens[i]), float(tokens[i + 1])
                    i += 2
                    new_pos = current_pos + create_point(x, y) if is_relative else create_point(x, y)
                    curves.append(self._line_to_bezier(current_pos, new_pos))
                    current_pos = new_pos
            elif cmd_upper == "L":
                x, y = float(tokens[i]), float(tokens[i + 1])
                i += 2
                new_pos = current_pos + create_point(x, y) if is_relative else create_point(x, y)
                curves.append(self._line_to_bezier(current_pos, new_pos))
                current_pos = new_pos
            elif cmd_upper == "H":
                x = float(tokens[i])
                i += 1
                new_pos = current_pos + create_point(x, 0) if is_relative else create_point(x, current_pos[1])
                curves.append(self._line_to_bezier(current_pos, new_pos))
                current_pos = new_pos
            elif cmd_upper == "V":
                y = float(tokens[i])
                i += 1
                new_pos = current_pos + create_point(0, y) if is_relative else create_point(current_pos[0], y)
                curves.append(self._line_to_bezier(current_pos, new_pos))
                current_pos = new_pos
            elif cmd_upper == "C":
                x1, y1 = float(tokens[i]), float(tokens[i + 1])
                x2, y2 = float(tokens[i + 2]), float(tokens[i + 3])
                x, y = float(tokens[i + 4]), float(tokens[i + 5])
                i += 6
                cp1 = current_pos + create_point(x1, y1) if is_relative else create_point(x1, y1)
                cp2 = current_pos + create_point(x2, y2) if is_relative else create_point(x2, y2)
                end = current_pos + create_point(x, y) if is_relative else create_point(x, y)
                curves.append(CubicBezier(current_pos, cp1, cp2, end))
                last_control = cp2
                current_pos = end
            elif cmd_upper == "S":
                x2, y2 = float(tokens[i]), float(tokens[i + 1])
                x, y = float(tokens[i + 2]), float(tokens[i + 3])
                i += 4
                cp1 = 2 * current_pos - last_control if last_control is not None else current_pos
                cp2 = current_pos + create_point(x2, y2) if is_relative else create_point(x2, y2)
                end = current_pos + create_point(x, y) if is_relative else create_point(x, y)
                curves.append(CubicBezier(current_pos, cp1, cp2, end))
                last_control = cp2
                current_pos = end
            elif cmd_upper == "Q":
                x1, y1 = float(tokens[i]), float(tokens[i + 1])
                x, y = float(tokens[i + 2]), float(tokens[i + 3])
                i += 4
                cp = current_pos + create_point(x1, y1) if is_relative else create_point(x1, y1)
                end = current_pos + create_point(x, y) if is_relative else create_point(x, y)
                curves.append(self._quadratic_to_cubic(current_pos, cp, end))
                last_control = cp
                current_pos = end
            elif cmd_upper == "T":
                x, y = float(tokens[i]), float(tokens[i + 1])
                i += 2
                cp = 2 * current_pos - last_control if last_control is not None else current_pos
                end = current_pos + create_point(x, y) if is_relative else create_point(x, y)
                curves.append(self._quadratic_to_cubic(current_pos, cp, end))
                last_control = cp
                current_pos = end
            elif cmd_upper == "A":
                rx, ry = float(tokens[i]), float(tokens[i + 1])
                rotation = float(tokens[i + 2])
                large_arc = int(tokens[i + 3])
                sweep = int(tokens[i + 4])
                x, y = float(tokens[i + 5]), float(tokens[i + 6])
                i += 7
                end = current_pos + create_point(x, y) if is_relative else create_point(x, y)
                arc_curves = self._arc_to_beziers(current_pos, end, rx, ry, rotation, large_arc, sweep)
                curves.extend(arc_curves)
                if arc_curves:
                    last_control = arc_curves[-1].p2
                current_pos = end
            elif cmd_upper == "Z":
                if point_distance(current_pos, start_pos) > 1e-10:
                    curves.append(self._line_to_bezier(current_pos, start_pos))
                is_closed = True
                current_pos = start_pos
        return {"curves": curves, "closed": is_closed}

    def _tokenize_path(self, d: str) -> list[str]:
        """Tokenize path data string."""
        pattern = r"([MmLlHhVvCcSsQqTtAaZz])|(-?\d+\.?\d*(?:[eE][+-]?\d+)?)"
        matches = re.findall(pattern, d)
        tokens = []
        for m in matches:
            if m[0]:
                tokens.append(m[0])
            elif m[1]:
                tokens.append(m[1])
        return tokens

    def _line_to_bezier(self, p1: Point, p2: Point) -> CubicBezier:
        """Convert line segment to cubic Bezier."""
        t = 1.0 / 3.0
        cp1 = p1 + t * (p2 - p1)
        cp2 = p1 + 2 * t * (p2 - p1)
        return CubicBezier(p1, cp1, cp2, p2)

    def _quadratic_to_cubic(self, p0: Point, p1: Point, p2: Point) -> CubicBezier:
        """Convert quadratic to cubic Bezier."""
        cp1 = p0 + (2.0 / 3.0) * (p1 - p0)
        cp2 = p2 + (2.0 / 3.0) * (p1 - p2)
        return CubicBezier(p0, cp1, cp2, p2)

    def _arc_to_beziers(self, start: Point, end: Point, rx: float, ry: float,
                        rotation: float, large_arc: int, sweep: int) -> list[CubicBezier]:
        """Convert elliptical arc to cubic Bezier curves."""
        if rx == 0 or ry == 0:
            return [self._line_to_bezier(start, end)]
        x1, y1 = start[0], start[1]
        x2, y2 = end[0], end[1]
        phi = math.radians(rotation)
        cos_phi = math.cos(phi)
        sin_phi = math.sin(phi)
        dx = (x1 - x2) / 2.0
        dy = (y1 - y2) / 2.0
        x1_prime = cos_phi * dx + sin_phi * dy
        y1_prime = -sin_phi * dx + cos_phi * dy
        rx_sq = rx * rx
        ry_sq = ry * ry
        x1_prime_sq = x1_prime * x1_prime
        y1_prime_sq = y1_prime * y1_prime
        radius_check = x1_prime_sq / rx_sq + y1_prime_sq / ry_sq
        if radius_check > 1:
            scale = math.sqrt(radius_check)
            rx *= scale
            ry *= scale
            rx_sq = rx * rx
            ry_sq = ry * ry
        numerator = rx_sq * ry_sq - rx_sq * y1_prime_sq - ry_sq * x1_prime_sq
        denominator = rx_sq * y1_prime_sq + ry_sq * x1_prime_sq
        if numerator < 0:
            numerator = 0
        if denominator == 0:
            return [self._line_to_bezier(start, end)]
        sqrt_term = math.sqrt(numerator / denominator)
        if large_arc == sweep:
            sqrt_term = -sqrt_term
        cx_prime = sqrt_term * (rx * y1_prime) / ry
        cy_prime = sqrt_term * -(ry * x1_prime) / rx
        cx = cos_phi * cx_prime - sin_phi * cy_prime + (x1 + x2) / 2.0
        cy = sin_phi * cx_prime + cos_phi * cy_prime + (y1 + y2) / 2.0
        v1x = (x1_prime - cx_prime) / rx
        v1y = (y1_prime - cy_prime) / ry
        v2x = (-x1_prime - cx_prime) / rx
        v2y = (-y1_prime - cy_prime) / ry
        angle1 = math.atan2(v1y, v1x)
        angle2 = math.atan2(v2y, v2x)
        delta_angle = angle2 - angle1
        if sweep == 1 and delta_angle < 0:
            delta_angle += 2 * math.pi
        elif sweep == 0 and delta_angle > 0:
            delta_angle -= 2 * math.pi
        arc = EllipticalArc(cx=cx, cy=cy, rx=rx, ry=ry, phi=phi,
                            start_angle=angle1, delta_angle=delta_angle)
        return arc_to_beziers(arc)

    def _rect_to_path(self, x: float, y: float, w: float, h: float, rx: float, ry: float) -> str:
        """Convert rect to path data."""
        if rx == 0 or ry == 0:
            return f"M {x} {y} h {w} v {h} h -{w} Z"
        rx = min(rx, w / 2)
        ry = min(ry, h / 2)
        return (f"M {x + rx} {y} h {w - 2 * rx} a {rx} {ry} 0 0 1 {rx} {ry}"
                f" v {h - 2 * ry} a {rx} {ry} 0 0 1 -{rx} {ry} h -{w - 2 * rx}"
                f" a {rx} {ry} 0 0 1 -{rx} -{ry} v -{h - 2 * ry}"
                f" a {rx} {ry} 0 0 1 {rx} -{ry} Z")

    def _ellipse_to_path(self, cx: float, cy: float, rx: float, ry: float) -> str:
        """Convert ellipse/circle to path data."""
        return (f"M {cx + rx} {cy} A {rx} {ry} 0 1 0 {cx - rx} {cy}"
                f" A {rx} {ry} 0 1 0 {cx + rx} {cy} Z")

    def _parse_points(self, points_str: str) -> list[tuple[float, float]]:
        """Parse points attribute string."""
        coords = re.findall(r"-?\d+\.?\d*(?:[eE][+-]?\d+)?", points_str)
        result = []
        for i in range(0, len(coords) - 1, 2):
            result.append((float(coords[i]), float(coords[i + 1])))
        return result

    def _parse_length(self, value: str | None) -> float | None:
        """Parse length value with optional units."""
        if not value:
            return None
        match = re.match(r"(-?\d+\.?\d*(?:[eE][+-]?\d+)?)", value)
        return float(match.group(1)) if match else None

    def _parse_viewbox(self, value: str) -> tuple[float, float, float, float]:
        """Parse viewBox attribute."""
        parts = [float(x) for x in re.findall(r"-?\d+\.?\d*(?:[eE][+-]?\d+)?", value)]
        return (parts[0], parts[1], parts[2], parts[3]) if len(parts) >= 4 else (0.0, 0.0, 0.0, 0.0)

    def _parse_style(self, elem: etree._Element) -> dict[str, str]:
        """Parse element style attributes."""
        style = {}
        style_str = elem.get("style")
        if style_str:
            for pair in style_str.split(";"):
                if ":" in pair:
                    k, v = pair.split(":", 1)
                    style[k.strip()] = v.strip()
        for attr in ["fill", "stroke", "stroke-width", "fill-rule", "opacity"]:
            v = elem.get(attr)
            if v:
                style[attr] = v
        return style

    def _strip_namespace(self, tag: str) -> str:
        """Remove namespace from tag name."""
        return tag.split("}", 1)[1] if "}" in tag else tag
