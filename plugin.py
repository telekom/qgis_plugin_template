# -*- coding: utf-8 -*-
# SPDX-FileCopyrightText: 2025 Deutsche Telekom Technik GmbH <f.vonstudsinske@telekom.de>
# SPDX-License-Identifier: GPL-3.0-only

import os.path
import os
import shutil
import configparser

import time
from datetime import datetime

from pathlib import Path
from pkg_resources import packaging

from qgis.core import QgsApplication
from qgis.gui import QgisInterface

from qgis.PyQt.QtWidgets import QApplication, QAction
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtCore import pyqtSignal

from .test import run_pytest_from_ui

from .submodules.base import constants
from .submodules.base.versions_reader import VersionPlugin
from .submodules.base.functions import qgis_unload_keyerror, get_files

from .submodules.base.ui.base_class import ModuleBase
from .submodules.base.ui.base_plugin import Plugin
from .submodules.base.ui.confirmation_dialog import ConfirmationDialog


TEMPLATE_VERSION = "1.2"

LOG_LIFETIME = 7.0  # older log_files will be removed (in Days)


class PluginTemplate(Plugin):
    """ Main class for this plugin.

        Attachments when contacting support are stored in:
        * Path to qgis profile/_temp_files/plugin name.
        * This folder will be cleared on startup and end.

        . Qt Signals:

            * pluginReloaded: add your callables to trigger, when user triggered manual reloading

        :param iface: qgis interface (QMainWindow, layer handling, etc.)
        :param kwargs: dictionary with keyword arguments, if empty -> then QGIS handle this plugin, else an other
                       ModuleBase loads this
    """
    pluginUnloaded = pyqtSignal(name="pluginUnloaded")
    pluginReloaded = pyqtSignal(name="pluginReloaded")
    versionRead = pyqtSignal(ModuleBase, name="versionRead")
    feedbackClicked = pyqtSignal(ModuleBase, name="feedbackClicked")

    def __init__(self, iface: QgisInterface, *args, **kwargs: dict):

        self._iface: QgisInterface = iface

        # Plugin files/folders variables
        self.plugin_dir = os.path.normpath(os.path.normcase(os.path.dirname(__file__)))
        self.plugin_import_name = os.path.basename(self.plugin_dir)
        self.meta_file = os.path.join(self.plugin_dir, 'metadata.txt')
        self.icons_dir = os.path.join(self.plugin_dir, 'templates', 'icons')
        self.plugin_version = VersionPlugin.get_local_version(self.meta_file)
        self.plugin_name = VersionPlugin.get_meta_value(self.meta_file, "name")
        self.plugin_menu_name = VersionPlugin.get_meta_value(self.meta_file, "name_menu_bar")
        self.homepage_url = VersionPlugin.get_meta_value(self.meta_file, "homepage")
        # similar to `Qgis.versionInt()`
        self.minimum_qgis_version = packaging.version.parse(
            VersionPlugin.get_meta_value(self.meta_file, "qgisMinimumVersion"))
        self.maximum_qgis_version = packaging.version.parse(
            VersionPlugin.get_meta_value(self.meta_file, "qgisMaximumVersion"))

        # logging settings
        log_day = time.strftime("%Y_%m_%d", time.localtime())
        friendly_version = str(self.plugin_version).replace('.', '_')
        plugin_folder_version = f"{self.plugin_name}_{friendly_version}"
        self.log_filename = f"{log_day}-{plugin_folder_version}.jsonl"
        self.log_dir = os.path.join(QgsApplication.qgisSettingsDirPath(), '_logs')
        self.log_file_path = os.path.join(self.log_dir, plugin_folder_version, self.log_filename)
        self.temp_files = os.path.join(QgsApplication.qgisSettingsDirPath(), '_temp_files', self.log_filename)
        self.logging_level_debug = self.is_logging_debug_active()
        # developer settings
        self.force_dev_mode = VersionPlugin.get_meta_value(self.meta_file, "force_dev_mode").lower() == "true"

        # accessibility settings
        self.accessibility_config_path = os.path.join(self.plugin_dir, "accessibility_mode.ini")
        self._accessibility_config = configparser.ConfigParser()

        self.email = VersionPlugin.get_meta_value(self.meta_file, "emailBugs")

        self.repo_xml_path = VersionPlugin.get_local_xml_url(self.meta_file)
        self.zip_file_name = VersionPlugin.get_local_zipname(self.meta_file)
        self.repo_version = None
        self.repo_version_error = None
        self.repo_commit = None
        self.repo_version_data = None

        try:
            # get latest git commit from metadata.txt
            self.commit = VersionPlugin.get_meta_value(self.meta_file, "commit")
        except KeyError:
            self.commit = None

        super().__init__(*args,
                         name=self.plugin_name,
                         logging_file_path=self.log_file_path,
                         logging_level_debug=self.logging_level_debug,
                         **kwargs)

        self.connect(self.pluginUnloaded, self.reloaded)

        if self.is_qgis_plugin():
            self.connect(QgsApplication.messageLog().messageReceived, self.qgis_message_received_python_error)
            self.connect(self.iface.mapCanvas().mapToolSet, self.check_map_tool_changed)

        self.__load_plugin_template_version()
        self.load_version_info()
        self.clear_log_files()
        self.clear_temp_files()

        # call init function for seperate init routines
        from .utilities import ui_control
        ui_control.init_plugin(self)

        # finish loading with a log message
        self.log(f"{self.plugin_name} version {self.plugin_version} loaded.",
                 level=self.INFO,
                 extra={'is_dev_mode': self.is_dev_mode()})

    def is_logging_debug_active(self) -> bool:
        return (Path(self.plugin_dir) / "logging_level_debug.debug").is_file()

    def is_accessibility_mode_active(self) -> bool:
        """ Checks if accessibility mode is active by reading the config file
        """
        self._accessibility_config.read(self.accessibility_config_path)
        return self._accessibility_config.getboolean('accessibility', 'enable', fallback=False)

    def __load_plugin_template_version(self):
        """ Loads plugin template version to the user's profile.
            Calls possible migration method for further migrations due to template changes.
            E.g. changes in the user profile settings.
        """
        current_version = packaging.version.parse(TEMPLATE_VERSION)

        # get latest saved template version in user's profile settings
        saved_template_version = self.get_option("PluginTemplateVersion")
        if saved_template_version is not None:
            try:
                saved_template_version = packaging.version.parse(saved_template_version)
            except:
                saved_template_version = None

        if saved_template_version is None or current_version > saved_template_version:
            # nothing saved yet or new version to set
            from .utilities.plugin_migration import migrate
            migrate(self, current_version, saved_template_version)

        # update it
        self.set_option("PluginTemplateVersion", TEMPLATE_VERSION)

    def load_version_info(self):

        # set default values
        self.repo_version = "-1"
        self.repo_commit = None
        self.repo_version_data = None
        self.repo_version_error = "no repository url defined in metadata.txt"

        if self.repo_xml_path:
            self.repo_version_data = VersionPlugin.get_repository_version_zipname(
                self.repo_xml_path, self.zip_file_name)

            if isinstance(self.repo_version_data, constants.VersionInfo):
                # valid version found
                self.repo_version = self.repo_version_data.version
                self.repo_commit = self.repo_version_data.commit
            else:
                # error occurred
                self.repo_version_error = self.repo_version_data.error

        self.versionRead.emit(self)

    def load_frame_picker(self):
        """ Load the developer frame picker into the existing plugin UI. """
        from .modules.dev.frame_quick_reload import FramePicker

        if "FramePicker" not in self:
            picker = self.add_module("FramePicker", FramePicker)
        else:
            picker = self["FramePicker"]

        action = self.add_action(
            f"Frame neu laden (Picker)",
            self.getThemeIcon("cursors/mSelect.svg"),
            None,  # connected manually below to receive the checked state
            toolbar_name=self.plugin_menu_name,
            toolbar_displayname=self.plugin_menu_name)
        action.setCheckable(True)
        action.setStatusTip("Einen Frame anklicken, um dessen Modul "
                            "neu zu laden (ohne Plugin-Neustart).\n"
                            "Mausrad: Eltern-Frame · Esc/Rechtsklick: Abbrechen.")
        action.setToolTip(action.statusTip())
        picker.set_action(action)
        self.connect(
            action.triggered,
            lambda checked: picker.start() if checked else picker.cancel())

    def check_map_tool_changed(self, new_tool, old_tool):
        for drawing in self.drawings:
            if drawing:
                self.iface.mapCanvas().scene().removeItem(drawing)

        self.drawings.clear()

    def get_temp_folder(self):
        path = os.path.join(self.temp_files,
                            datetime.now().strftime("_%Y-%m-%d_%H-%M-%S_%f"))
        if not os.path.exists(path):
            os.makedirs(path)

        return path

    def clear_temp_files(self):
        """ cleanup all temp files. Nothing happens on blocking process """
        try:
            shutil.rmtree(self.temp_files)
        except OSError:
            ...

    def clear_log_files(self):
        """ remove all log file older than X days """
        files = get_files(self.log_dir)
        for file in files:
            time_file = os.path.getmtime(file)
            time_diff = (time.time() - time_file) / 86400  # 24 Stunden
            if time_diff > LOG_LIFETIME:
                try:
                    os.remove(file)
                except PermissionError:
                    # still in use by another programm/plugin
                    continue

            parent = Path(file).parent
            if not parent.is_dir():
                continue

            if not list(parent.iterdir()):
                parent.rmdir()

        # remove parent dirs without content
        for path in Path(self.log_dir).iterdir():
            if not path.is_dir():
                continue

            if not list(path.iterdir()):
                path.rmdir()

    def is_module(self) -> bool:
        """ is this a module loaded by another module? """
        path = Path(QgsApplication.qgisSettingsDirPath()) / 'python' / 'plugins'
        path = path / Path(self.plugin_dir).name / Path(__file__).name

        return not (path == Path(__file__))

    # noinspection PyPep8Naming
    def initGui(self):
        """ Called by QGIS on programm start or loading this plugin.
            At this point you can interacting with QGIS gui, e.g. `self.iface.mainWindow()`.
            Add your own QActions/QToolBars in `utilities.ui_control.load_tool_bar`
        """
        super().initGui()

        # get current logging information
        current_state = "aktiv" if self.is_logging_debug_active() else "inaktiv"
        logging_debug = self.is_logging_debug_active()

        accessibility_state = "deaktivieren" if self.is_accessibility_mode_active() else "aktivieren"
        accessibility_mode = self.is_accessibility_mode_active()

        # create a new action
        self.logging_action = QAction(f"Erweitertes Logging aktivieren (DEBUG ist {current_state})", self)
        self.logging_action.setCheckable(True)
        self.logging_action.setChecked(logging_debug)  # restore the current state
        self.logging_action.toggled.connect(lambda checked: self.__switch_logging_debug_mode())

        # create a new action (accessibility mode)
        self.accessibility_action = QAction(f"Barrierefreiheitsmodus {accessibility_state}", self)
        self.accessibility_action.setCheckable(True)
        self.accessibility_action.setChecked(accessibility_mode)  # restore the current state
        self.accessibility_action.toggled.connect(lambda checked: self.__switch_accessibility_mode())

        # add log action to menu bar, only if this the plugin object and not a boring module
        if self.is_qgis_plugin():
            icon = self.getThemeIcon("mIconFieldTime.svg")
            self.add_action(f"Protokoll-Ordner öffnen",
                            icon,
                            lambda: self.webbrowser_open(Path(self.log_file_path).parent))

            # add the logging & accesibility action to the toolbar
            self.iface.addPluginToMenu(self.plugin_menu_name, self.logging_action)
            self.iface.addPluginToMenu(self.plugin_menu_name, self.accessibility_action)

            tool_tip = ("Das Plugin sowie enthaltene Untermodule werden neugestartet.\n"
                        "Stelle sicher, dass du alle notwendigen Änderungen gespeichert hast.\n\n"
                        "Es können nicht gespeicherte Änderungen verloren gehen!\n\n"
                        "Diese Funktion sollte zur Fehlerbehebung verwendet werden, "
                        "wenn beispielsweise das Plugin komplett abstürzt und nicht mehr reagiert.")
            icon = QIcon(self.getThemeIcon("mActionTiltDown.svg"))
            self.add_action(f"Plugin (+ Module) neuladen",
                            icon,
                            lambda: self.reload(),
                            tool_tip=tool_tip)
            self.add_action(f"Plugineinstellungen zurücksetzen",
                            QIcon(),
                            lambda: self.clear_options(),
                            tool_tip="Im Plugin zwischengespeicherte Optionen/Einstellungen auf Standard setzen.")

        # load actions to run tests and other functionalities
        # add actions only in the dev-mode
        if self.is_dev_mode():
            self.add_action(f"pytest ausführen (ohne pytest-Plugins)",
                            QIcon(),
                            lambda: run_pytest_from_ui(self),
                            tool_tip="Führt pytest für das aktuelle Plugin über die Benutzeroberläche aus.\n"
                                     "tests.py: run_pytest_from_ui-Funktion wird aufgerufen.\n\n"
                                     "Kann möglicherweise nur einmalig ausgeführt werden (QGIS CRASH DANACH MÖGLICH).\n\n"
                                     "Alle pytest-Plugins sind deaktiviert.")

            # TestDockWidget, you can comment this out, when you don't need to test these classes
            from .modules.examples import dockwidget
            dockwidget.init(self)

            self.load_frame_picker()

        # init gui from ui control
        from .utilities.ui_control import init_plugin_gui
        init_plugin_gui(self)

        # Do not add you actions in initGui, keep it clean and use load_tool_bar instead
        from .utilities.ui_control import load_tool_bar
        load_tool_bar(self)

    def __switch_logging_debug_mode(self):
        """ Disables the DEBUG logging from the plugin and restarts the plugin.
        """
        current_state = "aktiv" if self.is_logging_debug_active() else "inaktiv"
        new_state = "deaktivieren" if self.is_logging_debug_active() else "aktivieren"

        confirmed = ConfirmationDialog.confirm_message(
            f"Erweitertes Logging umschalten ({current_state} -> {new_state})",
            f"Möchtest du das erweiterte Logging {new_state}?\n\n"
            f"Das Plugin '{self.plugin_name}' wird anschließend neugestartet.\n"
            f"Etwaige Fenster müssen manuell neu geöffnet werden.\n"
            f"Ungespeicherte Änderungen können verloren gehen.",
            abort_but_visible=True
        )

        if not confirmed:
            # restore the current state
            self.logging_action.blockSignals(True)
            self.logging_action.setChecked(self.is_logging_debug_active())
            self.logging_action.blockSignals(False)
            return

        if self.is_logging_debug_active():
            # remove the existing logging file
            # deactivates the logging
            os.remove(Path(self.plugin_dir) / "logging_level_debug.debug")
            self.log("DEBUG logging disabled.", level=self.INFO)
        else:
            # create the logging file, to mark the logging as active
            with (Path(self.plugin_dir) / "logging_level_debug.debug").open(mode="w", encoding="utf-8") as file:
                file.write("logging active with DEBUG level")
            self.log("DEBUG logging activated.", level=self.INFO)
        self.logging_level_debug = self.is_logging_debug_active()

        self.reload()

    def __switch_accessibility_mode(self):
        """ Disables/Enables the accessibility mode from the plugin and restarts the plugin.
        """
        self._accessibility_config.read(self.accessibility_config_path)
        if self.is_accessibility_mode_active():
            self._accessibility_config.set('accessibility', 'enable', 'false')
        else:
            if not self._accessibility_config.has_section('accessibility'):
                self._accessibility_config.add_section('accessibility')
            self._accessibility_config.set('accessibility', 'enable', 'true')

        with open(self.accessibility_config_path, 'w', encoding='utf-8')  as configfile:
            self._accessibility_config.write(configfile)

        self.reload()

    def reloaded(self):
        self.iface.messageBar().pushSuccess(
            f"{self.plugin_menu_name}",
            "QGIS-Plugin erfolgreich neugestartet")

    def reload(self):
        """ reloads this QGIS plugin """
        if not self.is_qgis_plugin():
            return

        from qgis.utils import reloadPlugin, plugins
        module = os.path.basename(self.get_plugin().plugin_dir)
        reloadPlugin(module)
        module = plugins[module]
        module.pluginReloaded.emit()
        self.pluginUnloaded.emit()

    def unload(self, self_unload: bool = False):
        """ Auto-call when plugin will be unloaded from QGIS plugin manager. """
        super().unload()

        QApplication.restoreOverrideCursor()

        # Entferne Actions
        for action in self._actions:
            self.iface.removePluginMenu(self.plugin_menu_name, action)
            self.iface.removeToolBarIcon(action)

        qgis_unload_keyerror(self.plugin_dir)

        # final remove the menu(action) from this plugin from the QGIS plugin menu
        if plugin_menu := self.get_menu():
            self.iface.pluginMenu().removeAction(plugin_menu.menuAction())

        for marker in self.drawings:
            self.iface.mapCanvas().scene().removeItem(marker)
        self.drawings.clear()
        self.clear_log_files()
        self.clear_temp_files()

    def __repr__(self) -> str:
        if self.is_qgis_plugin():
            managed_by = "QgsApplication(stand-alone)"
            plugin = ""
        else:
            parent = self.get_parent()
            if parent is None:
                managed_by = "self managed, no parent"
                plugin = ""
            else:
                managed_by = self.get_parent().__class__.__name__
                plugin = f", plugin={self.get_plugin().plugin_menu_name}"

        version = getattr(self, "plugin_version", "not set")
        plugin_menu_name = getattr(self, "plugin_menu_name", "not set")

        return f"{self.__class__.__name__}(version={version}, " \
               f"plugin_menu_name={plugin_menu_name}, managed_by={managed_by}{plugin})"
