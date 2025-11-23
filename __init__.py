# -*- coding: utf-8 -*-
# SPDX-FileCopyrightText: 2025 Deutsche Telekom Technik GmbH <f.vonstudsinske@telekom.de>
# SPDX-License-Identifier: GPL-3.0-only

import sys
import os

from qgis.gui import QgisInterface
from typing import Type

# Edit this import and references in this file to new name
from .plugin import PluginTemplate


def get_class() -> Type[PluginTemplate]:
    """ returns plugin class """

    return PluginTemplate


# noinspection PyPep8Naming
def classFactory(iface: QgisInterface, **kwargs: dict) -> PluginTemplate:  # pylint: disable=invalid-name
    """Loads this plugin an loads it. Automatically called by QGIS

    :param iface: A QGIS interface instance.
    """

    if sys.executable.endswith(('qgis-ltr-bin.exe', 'qgis-ltr-dev-bin.exe')):
        # disables pytest auto load of plugins only if the current main executable is QGIS (with GUI)
        # https://docs.pytest.org/en/7.1.x/reference/reference.html#envvar-PYTEST_DISABLE_PLUGIN_AUTOLOAD
        # this is possible necessary when using pytest from the QGIS App in the frontend
        os.environ['PYTEST_DISABLE_PLUGIN_AUTOLOAD'] = "just set this variable"

    return get_class()(iface, **kwargs)
