# -*- coding: utf-8 -*-
# SPDX-FileCopyrightText: 2025 Deutsche Telekom Technik GmbH <f.vonstudsinske@telekom.de>
# SPDX-License-Identifier: GPL-3.0-only
""" Example pytest cases for plugin development. """

import os

import pytest

from ..submodules.base.tests.markers import skipif_no_python_exe, skipif_no_qgis_app


@skipif_no_python_exe
def test_python_exe(qgis_app):
    print("run only in opened QGIS Python interpreter")


@skipif_no_qgis_app
def test_python_exe():
    print("run only in the opened QGIS Desktop Application")


def test_always():
    """ run this test always """


@pytest.mark.skipif(
    "PLUGIN_PYTEST_GUI_EXAMPLE" not in os.environ,
    reason="PLUGIN_PYTEST_GUI_EXAMPLE is not set by the selected env file")
def test_pytest_environment_variable_from_env_file():
    """ Run only when the example environment variable is set by the GUI. """
    assert os.environ["PLUGIN_PYTEST_GUI_EXAMPLE"]
