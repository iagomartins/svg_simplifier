"""Pytest configuration and fixtures."""

from __future__ import annotations

import pytest

from simplifier.optimizer import SimplificationOptions
from simplifier.parser import SVGParser


@pytest.fixture
def parser():
    """Return SVG parser instance."""
    return SVGParser()


@pytest.fixture
def default_options():
    """Return default simplification options."""
    return SimplificationOptions()


@pytest.fixture
def sample_svg():
    """Return sample SVG string."""
    return """<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="100" height="100">
    <path d="M 0 0 L 100 0 L 100 100 L 0 100 Z" fill="red"/>
</svg>"""


@pytest.fixture
def complex_svg():
    """Return complex SVG with multiple shapes."""
    return """<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 200">
    <rect x="10" y="10" width="50" height="50"/>
    <circle cx="100" cy="100" r="40"/>
    <polygon points="150,10 190,50 150,90 110,50"/>
    <path d="M 0 150 Q 50 100 100 150 T 200 150"/>
</svg>"""


@pytest.fixture
def curved_path_svg():
    """Return SVG with curved paths."""
    return """<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="500" height="500">
    <path d="M 100 250 C 100 100 400 100 400 250" fill="none" stroke="black"/>
</svg>"""


@pytest.fixture
def arc_path_svg():
    """Return SVG with arc paths."""
    return """<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="200" height="200">
    <path d="M 100 100 A 50 50 0 1 1 150 150" fill="none" stroke="black"/>
</svg>"""
