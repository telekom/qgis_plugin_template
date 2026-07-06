# -*- coding: utf-8 -*-
# SPDX-FileCopyrightText: 2025 Deutsche Telekom Technik GmbH <f.vonstudsinske@telekom.de>
# SPDX-License-Identifier: GPL-3.0-only

import sys
import inspect
import importlib
from pathlib import Path
from typing import Optional

from qgis.PyQt.QtWidgets import QFrame, QFileDialog
from qgis.PyQt.QtGui import QIcon

from ...submodules.base.ui.base_class import UiModuleBase

FORM_CLASS, _ = UiModuleBase.get_uic_classes(__file__)


class ClassNotFoundException(Exception):
    """ Raised when no suitable class is found in the loaded .py file. """
    ...


class UIQuickCheck(UiModuleBase, QFrame, FORM_CLASS):
    """ A simple UI to test loading of .py files containing classes inheriting from UiModuleBase.
    """

    def __init__(self, **kwargs: dict):
        super().__init__(**kwargs)
        QFrame.__init__(self, kwargs.get("parent"))

        self.setupUi(self)

        self.is_loaded: bool = False
        self._last_directory: Optional[str] = None
        self._last_file_path: Optional[str] = None

        self.connect(self.Btn_Load_UI.clicked, lambda *_: self.__load_to_ui())
        self.connect(self.Btn_Reload_UI.clicked, lambda *_: self.__reload_ui())
        self.connect(self.Btn_Unload_UI.clicked, lambda *_: self.__unload_ui())

        self.Btn_Load_UI.setIcon(QIcon(self.getThemeIcon("mActionFileOpen.svg")))
        self.Btn_Reload_UI.setIcon(QIcon(self.getThemeIcon("mActionReload.svg")))
        self.Btn_Unload_UI.setIcon(QIcon(self.getThemeIcon("mIconClose.svg")))

    def __load_to_ui(self):
        """ Load a .py file containing a class inheriting from UiModuleBase and display it either as a popup or in the replacement frame.
            The file must be located inside the plugin directory and use relative imports if needed.
        """

        if self.is_loaded:
            self.is_loaded = False
            mod = self._modules.get("LoadedModule")
            if not mod:
                return
            mod.unload(self_unload=True)
            self.replace_widget_with_widget(self.Frame_Replacement_Element, QFrame(self))
            return

        directory = self._last_directory or self.get_plugin().plugin_dir
        file_path, _ = QFileDialog.getOpenFileName(self, None,
                                                   directory=directory,
                                                   filter="Python Files (*.py)")
        if not file_path or not Path(file_path).exists():
            return
        self._last_directory = str(Path(file_path).parent)
        self._last_file_path = file_path

        try:
            found_class = self.__get_class_from_file(file_path)
        except ClassNotFoundException as e:
            self.critical("Load UI", str(e))
            return

        if self.Radio_Popup.isChecked():
            module = self.add_module("LoadedModule",
                                     found_class,
                                     parent=self.iface.mainWindow())
            module.show()
        elif self.Radio_Replacement.isChecked():
            try:
                self.add_ui_module("LoadedModule", self.Frame_Replacement_Element, found_class)
                self.is_loaded = True
            except AttributeError as e:
                self.__cleanup_failed_loaded_module()
                self.is_loaded = False
                self.critical("Load UI", f"Modul kann nicht als Replacement-Modul geladen werden. "
                              f"Siehe Fehlertext: {e}")
        else:
            return

    def __reload_ui(self):
        """ Reload the previously loaded UI from disk without prompting for a file.
            For popup mode, opens a new popup from the last file.
            For replacement mode, unloads the current widget and replaces it with a fresh instance.
        """
        if not self._last_file_path or not Path(self._last_file_path).exists():
            return

        if self.Radio_Replacement.isChecked():
            try:
                found_class = self.__get_class_from_file(self._last_file_path)
            except ClassNotFoundException as e:
                self.critical("Load UI", str(e))
                return
            previous_module = self._modules.pop("LoadedModule", None)
            try:
                self.add_ui_module("LoadedModule", self.Frame_Replacement_Element, found_class)
            except AttributeError as e:
                self.__cleanup_failed_loaded_module(previous_module)
                self.is_loaded = previous_module is not None
                self.critical("Load UI", f"Modul kann nicht als Replacement-Modul geladen werden. "
                              f"Siehe Fehlertext: {e}")
                return

            if previous_module:
                previous_module.unload(self_unload=False)
            self.is_loaded = True
        elif self.Radio_Popup.isChecked():
            try:
                found_class = self.__get_class_from_file(self._last_file_path)
            except ClassNotFoundException as e:
                self.critical("Load UI", str(e))
                return
            module = self.add_module("LoadedModule",
                                     found_class,
                                     parent=self.iface.mainWindow())
            module.show()

    def __unload_ui(self):
        """ Unload the currently loaded UI module and reset the replacement frame to its default state.
            For replacement mode, the widget is removed and replaced with an empty QFrame.
            For popup mode, the module is unloaded without any frame manipulation.
        """
        mod = self._modules.get("LoadedModule")
        if self.Radio_Replacement.isChecked():
            if mod:
                mod.unload(self_unload=True)
            self.replace_widget_with_widget(self.Frame_Replacement_Element, QFrame(self))
            self.is_loaded = False
        elif self.Radio_Popup.isChecked():
            if mod:
                mod.unload(self_unload=True)
            self.is_loaded = False

    def __cleanup_failed_loaded_module(self, previous_module=None):
        """ Remove a partially registered replacement module after a failed load. """
        failed_module = self._modules.pop("LoadedModule", None)
        if failed_module is not None and failed_module is not previous_module:
            failed_module.unload(self_unload=False)
        if previous_module is not None:
            self._modules["LoadedModule"] = previous_module

    def __get_class_from_file(self, file_path: str):
        """ try to load the file as a module and find a class inheriting from UiModuleBase.
            The file must be located inside the plugin directory and use relative imports if needed.

            :param file_path: path to the .py file to load
            :return: the first class found in the file that inherits from UiModuleBase
            :raises ClassNotFoundException: if the file is not inside the plugin directory or no
                suitable class is found
        """
        plugin_dir = Path(self.get_plugin().plugin_dir).resolve()
        file_path_resolved = Path(file_path).resolve()

        # Only files inside the plugin directory can be loaded with their proper
        # package context. Relative imports (`from ...submodules...`) require the
        # module to be imported under its full dotted package name.
        try:
            rel_path = file_path_resolved.relative_to(plugin_dir)
        except ValueError as e:
            raise ClassNotFoundException(
                f"File '{file_path}' is not located inside the plugin directory "
                f"'{plugin_dir}'. Modules with relative imports must live inside "
                f"the plugin package."
            ) from e

        # Build the full dotted module name, e.g.
        #   plangoo_v2.modules.dev_tools.ui_quick_check
        plugin_package = plugin_dir.name
        parts = list(rel_path.with_suffix("").parts)
        if parts and parts[-1] == "__init__":
            parts = parts[:-1]
        full_module_name = ".".join([plugin_package, *parts])

        # Remove any cached version so the file is re-read from disk on every
        # load.  This is intentional: the whole point of this dev tool is to
        # reflect live changes (including recompiled .ui files) without
        # restarting QGIS.
        sys.modules.pop(full_module_name, None)

        # Import through the regular machinery so the module's __package__ is
        # set correctly and relative imports resolve.
        module = importlib.import_module(full_module_name)

        classes = [
            obj
            for name, obj in inspect.getmembers(module, inspect.isclass)
            if obj.__module__ == module.__name__
            and issubclass(obj, UiModuleBase)
            and obj is not UiModuleBase
        ]

        if not classes:
            raise ClassNotFoundException(
                f"No class inheriting from {UiModuleBase.__name__} found in {file_path}"
            )

        return classes[0]
