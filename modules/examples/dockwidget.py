# -*- coding: utf-8 -*-
# SPDX-FileCopyrightText: 2025 Deutsche Telekom Technik GmbH <f.vonstudsinske@telekom.de>
# SPDX-License-Identifier: GPL-3.0-only

from qgis.core import QgsApplication
from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QMainWindow, QPushButton

from .show_modules import TestShowModules
from .dynamic_module_list import TestModuleDynamicModules

from ...submodules.base.ui.base_dockwidget import DockWidgetModuleBase
from ...submodules.base.ui.base_tab_widget import TabModuleBase
from ...submodules.base.ui.base_class import ModuleBase
from ...submodules.base.ui.base_plugin import Plugin

KEY = "TestDockWidget"


def init(plugin: ModuleBase):
    """ creates test icon for dock widget """

    plugin: Plugin = plugin.get_plugin()
    icon = QIcon(plugin.get_icon_path("icon.svg"))
    plugin.add_action(f"{KEY} öffnen",
                      icon,
                      lambda x=None, p=plugin: show(p),
                      toolbar_name=plugin.plugin_menu_name,
                      toolbar_displayname=plugin.plugin_menu_name)

    icon = plugin.getThemeIcon("mLayoutItemPicture.svg")
    plugin.add_action(f"QgsApplication.getThemePixmap",
                      icon,
                      lambda x=None: show_icon(),
                      toolbar_name=plugin.plugin_menu_name,
                      toolbar_displayname=plugin.plugin_menu_name)


def show_icon():
    from .qgis_theme_icons import QgisDefaultThemeTable
    from qgis.utils import iface

    w = QgisDefaultThemeTable(iface.mainWindow() if iface else None)
    w.show()


def show(plugin: ModuleBase):
    """ opens dock widget """

    if KEY in plugin:
        plugin[KEY].show()
    else:
        module = plugin.add_module(KEY, TestDockWidget)
        window: QMainWindow = plugin.iface.mainWindow()
        window.addDockWidget(Qt.RightDockWidgetArea, module)


def activity_condition(plugin, key, module_to_compare) -> bool:
    # continue singleShot loop
    if key not in plugin:
        # key no more in plugin's modules
        return False

    module = plugin[key]
    if module is not module_to_compare:
        # object changed
        return False

    return module_to_compare.isVisible()


def activity_condition_stop(plugin, key, module_to_compare) -> bool:
    # callback to cancel daily singleShot calls
    if key not in plugin:
        # key no more in plugin's modules
        return True

    module = plugin[key]
    if module is not module_to_compare:
        # object changed
        return True

    return False


class TestDockWidget(DockWidgetModuleBase):

    def __init__(self, *args, **kwargs):
        DockWidgetModuleBase.__init__(self, *args, **kwargs)

        self.setWindowTitle("Hamster Laufrad")

        self.frame = self.load_empty_frame('frame')
        module: TabModuleBase = self.add_ui_module("Tab", self.frame,
                                                   TabModuleBase, use_directly=True)

        module.insert_module_tab(0, "Test 0", "tab_object_0")
        index_1, frame_1 = module.insert_module_tab(1, "Test 1", "tab_object_1")
        index_2, frame_2 = module.insert_module_tab(2, "TestModuleDynamicModules", "tab_TestModuleDynamicModules")
        self.add_ui_module('TestShowModules', frame_1, TestShowModules)
        self.add_ui_module('TestModuleDynamicModules', frame_2, TestModuleDynamicModules)

        self.btn0 = QPushButton()
        self.connect(self.btn0.clicked, self.unload_test_tab_module)
        self.btn0.setText(f"unload {module.__class__.__name__}")
        self.widget().layout().addWidget(self.btn0)

        self.btn1 = QPushButton()
        self.connect(self.btn1.clicked, self.replace_test_tab_module)
        self.btn1.setText(f"replace with dummy {module.__class__.__name__}")
        self.widget().layout().addWidget(self.btn1)

        # Test Barrierefreiheit
        from .test_focus import TestFocus
        index_3, frame_3 = module.insert_module_tab(3, "Barrierefreiheit", "tab_object_3")
        self.add_ui_module('TestFocus', frame_3, TestFocus)

        # some default post checks
        self.post_checks()

    def unload_test_tab_module(self, checked: bool):
        module = self._get_module(self.frame)
        module.unload(True)
        self.btn0.setEnabled(False)
        self.btn0.setText("ist ja bereits weg")

        self.btn1.setEnabled(False)
        self.btn1.setText("jetzt mag ich nicht mehr")

    def replace_test_tab_module(self, checked: bool):
        module = self._get_module(self.frame)
        module.replace_with_empty_frame()
        self.btn0.setEnabled(False)
        self.btn0.setText("ist ja bereits weg")

        self.btn1.setEnabled(False)
        self.btn1.setText("jetzt mag ich nicht mehr")
