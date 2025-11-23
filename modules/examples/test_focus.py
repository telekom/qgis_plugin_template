# -*- coding: utf-8 -*-
# SPDX-FileCopyrightText: 2025 Deutsche Telekom Technik GmbH <f.vonstudsinske@telekom.de>
# SPDX-License-Identifier: GPL-3.0-only

from qgis.PyQt.QtWidgets import QMainWindow

from ...submodules.base.ui.base_class import UiModuleBase

FORM_CLASS, _ = UiModuleBase.get_uic_classes(__file__)

class TestFocus(UiModuleBase, QMainWindow, FORM_CLASS):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        QMainWindow.__init__(self, kwargs.get("parent"))
        self.setupUi(self)
