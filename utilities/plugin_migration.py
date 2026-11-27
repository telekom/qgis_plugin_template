# -*- coding: utf-8 -*-
# SPDX-FileCopyrightText: 2025 Deutsche Telekom Technik GmbH <f.vonstudsinske@telekom.de>
# SPDX-License-Identifier: GPL-3.0-only
""" Migrate template settings stored in the user's profile. """

from typing import Any

from ..submodules.base.version import Version


def migrate(plugin: Any, current_version: Version, saved_template_version: Version | None) -> None:
    """ Handle necessary migrations of plugin template settings in the user profile.

        :param plugin: plugin object from plugin.py
        :param current_version: current template version
        :param saved_template_version: latest saved template version, or None
    """

    if saved_template_version is None:

        return

    # add further updates, if necessary
