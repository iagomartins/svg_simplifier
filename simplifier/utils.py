"""Utility functions for SVG simplification.

This module provides helper functions for logging, timing, and data processing.
"""

from __future__ import annotations

import sys
import time
from collections.abc import Generator
from contextlib import contextmanager
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from types import TracebackType


class Timer:
    """Context manager for timing code blocks.

    Example:
        >>> with Timer() as timer:
        ...     do_something()
        >>> print(f"Elapsed: {timer.elapsed:.3f}s")
    """

    def __init__(self) -> None:
        """Initialize timer."""
        self._start: float = 0.0
        self._end: float = 0.0
        self.elapsed: float = 0.0

    def __enter__(self) -> Timer:
        """Start timer on context entry.

        Returns:
            Self for accessing elapsed time later.
        """
        self._start = time.perf_counter()
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        """Stop timer on context exit."""
        self._end = time.perf_counter()
        self.elapsed = self._end - self._start


@contextmanager
def progress_spinner(message: str = "Processing") -> Generator[None, None, None]:
    """Context manager showing a progress spinner.

    Args:
        message: Message to display with spinner.

    Yields:
        None.
    """
    import itertools
    import threading

    spinner = itertools.cycle(["|", "/", "-", "\\"])
    stop_event = threading.Event()

    def spin() -> None:
        while not stop_event.is_set():
            sys.stdout.write(f"\r{message} {next(spinner)}")
            sys.stdout.flush()
            stop_event.wait(0.1)
        sys.stdout.write(f"\r{message} ✓\n")
        sys.stdout.flush()

    thread = threading.Thread(target=spin)
    thread.start()

    try:
        yield
    finally:
        stop_event.set()
        thread.join()


def format_number(num: float, precision: int = 6) -> str:
    """Format number with specified precision, removing trailing zeros.

    Args:
        num: Number to format.
        precision: Maximum decimal places.

    Returns:
        Formatted string.
    """
    formatted = f"{num:.{precision}f}"
    return formatted.rstrip("0").rstrip(".")


def format_percentage(value: float, decimals: int = 1) -> str:
    """Format percentage with specified decimal places.

    Args:
        value: Value to format (e.g., 0.75 for 75%).
        decimals: Number of decimal places.

    Returns:
        Formatted percentage string.
    """
    return f"{value * 100:.{decimals}f}%"


def format_time(seconds: float) -> str:
    """Format time duration in human-readable format.

    Args:
        seconds: Time in seconds.

    Returns:
        Formatted time string.
    """
    if seconds < 0.001:
        return f"{seconds * 1000000:.1f}µs"
    if seconds < 1:
        return f"{seconds * 1000:.1f}ms"
    if seconds < 60:
        return f"{seconds:.2f}s"
    if seconds < 3600:
        minutes = int(seconds // 60)
        secs = seconds % 60
        return f"{minutes}m {secs:.1f}s"
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    return f"{hours}h {minutes}m"


def format_size(bytes_val: int) -> str:
    """Format byte size in human-readable format.

    Args:
        bytes_val: Size in bytes.

    Returns:
        Formatted size string.
    """
    units = ["B", "KB", "MB", "GB"]
    size = float(bytes_val)
    unit_idx = 0

    while size >= 1024 and unit_idx < len(units) - 1:
        size /= 1024
        unit_idx += 1

    return f"{size:.1f} {units[unit_idx]}"


class Statistics:
    """Container for simplification statistics.

    Attributes:
        original_nodes: Number of nodes in original SVG.
        optimized_nodes: Number of nodes in optimized SVG.
        reduction_percentage: Percentage of node reduction.
        execution_time: Total execution time in seconds.
        max_error: Maximum geometric error.
        bounding_box: Bounding box tuple (min_x, min_y, max_x, max_y).
    """

    def __init__(self) -> None:
        """Initialize statistics container."""
        self.original_nodes: int = 0
        self.optimized_nodes: int = 0
        self.reduction_percentage: float = 0.0
        self.execution_time: float = 0.0
        self.max_error: float = 0.0
        self.bounding_box: tuple[float, float, float, float] = (0.0, 0.0, 0.0, 0.0)

    def compute_reduction(self) -> None:
        """Compute reduction percentage from node counts."""
        if self.original_nodes > 0:
            self.reduction_percentage = (
                self.original_nodes - self.optimized_nodes
            ) / self.original_nodes

    def __str__(self) -> str:
        """Return formatted statistics string.

        Returns:
            Multi-line formatted statistics.
        """
        lines = [
            "Simplification Statistics",
            "=" * 40,
            f"Original nodes:     {self.original_nodes}",
            f"Optimized nodes:    {self.optimized_nodes}",
            f"Reduction:          {format_percentage(self.reduction_percentage)}",
            f"Execution time:     {format_time(self.execution_time)}",
            f"Max error:          {format_number(self.max_error)}",
            f"Bounding box:       ({format_number(self.bounding_box[0])}, "
            f"{format_number(self.bounding_box[1])}, "
            f"{format_number(self.bounding_box[2])}, "
            f"{format_number(self.bounding_box[3])})",
        ]
        return "\n".join(lines)


def chunk_list(lst: list[Any], chunk_size: int) -> Generator[list[Any], None, None]:
    """Split list into chunks of specified size.

    Args:
        lst: List to split.
        chunk_size: Size of each chunk.

    Yields:
        Chunks of the list.
    """
    for i in range(0, len(lst), chunk_size):
        yield lst[i : i + chunk_size]


def count_nodes_in_path_data(path_data: str) -> int:
    """Count approximate number of nodes in SVG path data.

    Args:
        path_data: SVG path d attribute string.

    Returns:
        Approximate node count.
    """
    import re

    commands = re.findall(r"[MmLlHhVvCcSsQqTtAaZz]", path_data)
    return len(commands)


def safe_divide(numerator: float, denominator: float, default: float = 0.0) -> float:
    """Safely divide, returning default if denominator is zero.

    Args:
        numerator: Numerator value.
        denominator: Denominator value.
        default: Default value if division by zero.

    Returns:
        Division result or default.
    """
    if denominator == 0:
        return default
    return numerator / denominator


def clamp(value: float, min_val: float, max_val: float) -> float:
    """Clamp value to range [min_val, max_val].

    Args:
        value: Value to clamp.
        min_val: Minimum allowed value.
        max_val: Maximum allowed value.

    Returns:
        Clamped value.
    """
    return max(min_val, min(max_val, value))


class PathHasher:
    """Hashable wrapper for path objects."""

    def __init__(self, path: Any) -> None:
        """Initialize with path object.

        Args:
            path: Path object to wrap.
        """
        self.path = path
        self._hash = hash(str(path))

    def __hash__(self) -> int:
        """Return hash of wrapped path.

        Returns:
            Hash value.
        """
        return self._hash

    def __eq__(self, other: object) -> bool:
        """Check equality with another PathHasher.

        Args:
            other: Object to compare.

        Returns:
            True if paths are equal.
        """
        if not isinstance(other, PathHasher):
            return NotImplemented
        return self._hash == other._hash


def unique_elements(seq: list[Any]) -> list[Any]:
    """Remove duplicate elements while preserving order.

    Args:
        seq: List with potential duplicates.

    Returns:
        List with duplicates removed.
    """
    seen: set[Any] = set()
    result: list[Any] = []
    for item in seq:
        if item not in seen:
            seen.add(item)
            result.append(item)
    return result
