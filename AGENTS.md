# Tapen Agent Guide

## Project Overview

Tapen is a Python application for composing and printing labels on Brother P-touch printers. It supports USB discovery and network printing for the registered devices, currently including the PT-P700 and PT-P750W families. The project is licensed under GPL-3.0-or-later.

The repository uses a `src` layout and uv for packaging and dependency management:

- `src/tapen/` contains the application layer: CLI, configuration, library loading, rendering, and printer abstractions.
- `src/ptouch_py/` contains the low-level P-touch protocol implementation and USB/TCP transports.
- `src/tapen/resources/` contains the built-in `std` template library.
- `examples/` contains example template libraries and rendering input.
- `development/` contains setup, copyright, and local CLI helper scripts.
- `tapen.spec` is the PyInstaller configuration for the windowed single-binary build.
- `docs/` contains user-facing documentation and protocol reference material.

There is currently no `tests/` directory or configured test runner. Use static checks and targeted manual smoke tests when changing behavior.

## Environment and Dependencies

- Use Python 3.14 for development and CI. Project metadata permits Python `>=3.11,<3.16`.
- The normal development environment is the repository-local `venv/` directory.
- Install uv at system level. The Makefile sets `UV_PROJECT_ENVIRONMENT` to the repository-local `venv/` directory and invokes tools through uv.
- System libraries required by WeasyPrint may be needed for local rendering/builds. USB access may also require the rules in `udev-rule.txt`.
- Do not commit `venv/`, build output, distribution archives, caches, or generated metadata; these are covered by `.gitignore`.

Initial setup:

```bash
make setup
```

This verifies `python3.14`, `uv`, and `sed`, creates `venv/`, installs dependencies from `uv.lock` plus the `dev` group, and installs pre-commit hooks. The `tapen` and `tpp` console scripts are installed by uv.

For an already-created environment, synchronize exactly to `uv.lock` with:

```bash
make deps-sync
```

Use `NO_VENV=True` when the shell already has the intended environment activated or when running in CI:

```bash
make deps NO_VENV=True
```

## Common Commands

The default Make target is `pre_commit`, which runs pre-commit hooks and the full lint target.

```bash
make pre_commit       # hooks plus formatting checks, Ruff lint, and MyPy
make lint             # formatting checks, Ruff lint, and MyPy
make format           # apply Ruff import sorting and formatting under src/
make check-format     # check formatting without changing files
make mypy             # type-check src/tapen and src/ptouch_py
make build            # copyright headers, format, lint, clean, then uv build
make package          # uv build without the complete validation sequence
make single-binary    # PyInstaller build using tapen.spec
make clean            # remove generated build/dist/egg-info/pytest cache output
```

`make build` is intentionally mutating: it applies copyright headers, formats source files, and removes build artifacts before creating uv distributions. Review the diff after running it.

Dependency and release helpers:

```bash
make deps-update       # update dependencies and the lock file
make deps-lock         # regenerate the lock file
make deps-tree         # display the uv dependency tree
make changelog         # generate an incremental changelog with Commitizen
make release           # run Commitizen version bump and changelog generation
make print-version
```

Run a CLI smoke test without touching a physical printer:

```bash
tapen print --skip-printing 'Hello world'
```

Skip-printing still requires cached tape information unless a real printer is available; use a real device for status and printing paths.

## Quality Rules

- Use Ruff as the formatter, import sorter, and linter. Do not introduce Black, isort, or flake8 configuration.
- Ruff uses a 120-character line limit and targets `py311`; its configured rule set includes security, bugbear, complexity, docstring, import, pyupgrade, and related checks.
- MyPy targets Python 3.11, shows error codes, and checks both `src/tapen` and `src/ptouch_py`. Keep public interfaces typed, especially hardware and renderer boundaries.
- Preserve the GPL copyright header in Python files. `make copyright` and the pre-commit hook apply `development/copyright.tmpl`.
- Keep YAML within the 120-character limit and compatible with `.yamllint.yaml`.
- Run `make check-format`, `make ruff-lint`, and `make mypy` for focused verification, or `make lint` before completing a code change.
- Pre-commit also checks debug statements, executable shebangs, merge conflicts, end-of-file newlines, YAML, and the uv lockfile.
- Avoid unrelated formatting or generated-file changes in a feature commit.

The project uses modern Python syntax such as union types and built-in generic types. Keep compatibility with the declared Python range, and remember that the Ruff and MyPy configuration uses Python 3.11 as its language baseline.

## Application Architecture

