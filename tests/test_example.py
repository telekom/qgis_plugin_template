# -*- coding: utf-8 -*-
# SPDX-FileCopyrightText: 2025 Deutsche Telekom Technik GmbH <f.vonstudsinske@telekom.de>
# SPDX-License-Identifier: GPL-3.0-only

from ..submodules.base.tests.markers import skipif_no_python_exe, skipif_no_qgis_app


@skipif_no_python_exe
def test_python_exe(qgis_app):
    print("run only in opened QGIS Python interpreter")


@skipif_no_qgis_app
def test_python_exe():
    print("run only in the opened QGIS Desktop Application")


def test_always():
    """ run this test always """


