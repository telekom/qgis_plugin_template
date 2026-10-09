# -*- coding: utf-8 -*-
# SPDX-FileCopyrightText: 2026 Deutsche Telekom Technik GmbH <f.vonstudsinske@telekom.de>
# SPDX-License-Identifier: GPL-3.0-only
"""Check that every plugin Python module can be imported in a QGIS environment."""

import os
from importlib import import_module
from pathlib import Path

import pytest

from ..submodules.base.tests.functions import new_qgis_project


PLUGIN_ROOT = Path(__file__).resolve().parents[1]
PLUGIN_PACKAGE = __package__.rsplit(".", 1)[0]
EXCLUDED_DIRECTORIES = {"__pycache__", "venv", "env", "build", "dist", ".git"}
# These manual scripts modify projects/network settings and export files at import time.
EXCLUDED_FILES = {
    "submodules/base/tests/test_plot/script_test_export_existing_layout.py",
    "submodules/base/tests/test_plot/script_test_wms_legend_filter_map_enabled.py",
}


def get_module_files() -> tuple[Path, ...]:
    """Discover source files without importing packages or scanning virtual environments."""
    module_files = []
    for directory, subdirectories, filenames in os.walk(PLUGIN_ROOT):
        subdirectories[:] = sorted(
            name for name in subdirectories
            if not name.startswith(".") and name not in EXCLUDED_DIRECTORIES
        )
        for filename in filenames:
            if not filename.endswith(".py"):
                continue
            path = Path(directory) / filename
            if path.relative_to(PLUGIN_ROOT).as_posix() not in EXCLUDED_FILES:
                module_files.append(path)
    return tuple(sorted(module_files))


MODULE_FILES = get_module_files()


@pytest.fixture(scope="module")
def module_import_qgis_environment():
    """Initialize QGIS and Processing before importing UI and QGIS-dependent modules."""
    yield from new_qgis_project()


@pytest.mark.usefixtures("module_import_qgis_environment")
@pytest.mark.parametrize("module_file", MODULE_FILES, ids=lambda path: path.relative_to(PLUGIN_ROOT).as_posix())
def test_module_can_be_imported(module_file: Path):
    """Let syntax errors, missing dependencies and other import exceptions fail the test."""
    relative_path = module_file.relative_to(PLUGIN_ROOT).with_suffix("")
    parts = relative_path.parts
    if parts[-1] == "__init__":
        parts = parts[:-1]
    module_name = ".".join((PLUGIN_PACKAGE, *parts))
    import_module(module_name)
