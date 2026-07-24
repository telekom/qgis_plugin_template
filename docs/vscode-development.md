<!--
SPDX-FileCopyrightText: 2026 Deutsche Telekom Technik GmbH
SPDX-License-Identifier: CC-BY-4.0
-->

# QGIS Python development in VS Code

## One-time setup

Requirements:

- QGIS installed through the Windows standalone installer or OSGeo4W
- Git Bash
- the VS Code extensions recommended by this workspace

From Git Bash in the plugin root, run:

```bash
bash scripts/setup-qgis-dev.sh
```

Without an argument, the script uses `QGIS_ROOT` when it is set; otherwise, it
finds the newest installation below `C:\Program Files\QGIS*`. To use a
particular standalone or OSGeo4W installation, pass its root directory
explicitly:

```bash
bash scripts/setup-qgis-dev.sh 'C:\Program Files\QGIS 3.40.7'
```

An explicit argument takes precedence over `QGIS_ROOT`. Run the script from Git
Bash, not WSL, because it creates and invokes Windows executables.

Then reload the VS Code window. The shared workspace settings select
`.venv\Scripts\python.exe`. If VS Code has cached a previously selected
interpreter, run **Python: Select Interpreter** once and choose that file.

The setup script also initializes the repository's Git submodules. Empty
submodule directories contain no Python source, so neither Python nor an IDE can
resolve imports from them.

It installs the pinned development packages from `requirements-dev.txt` into
the local environment. This guarantees that pytest, QGIS stubs, and PyQt5 stubs
are available even when the QGIS installation does not include them. The stub
packages provide completion, type information, and navigation for the native
QGIS and Qt APIs.

The script may be rerun after a QGIS upgrade. Its generated files (`.venv` and
`.env`) are machine-local and ignored. The VS Code settings and setup script are
shared by the repository.

## Why the batch file is not selected as the interpreter

`python-qgis-ltr.bat` is an environment launcher, not a Python executable. VS
Code's Python extension, Pylance, test discovery, formatters, and debuggers need
a real `python.exe` and start it directly in subprocesses.

Starting all of VS Code through the QGIS batch file is also unsafe. The batch
file sets `PYTHONHOME` and replaces much of `PATH`; those process-wide values are
inherited by unrelated Python tools and can prevent linters or virtual
environments from starting.

The setup uses QGIS's real executable under `apps\Python3*\python.exe` to create
a project-local virtual environment that can access QGIS's bundled packages. A
`.pth` file adds `apps\qgis-ltr\python` (or `apps\qgis\python`). On Windows, the
`qgis` package then reads QGIS's own environment file and registers the native
DLL directories when it is imported. This gives VS Code a normal interpreter
without applying QGIS's process-wide environment to VS Code itself.

A virtual environment made with a separately installed Python is not compatible
with the native QGIS bindings unless its Python major/minor version and ABI match
QGIS exactly. The setup script avoids that mismatch.

## Linting and formatting

- Pylance uses the QGIS-derived `.venv` for imports and type analysis.
- Pylance is selected explicitly because the optional ty extension otherwise
  changes VS Code's default Python language server to `None`.
- The plugin directory's parent is added as an analysis import root so files in
  the QGIS plugin package retain their relative-import context.
- Ruff runs as its own native language server, so linting and PEP 8 checks do not
  depend on launching QGIS Python.
- Ruff is the default formatter with a line length of 120.
- If the Pylint extension is installed, its workspace configuration uses the
  same interpreter and suppresses false `no-name-in-module` reports for members
  exported dynamically by QGIS's SIP-generated modules.
- ty is disabled for this workspace because it currently reports false import
  and member errors for the plugin package and QGIS compatibility modules.

VS Code discovers pytest tests from the parent QGIS plugins directory so the
plugin keeps its package context and relative imports work. The FPF integration
suite is excluded from default discovery because it requires private credentials
and external test workspaces.

The generated `.env` records the selected QGIS installation and environment
name and disables user-site packages so undeclared personal installations cannot
hide missing dependencies. It does not set `PYTHONHOME`; the setup script also
removes an inherited `PYTHONHOME` before invoking Python.

## Troubleshooting

- If `qgis` cannot be imported, rerun the setup script with the exact QGIS
  installation directory and reload VS Code.
- If QGIS was upgraded in place and imports fail, delete `.venv` and rerun the
  script.
- If Ruff is missing, accept the workspace's recommended extensions.
- If QGIS or Qt completion is missing, accept the Pylance recommendation and run
  **Developer: Reload Window** after rerunning the setup script.
- Do not add QGIS directories globally to the user or system `PATH`,
  `PYTHONPATH`, or `PYTHONHOME`.