### CLI and orchestration

`src/tapen/cli.py` defines the `tapen` and legacy `tpp` entrypoints from `pyproject.toml`. CLI functionality is organized as `cli_rack` extensions:

- `import-lib` registers a local or remote template library in the user configuration.
- `printers add|list` manages configured printers and reports USB discovery.
- `status` initializes a selected printer and reads its status.
- `print` resolves a template, renders each data item, and optionally sends copies to the device.

Shared CLI extensions load configuration, create the renderer and printer factory, and lazily fetch template libraries. Preserve this lifecycle when adding commands. Use `tapen.const` keys rather than duplicating configuration strings.

### Configuration and libraries

Configuration is YAML validated through `cli_rack_validation` in `config.py` and `validate.py`. The file is `conf.yaml` in the current directory when present, otherwise under the platform-specific `appdirs` user config directory. Writing configuration normalizes the default printer to a valid configured printer and selects the first printer when no default exists.

Template libraries contain a `manifest.yaml` with `template`, `params`, and `layout` sections. The layout requires a Jinja template string and may include CSS. Locators use a prefix/body form such as `local:/path` or `github://owner/repository`; template locators are resolved through the cloned `cli_rack` loader registry. The built-in library is always registered as `std` and must not be persisted in user configuration.

When changing manifests or validation, update both the schema and representative examples. Keep user-controlled template processing and configuration parsing behavior explicit; do not bypass the existing validation layer.

### Rendering

`renderer/processor.py` renders Jinja templates. `renderer/weasyprint.py` converts the resulting HTML/CSS to PDF/PNG through WeasyPrint and PyMuPDF, then converts the image to a monochrome Pillow bitmap for printing. Rendering context exposes `params`, `param`, `tape`, and `is_preview`.

Keep renderer resource paths package-relative and ensure new resources are included in uv packaging and `tapen.spec`. The renderer has process-wide singleton factories in `renderer/__init__.py`; avoid adding hidden global state without a concrete need.

### Printers and protocol

`printer/common.py` defines the application-facing interfaces (`TapenPrinter`, `PrinterFactory`, `TapeInfo`, and `PrinterStatus`). `printer/brother.py` adapts those interfaces to `ptouch_py` and persists detected tape metadata under the platform-specific cache directory.

`ptouch_py` owns device protocol details. `Transport` abstracts byte I/O, with `_USBTransport` using PyUSB and `_TCPTransport` using raw TCP port 9100. `Printer.init()` must run before status or raster commands. Network status is read from the Brother embedded page at `/general/status.html`, while USB status uses the P-touch status endpoint.

When changing hardware behavior:

- Keep transport-independent protocol code in `ptouch_py/core.py`.
- Add device IDs and capabilities to `ptouch_py/registry.py` rather than hard-coding them in discovery.
- Preserve the initialization, raster framing, tape-size, and cut/advance semantics.
- Test with mocks or a fake `Transport` where possible; do not require a physical printer for pure protocol tests.
- Treat USB discovery, network connections, and printer commands as side effects that require explicit handling and useful errors.

## Packaging and Release

uv packages both `ptouch_py` and `tapen` from `src/` through Hatchling, exposes `tapen` and `tpp` console scripts, and includes built-in resources plus the license and README. Keep `uv.lock` synchronized with dependency changes; use `make deps-lock` or `make deps-update` rather than editing the lock file manually.

The release version is declared in PEP 621 metadata and mirrored in `src/tapen/__version__.py`. Commitizen uses the PEP 621 provider and updates the version file and changelog. Release/publish commands can modify version files and upload artifacts; inspect `dist/` and the resulting diff before publishing.

The PyInstaller build uses `tapen.spec`, which explicitly includes renderer resources and hidden `poppler.cpp.*` imports needed by the rendering stack. Update the spec when packaging introduces new non-Python resources or hidden imports.

## Change Workflow

1. Read the relevant interface and its adapter before changing behavior. Keep changes within the owning layer.
2. Update schemas, manifests, registries, packaging data, or the PyInstaller spec when the change crosses those boundaries.
3. Run focused checks while iterating, then run `make lint`.
4. For packaging or build-toolchain changes, run `make build` and inspect generated changes; use `make single-binary` when the executable path is affected.
5. Exercise CLI parsing and `--skip-printing` paths for CLI changes. Use mocked transports for protocol changes and a real printer only for hardware integration validation.
6. Do not commit generated `build/`, `dist/`, cache, virtual-environment, or local configuration files.
