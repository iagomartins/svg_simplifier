# SVG Simplifier — AI Rules

These rules govern how AI assistants (Cascade/Windsurf) must behave when working in this repository.
They exist to preserve the current project structure, coding standards, and design decisions.

---

## 1. Project Identity

- This is a **pure Python library** for SVG path geometry simplification.
- The package name is `svg-simplifier`; the importable package is `simplifier`.
- It targets **Python 3.12+** exclusively.
- License: **MIT** (open source).

---

## 2. Immutable Project Structure

Never restructure, rename, move, or delete any of the following without explicit user instruction:

```
svg_simplifier/
├── simplifier/       ← core package; all production Python code lives here
│   ├── __init__.py
│   ├── cli.py
│   ├── parser.py
│   ├── optimizer.py
│   ├── bezier.py
│   ├── geometry.py
│   ├── transforms.py
│   ├── svg_writer.py
│   └── utils.py
├── tests/            ← pytest suite; mirrors simplifier/ structure
├── benchmarks/       ← standalone benchmark scripts
├── examples/         ← .svg sample files only
├── public/           ← static assets (logo.svg, icon.svg); no Python code
├── LICENSE
├── CONTRIBUTING.md
├── requirements.txt
├── pyproject.toml
└── README.md
```

**Rules:**
- Do not create new top-level directories.
- Do not add Python modules outside `simplifier/` or `tests/`.
- Do not place Python code in `public/` or `examples/`.
- Do not split `simplifier/` into sub-packages without explicit user approval.

---

## 3. Module Responsibilities (Do Not Cross Boundaries)

| Module | Responsibility |
|--------|----------------|
| `cli.py` | Click CLI only — no business logic |
| `parser.py` | SVG/XML parsing — lxml + svgpathtools |
| `optimizer.py` | Simplification pipeline orchestration |
| `bezier.py` | Bézier math — Schneider curve fitting, subdivision |
| `geometry.py` | Geometric primitives — points, vectors, angles |
| `transforms.py` | SVG transformation matrices |
| `svg_writer.py` | Serialization to SVG string/file |
| `utils.py` | Shared helpers — no domain logic |

Do not move logic between modules arbitrarily. Respect these boundaries.

---

## 4. Coding Standards

### Style
- Formatter: **`black`** with `line-length = 100`.
- Linter: **`ruff`** — all rules in `pyproject.toml` must pass.
- Do not manually override `black` formatting.

### Types
- All public functions must have **complete type annotations**.
- `mypy` is in strict mode. Do not add `# type: ignore` without a mandatory inline comment explaining why.
- Do not use `Any` unless there is no alternative.

### Imports
- Imports must always be at the top of every file.
- Import order is managed by `ruff` (isort rules). Do not reorder manually.

---

## 5. Testing Rules

- Every non-trivial change must be accompanied by tests in `tests/`.
- Test file naming: `test_<module_name>.py` — must mirror the module being tested.
- **Never delete or weaken existing tests.**
- Coverage must not decrease across PRs.
- Use `conftest.py` for shared fixtures — do not duplicate fixture code.

```bash
pytest --cov=simplifier --cov-report=term-missing
```

---

## 6. Dependencies

- Runtime deps: `pyproject.toml` → `[project.dependencies]`.
- Dev deps: `pyproject.toml` → `[project.optional-dependencies]` → `dev`.
- Also reflected in `requirements.txt`.
- Do **not** add new runtime dependencies without user approval.
- Do not introduce dependencies that duplicate existing ones (e.g., no new XML parsers beside lxml).

Current runtime dependencies (do not replace without user approval):
- `numpy`, `scipy` — numerical computing
- `svgpathtools` — SVG path parsing
- `lxml` — XML processing
- `shapely` — geometry operations
- `click` — CLI framework

---

## 7. Public API Stability

The public API is exported from `simplifier/__init__.py`. Do not:
- Remove or rename any exported symbol without user direction.
- Change existing function signatures in a breaking way.
- Add mandatory positional parameters to existing functions.

---

## 8. Configuration Files — Do Not Modify Without Instruction

| File | Owner |
|------|-------|
| `pyproject.toml` | Build system + all tool config |
| `requirements.txt` | Pinned dependencies |
| `.windsurf/rules.md` | This file |

Do not change `[tool.black]`, `[tool.ruff]`, `[tool.mypy]`, or `[tool.pytest.ini_options]` sections without user approval.

---

## 9. Documentation Rules

- `README.md` is the primary user-facing document. Keep it accurate and up to date with any API changes.
- `CONTRIBUTING.md` is the developer guide. Update it when development rules change.
- Do not remove the logo (`public/logo.svg`) from the README header.
- Do not change the license section in README or the `LICENSE` file.

---

## 10. Prohibited Actions

The AI must **never**:
- Delete any existing file without explicit user instruction.
- Commit or expose secrets, credentials, or personal data.
- Replace the MIT license with any other license.
- Introduce a web server, database, or external service dependency.
- Rewrite the entire codebase speculatively.
- Change the package name `svg-simplifier` or the importable name `simplifier`.
- Remove test coverage from existing test files.

---

*These rules must be followed in every AI-assisted session in this repository.*
