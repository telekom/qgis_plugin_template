# -*- coding: utf-8 -*-
# SPDX-FileCopyrightText: 2025 Deutsche Telekom Technik GmbH <f.vonstudsinske@telekom.de>
# SPDX-License-Identifier: GPL-3.0-only

from ..plugin import PluginTemplate


def load_tool_bar(plugin: PluginTemplate):
    """ loads default action for your plugin """
    pass


def init_plugin(plugin: PluginTemplate):
    """ Loads/calls some function in plugins class __init__-method.
        Maybe no ui is active from qgis (e.g. start process).

        WARNING: Do not setup UI elements or interact with them here! Use `load_tool_bar` instead.
    """
    pass


def init_plugin_gui(plugin: PluginTemplate):
    """ Run code, when the QGIS ui is guaranteed available. """
    pass
