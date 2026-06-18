# Contributing to SVG Simplifier

Thank you for your interest in contributing! Please read these rules carefully before submitting any changes.

---

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Project Structure](#project-structure)
- [Development Workflow](#development-workflow)
- [Coding Standards](#coding-standards)
- [Testing Requirements](#testing-requirements)
- [Commit Convention](#commit-convention)
- [Pull Request Process](#pull-request-process)
- [Dependency Management](#dependency-management)

---

## Code of Conduct

Be respectful, constructive, and professional. Harassment, discrimination, or toxic behavior of any kind will not be tolerated.

---

## Getting Started

```bash
git clone https://github.com/svg-simplifier/svg-simplifier.git
cd svg-simplifier
pip install -e ".[dev]"
```

Verify the environment works:

```bash
pytest
svgsimplify --help
```

---

## Project Structure

```
svg_simplifier/
├── simplifier/           # Core package — all production logic lives here
│   ├── __init__.py       # Public API surface
│   ├── cli.py            # Click-based command-line interface
│   ├── parser.py         # SVG parsing (lxml + svgpathtools)
│   ├── optimizer.py      # Main simplification engine / pipeline
│   ├── bezier.py         # Bézier math (Schneider curve fitting)
│   ├── geometry.py       # Geometric primitives and utilities
│   ├── transforms.py     # SVG transformation matrix handling
│   ├── svg_writer.py     # Serialization back to SVG
│   └── utils.py          # Shared utilities
├── tests/                # pytest test suite — mirrors simplifier/ structure
├── benchmarks/           # Performance benchmark scripts
├── examples/             # Sample SVG files for manual testing
├── public/               # Static assets (logo.svg, icon.svg)
├── requirements.txt      # Pinned runtime dependencies
├── pyproject.toml        # Build system, tool config (black, ruff, mypy, pytest)
└── README.md
```

**Rules for project structure:**

- Do **not** add new top-level directories without prior discussion in an issue.
- Do **not** add new modules inside `simplifier/` unless the feature genuinely cannot fit in an existing module.
- `public/` is for static assets only — no Python code goes there.
- `examples/` contains only `.svg` files used for documentation and manual verification.
- `benchmarks/` is separate from `tests/` — benchmark scripts must not be imported by core code.

---

## Development Workflow

1. Open or reference a GitHub issue for non-trivial changes.
2. Create a feature branch from `main`:
   ```bash
   git checkout -b feat/short-description
   ```
3. Implement changes following the standards below.
4. Run the full quality pipeline (see [Coding Standards](#coding-standards)).
5. Push the branch and open a Pull Request.

---

## Coding Standards

### Python Version

- Minimum: **Python 3.12**
- New syntax features up to 3.13 are allowed.

### Formatting — `black`

```bash
black simplifier/ tests/ benchmarks/
```

- Line length: **100 characters**
- Config is in `pyproject.toml` under `[tool.black]`
- Do **not** override `black` formatting manually.

### Linting — `ruff`

```bash
ruff check simplifier/ tests/
```

- All rules in `pyproject.toml` `[tool.ruff]` must pass with zero warnings.
- `ruff` handles import sorting (replaces `isort`).

### Type Checking — `mypy`

```bash
mypy simplifier/
```

- **All public functions and methods must have complete type annotations.**
- `mypy` is configured in strict mode — `disallow_untyped_defs = true`.
- Do not use `# type: ignore` unless absolutely unavoidable; add a comment explaining why.

### Run everything at once

```bash
black simplifier/ tests/ benchmarks/ && ruff check simplifier/ tests/ && mypy simplifier/ && pytest
```

---

## Testing Requirements

- Every new feature or bug fix **must** include tests.
- Tests live in `tests/` and mirror the module they test (e.g., `simplifier/geometry.py` → `tests/test_geometry.py`).
- **Coverage must not decrease.** PRs that reduce coverage will be rejected.
- Use `pytest` markers:
  - `@pytest.mark.slow` — tests that take >1 second
  - `@pytest.mark.benchmark` — performance benchmarks

```bash
# Run all tests with coverage
pytest --cov=simplifier --cov-report=term-missing

# Run a specific module's tests
pytest tests/test_geometry.py

# Exclude slow tests during development
pytest -m "not slow"
```

---

## Commit Convention

This project uses **Conventional Commits**:

```
<type>(<scope>): <short description>
```

| Type | When to use |
|------|-------------|
| `feat` | New feature |
| `fix` | Bug fix |
| `docs` | Documentation only |
| `refactor` | Code restructure without behavior change |
| `test` | Adding or fixing tests |
| `chore` | Build system, dependency updates, tooling |
| `perf` | Performance improvement |

Examples:
```
feat(optimizer): add curve merging threshold option
fix(parser): handle missing viewBox attribute gracefully
docs: add logo and open source license to README
test(geometry): add edge cases for collinear point removal
```

---

## Pull Request Process

1. Target branch: `main`
2. Title must follow Conventional Commits format.
3. Description must include:
   - What the change does
   - Why it is needed
   - How it was tested
4. All CI checks must pass before review.
5. At least one approval is required before merging.
6. Squash-merge is preferred to keep history clean.

---

## Dependency Management

- **Runtime dependencies**: add to `[project.dependencies]` in `pyproject.toml` with a minimum version constraint.
- **Development dependencies**: add to `[project.optional-dependencies]` under the `dev` key.
- Also update `requirements.txt` with `pip freeze > requirements.txt` after changing deps.
- Never add dependencies that duplicate functionality already provided by existing deps.
- Prefer stdlib solutions when the dependency would be trivial.

---

## Security

- Never commit secrets, API keys, tokens, passwords, or personal data.
- If you discover a security vulnerability, report it privately via a GitHub Security Advisory — do **not** open a public issue.

---

*By contributing you agree that your contributions will be licensed under the MIT License.*
