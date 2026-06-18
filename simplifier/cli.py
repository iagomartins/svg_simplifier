"""Command-line interface for SVG Simplifier.

Provides the svgsimplify command with options for controlling
the simplification process and output.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import TYPE_CHECKING

import click

from simplifier.optimizer import SimplificationOptions, Simplifier
from simplifier.parser import SVGParser
from simplifier.utils import Statistics

if TYPE_CHECKING:
    from collections.abc import Sequence


def validate_tolerance(
    ctx: click.Context, param: click.Parameter, value: float
) -> float:
    """Validate tolerance parameter.

    Args:
        ctx: Click context.
        param: Parameter being validated.
        value: Value to validate.

    Returns:
        Validated value.

    Raises:
        click.BadParameter: If value is invalid.
    """
    if value < 0:
        raise click.BadParameter("Tolerance must be non-negative")
    return value


def validate_corner_angle(
    ctx: click.Context, param: click.Parameter, value: float
) -> float:
    """Validate corner angle parameter.

    Args:
        ctx: Click context.
        param: Parameter being validated.
        value: Value to validate.

    Returns:
        Validated value.

    Raises:
        click.BadParameter: If value is invalid.
    """
    if value < 0 or value > 180:
        raise click.BadParameter("Corner angle must be between 0 and 180 degrees")
    import math

    return math.radians(value)


@click.command()
@click.argument("input_file", type=click.Path(exists=True, dir_okay=False))
@click.argument("output_file", type=click.Path(dir_okay=False))
@click.option(
    "--tolerance",
    "-t",
    default=0.001,
    show_default=True,
    callback=validate_tolerance,
    help="Simplification tolerance as fraction of bounding box diagonal",
)
@click.option(
    "--max-error",
    "-e",
    default=0.0005,
    show_default=True,
    callback=validate_tolerance,
    help="Maximum curve fitting error as fraction of bounding box diagonal",
)
@click.option(
    "--corner-angle",
    "-c",
    default=30.0,
    show_default=True,
    callback=validate_corner_angle,
    help="Corner detection angle in degrees",
)
@click.option(
    "--remove-duplicates/--keep-duplicates",
    default=True,
    show_default=True,
    help="Remove duplicate points",
)
@click.option(
    "--merge-curves/--no-merge-curves",
    default=True,
    show_default=True,
    help="Merge adjacent curves when possible",
)
@click.option(
    "--verbose",
    "-v",
    is_flag=True,
    help="Verbose output",
)
@click.option(
    "--stats",
    "-s",
    is_flag=True,
    help="Print statistics after processing",
)
@click.option(
    "--precision",
    "-p",
    default=6,
    show_default=True,
    type=int,
    help="Decimal precision for output coordinates",
)
@click.version_option(version="1.0.0", prog_name="svgsimplify")
def main(
    input_file: str,
    output_file: str,
    tolerance: float,
    max_error: float,
    corner_angle: float,
    remove_duplicates: bool,
    merge_curves: bool,
    verbose: bool,
    stats: bool,
    precision: int,
) -> None:
    """Simplify SVG path geometry while preserving visual appearance.

    INPUT_FILE: Path to input SVG file
    OUTPUT_FILE: Path for output SVG file
    """
    input_path = Path(input_file)
    output_path = Path(output_file)

    if verbose:
        click.echo(f"Reading {input_path}...")

    try:
        parser = SVGParser()
        parse_result = parser.parse_file(str(input_path))
        original_nodes = parse_result.count_total_nodes()

        if verbose:
            click.echo(f"Found {len(parse_result.paths)} path(s)")
            click.echo(f"Original node count: {original_nodes}")

    except Exception as e:
        click.echo(f"Error reading input file: {e}", err=True)
        sys.exit(1)

    options = SimplificationOptions(
        tolerance=tolerance,
        max_error=max_error,
        corner_angle=corner_angle,
        remove_duplicates=remove_duplicates,
        merge_curves=merge_curves,
        precision=precision,
    )

    simplifier = Simplifier(options)
    statistics = Statistics()

    try:
        result = simplifier.simplify_file(
            str(input_path), str(output_path), statistics
        )
    except Exception as e:
        click.echo(f"Error during simplification: {e}", err=True)
        sys.exit(1)

    if stats or verbose:
        click.echo()
        click.echo(statistics)

    if verbose:
        click.echo()
        click.echo(f"Output written to: {output_path}")

    if result.reduction_percentage < 0.1:
        click.echo()
        click.echo(
            "Warning: Low reduction achieved. Consider increasing tolerance."
        )


if __name__ == "__main__":
    main()
