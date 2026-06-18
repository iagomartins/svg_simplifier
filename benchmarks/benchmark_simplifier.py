"""Performance benchmark for SVG Simplifier.

Target: Process 1000 paths under 5 seconds.
"""

from __future__ import annotations

import random
import sys
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent.parent))

from simplifier.optimizer import SimplificationOptions, Simplifier
from simplifier.svg_writer import SVGWriter
from simplifier.parser import ParseResult, ParsedPath
from simplifier.bezier import CubicBezier
from simplifier.geometry import create_point


def generate_random_curve() -> CubicBezier:
    """Generate a random cubic Bezier curve."""
    return CubicBezier(
        create_point(random.uniform(0, 500), random.uniform(0, 500)),
        create_point(random.uniform(0, 500), random.uniform(0, 500)),
        create_point(random.uniform(0, 500), random.uniform(0, 500)),
        create_point(random.uniform(0, 500), random.uniform(0, 500)),
    )


def generate_test_svg(num_paths: int, curves_per_path: int = 10) -> str:
    """Generate test SVG with specified number of paths.

    Args:
        num_paths: Number of paths to generate.
        curves_per_path: Number of curves per path.

    Returns:
        SVG string.
    """
    paths = []
    for i in range(num_paths):
        d_parts = ["M 100 100"]
        for _ in range(curves_per_path):
            c = generate_random_curve()
            d_parts.append(
                f"C {c.p1[0]:.2f} {c.p1[1]:.2f} "
                f"{c.p2[0]:.2f} {c.p2[1]:.2f} "
                f"{c.p3[0]:.2f} {c.p3[1]:.2f}"
            )
        d_parts.append("Z")
        paths.append(f'<path d="{" ".join(d_parts)}" id="path{i}"/>')

    svg = f'''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 500 500">
    {''.join(paths)}
</svg>'''
    return svg


def benchmark_simplification(num_paths: int, target_time: float = 5.0) -> dict:
    """Run simplification benchmark.

    Args:
        num_paths: Number of paths to process.
        target_time: Target time in seconds.

    Returns:
        Benchmark results dictionary.
    """
    print(f"Generating test SVG with {num_paths} paths...")
    svg_string = generate_test_svg(num_paths)

    print("Parsing SVG...")
    from simplifier.parser import SVGParser
    parser = SVGParser()
    parse_result = parser.parse_string(svg_string)
    original_nodes = parse_result.count_total_nodes()
    print(f"Original nodes: {original_nodes}")

    print(f"Simplifying {len(parse_result.paths)} paths...")
    simplifier = Simplifier(SimplificationOptions(tolerance=0.001))

    start_time = time.perf_counter()
    result = simplifier._simplify_parse_result(parse_result)
    elapsed = time.perf_counter() - start_time

    reduction = (result.original_nodes - result.optimized_nodes) / result.original_nodes * 100

    results = {
        "num_paths": num_paths,
        "original_nodes": result.original_nodes,
        "optimized_nodes": result.optimized_nodes,
        "reduction_percentage": reduction,
        "elapsed_time": elapsed,
        "paths_per_second": num_paths / elapsed,
        "nodes_per_second": result.original_nodes / elapsed,
        "target_met": elapsed <= target_time,
    }

    return results


def main():
    """Run benchmarks."""
    print("=" * 60)
    print("SVG Simplifier Performance Benchmark")
    print("=" * 60)
    print()

    benchmarks = [10, 100, 500, 1000]

    for num_paths in benchmarks:
        print(f"\n--- Benchmark: {num_paths} paths ---")
        results = benchmark_simplification(num_paths)

        print(f"  Original nodes:    {results['original_nodes']:,}")
        print(f"  Optimized nodes:   {results['optimized_nodes']:,}")
        print(f"  Reduction:         {results['reduction_percentage']:.1f}%")
        print(f"  Elapsed time:      {results['elapsed_time']:.3f}s")
        print(f"  Paths/second:      {results['paths_per_second']:.1f}")
        print(f"  Nodes/second:      {results['nodes_per_second']:,.0f}")

        if num_paths == 1000:
            target = 5.0
            if results['elapsed_time'] <= target:
                print(f"  ✓ Target met: {results['elapsed_time']:.3f}s <= {target}s")
            else:
                print(f"  ✗ Target missed: {results['elapsed_time']:.3f}s > {target}s")

    print("\n" + "=" * 60)


if __name__ == "__main__":
    main()
