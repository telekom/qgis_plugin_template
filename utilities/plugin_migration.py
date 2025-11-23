# -*- coding: utf-8 -*-
# SPDX-FileCopyrightText: 2025 Deutsche Telekom Technik GmbH <f.vonstudsinske@telekom.de>
# SPDX-License-Identifier: GPL-3.0-only

from pkg_resources import packaging


def migrate(plugin, current_version: packaging.version.Version, saved_template_version: packaging.version.Version):
    """ Handles necessary migrations of plugin template stuff.
        For e.g., changed profile variables.

        Be careful with changes!

        :param plugin: Plugin object from plugin.py
        :current_version: Current version set in plugin.py
        :saved_template_version: Latest saved version number in profile settings
    """

    if saved_template_version is None:

        return

    # add further updates, if necessary
