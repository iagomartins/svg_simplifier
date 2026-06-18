"""Tests for utility functions."""

from __future__ import annotations

import time

import pytest

from simplifier.utils import (
    Statistics,
    Timer,
    clamp,
    chunk_list,
    format_number,
    format_percentage,
    format_size,
    format_time,
    safe_divide,
    unique_elements,
)


class TestTimer:
    """Test timer utility."""

    def test_timer_context(self) -> None:
        """Test timer as context manager."""
        with Timer() as timer:
            time.sleep(0.01)
        assert timer.elapsed >= 0.01

    def test_timer_elapsed(self) -> None:
        """Test elapsed time recording."""
        timer = Timer()
        with timer:
            time.sleep(0.01)
        assert timer.elapsed > 0


class TestFormatting:
    """Test formatting utilities."""

    def test_format_number(self) -> None:
        """Test number formatting."""
        assert format_number(3.14159, 2) == "3.14"
        assert format_number(3.0, 2) == "3"
        assert format_number(0.0, 2) == "0"

    def test_format_percentage(self) -> None:
        """Test percentage formatting."""
        assert format_percentage(0.756, 1) == "75.6%"
        assert format_percentage(1.0, 0) == "100%"

    def test_format_time_microseconds(self) -> None:
        """Test microsecond formatting."""
        result = format_time(0.000001)
        assert "µs" in result

    def test_format_time_milliseconds(self) -> None:
        """Test millisecond formatting."""
        result = format_time(0.001)
        assert "ms" in result

    def test_format_time_seconds(self) -> None:
        """Test second formatting."""
        result = format_time(1.5)
        assert "s" in result and "ms" not in result

    def test_format_time_minutes(self) -> None:
        """Test minute formatting."""
        result = format_time(65.5)
        assert "m" in result

    def test_format_size_bytes(self) -> None:
        """Test byte formatting."""
        assert format_size(500) == "500.0 B"

    def test_format_size_kilobytes(self) -> None:
        """Test kilobyte formatting."""
        assert "KB" in format_size(1024)

    def test_format_size_megabytes(self) -> None:
        """Test megabyte formatting."""
        assert "MB" in format_size(1024 * 1024)


class TestSafeOperations:
    """Test safe operations."""

    def test_safe_divide_normal(self) -> None:
        """Test safe divide with normal case."""
        assert safe_divide(10, 2, 0) == 5.0

    def test_safe_divide_by_zero(self) -> None:
        """Test safe divide by zero."""
        assert safe_divide(10, 0, 999) == 999

    def test_clamp_within_range(self) -> None:
        """Test clamp within range."""
        assert clamp(5, 0, 10) == 5

    def test_clamp_below_range(self) -> None:
        """Test clamp below range."""
        assert clamp(-5, 0, 10) == 0

    def test_clamp_above_range(self) -> None:
        """Test clamp above range."""
        assert clamp(15, 0, 10) == 10


class TestListOperations:
    """Test list operations."""

    def test_chunk_list(self) -> None:
        """Test list chunking."""
        lst = [1, 2, 3, 4, 5, 6, 7, 8, 9]
        chunks = list(chunk_list(lst, 3))
        assert len(chunks) == 3
        assert chunks[0] == [1, 2, 3]

    def test_chunk_list_partial(self) -> None:
        """Test chunking with partial last chunk."""
        lst = [1, 2, 3, 4, 5]
        chunks = list(chunk_list(lst, 3))
        assert len(chunks) == 2
        assert chunks[1] == [4, 5]

    def test_unique_elements(self) -> None:
        """Test unique elements."""
        lst = [1, 2, 2, 3, 3, 3, 4]
        result = unique_elements(lst)
        assert result == [1, 2, 3, 4]

    def test_unique_elements_order(self) -> None:
        """Test unique elements preserves order."""
        lst = [3, 1, 2, 1, 3, 2]
        result = unique_elements(lst)
        assert result == [3, 1, 2]


class TestStatistics:
    """Test statistics container."""

    def test_init(self) -> None:
        """Test initialization."""
        stats = Statistics()
        assert stats.original_nodes == 0
        assert stats.optimized_nodes == 0
        assert stats.reduction_percentage == 0.0

    def test_compute_reduction(self) -> None:
        """Test reduction computation."""
        stats = Statistics()
        stats.original_nodes = 100
        stats.optimized_nodes = 50
        stats.compute_reduction()
        assert stats.reduction_percentage == 0.5

    def test_str(self) -> None:
        """Test string representation."""
        stats = Statistics()
        stats.original_nodes = 100
        stats.optimized_nodes = 50
        stats.execution_time = 1.5
        stats.compute_reduction()
        result = str(stats)
        assert "100" in result
        assert "50" in result
        assert "50.0%" in result or "50%" in result
