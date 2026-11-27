# -*- coding: utf-8 -*-
# SPDX-FileCopyrightText: 2025 Deutsche Telekom Technik GmbH <f.vonstudsinske@telekom.de>
# SPDX-License-Identifier: GPL-3.0-only
""" pytest runners for console and QGIS UI execution. """

import configparser
import os
import sys
import traceback

from datetime import datetime
from pathlib import Path

from qgis.core import QgsApplication
from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtWidgets import (QDialog, QFileDialog, QLabel, QProgressBar,
                                 QPushButton, QMessageBox, QVBoxLayout)


PYTEST_ENVIRONMENT_SECTION = "pytest-environment-variables"
_MISSING_ENVIRONMENT_VALUE = object()


def load_pytest_environment_variables(env_file: Path) -> dict:
    """ Load temporary pytest environment variables from an INI file.

        :param env_file: selected INI or ENV file
        :return: environment variable names and values
    """
    parser = configparser.ConfigParser(interpolation=None)
    parser.optionxform = str

    with env_file.open("r", encoding="utf-8") as file:
        parser.read_file(file)

    if not parser.has_section(PYTEST_ENVIRONMENT_SECTION):
        raise ValueError(f'Die Datei enthält keine Sektion "[{PYTEST_ENVIRONMENT_SECTION}]".')

    variables = dict(parser.items(PYTEST_ENVIRONMENT_SECTION, raw=True))
    if not variables:
        raise ValueError(f'Die Sektion "[{PYTEST_ENVIRONMENT_SECTION}]" enthält keine Variablen.')

    for name, value in variables.items():
        if not name or "=" in name or "\x00" in name:
            raise ValueError(f"Ungültiger Umgebungsvariablenname: {name!r}")
        if "\x00" in value:
            raise ValueError(f"Umgebungsvariable {name!r} enthält ein Null-Zeichen.")

    return variables


def apply_pytest_environment_variables(variables: dict) -> dict:
    """ Apply temporary environment variables and return their previous state.

        :param variables: environment variable names and values
        :return: previous environment state
    """
    previous_state = {}

    for name, value in variables.items():
        previous_state[name] = os.environ.get(name, _MISSING_ENVIRONMENT_VALUE)
        os.environ[name] = value

    return previous_state


def restore_pytest_environment_variables(previous_state: dict) -> None:
    """ Restore the environment state captured before pytest execution.

        :param previous_state: previous environment state
    """
    for name, value in previous_state.items():
        if value is _MISSING_ENVIRONMENT_VALUE:
            os.environ.pop(name, None)
        else:
            os.environ[name] = value


class PytestStatusDialog(QDialog):
    """ Minimal status dialog for pytest execution from the QGIS UI. """

    def __init__(self, parent: object = None) -> None:
        """ Create the status dialog.

            :param parent: optional Qt parent widget
        """
        super().__init__(parent)
        self._canceled = False
        self._running = True

        self.setObjectName("PytestStatusDialog")
        self.setWindowTitle("pytest")
        self.setWindowModality(Qt.ApplicationModal)
        self.setMinimumWidth(480)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(8)

        self.label_title = QLabel("pytest wird ausgeführt")
        self.label_title.setObjectName("Label_Title")
        layout.addWidget(self.label_title)

        self.label_current_test = QLabel("Tests werden gesammelt")
        self.label_current_test.setObjectName("Label_CurrentTest")
        self.label_current_test.setWordWrap(True)
        layout.addWidget(self.label_current_test)

        self.progress_tests = QProgressBar()
        self.progress_tests.setObjectName("Progress_Tests")
        self.progress_tests.setRange(0, 0)
        layout.addWidget(self.progress_tests)

        self.label_status = QLabel("0 / 0 Tests abgeschlossen")
        self.label_status.setObjectName("Label_Status")
        layout.addWidget(self.label_status)

        self.button_cancel = QPushButton("Abbrechen")
        self.button_cancel.setObjectName("Btn_Cancel")
        self.button_cancel.clicked.connect(self._cancel)
        layout.addWidget(self.button_cancel)

    def _process_events(self) -> None:
        """ Process Qt events after a visible status change. """
        QgsApplication.instance().processEvents()

    def set_total(self, total: int) -> None:
        """ Set the total number of collected tests.

            :param total: number of collected tests
        """
        self.progress_tests.setRange(0, max(total, 1))
        self.progress_tests.setValue(0)
        self.label_status.setText(f"0 / {total} Tests abgeschlossen")
        self._process_events()

    def set_current_test(self, node_id: str) -> None:
        """ Set the currently running test.

            :param node_id: pytest node identifier
        """
        self.label_current_test.setText(f"Aktuell: {node_id}")
        self._process_events()

    def set_completed(self, completed: int, total: int) -> None:
        """ Set the completed test count.

            :param completed: number of completed tests
            :param total: number of collected tests
        """
        self.progress_tests.setMaximum(max(total, 1))
        self.progress_tests.setValue(completed)
        self.label_status.setText(f"{completed} / {total} Tests abgeschlossen")
        self._process_events()

    def is_canceled(self) -> bool:
        """ Return whether cancellation was requested. """
        return self._canceled

    def _cancel(self) -> None:
        """ Request cancellation and update the dialog state. """
        if self._canceled:
            return

        self._canceled = True
        self.label_title.setText("pytest wird abgebrochen")
        self.label_current_test.setText("Aktuelle Prüfung wird abgeschlossen")
        self.button_cancel.setEnabled(False)
        self._process_events()

    def finish(self, status: str) -> None:
        """ Switch the dialog from running to the finished state.

            :param status: final status text
        """
        self._running = False
        self.label_title.setText(status)
        self.button_cancel.setText("Schließen")
        self.button_cancel.setEnabled(True)
        self.button_cancel.clicked.disconnect(self._cancel)
        self.button_cancel.clicked.connect(self.close)
        self._process_events()

    def reject(self) -> None:
        """ Cancel during execution or close after execution. """
        if self._running:
            self._cancel()
        else:
            super().reject()

    def closeEvent(self, event: object) -> None:
        """ Cancel an active run or accept closing an finished dialog.

            :param event: Qt close event
        """
        if self._running:
            self._cancel()
            event.ignore()
            return

        event.accept()


class PytestUIPlugin:
    """ pytest hooks that update a QGIS UI status dialog. """

    def __init__(self, dialog: PytestStatusDialog, pytest_module: object) -> None:
        """ Create the hook adapter.

            :param dialog: status dialog
            :param pytest_module: imported pytest module
        """
        self.dialog = dialog
        self.pytest_module = pytest_module
        self.completed_node_ids = set()

    def pytest_collection_finish(self, session: object) -> None:
        """ Update the dialog after pytest collection.

            :param session: pytest session
        """
        if self.dialog.is_canceled():
            self.pytest_module.exit("Ausführung durch Benutzer abgebrochen",
                                    returncode=self.pytest_module.ExitCode.INTERRUPTED)

        self.dialog.set_total(len(session.items))

    def pytest_runtest_logstart(self, nodeid: str, location: object) -> None:
        """ Update the dialog before a test starts.

            :param nodeid: pytest node identifier
            :param location: pytest source location
        """
        del location
        if self.dialog.is_canceled():
            self.pytest_module.exit("Ausführung durch Benutzer abgebrochen",
                                    returncode=self.pytest_module.ExitCode.INTERRUPTED)

        self.dialog.set_current_test(nodeid)

    def pytest_runtest_logreport(self, report: object) -> None:
        """ Count a test after its teardown phase.

            :param report: pytest test report
        """
        if report.when != "teardown" or report.nodeid in self.completed_node_ids:
            return

        self.completed_node_ids.add(report.nodeid)
        total = self.dialog.progress_tests.maximum()
        self.dialog.set_completed(len(self.completed_node_ids), total)


def run_pytest_from_console():
    """ Run pytest outside the QGIS UI. """

    import pytest

    from submodules.base.functions import get_test_folders, get_additional_sys_path_folders
    from submodules.base.qgis.qgis_env import setup_qgis
    from utilities.exceptions import TestErrorException

    # append additional paths
    # keep the path-order to prioritize the imports!
    for path in get_additional_sys_path_folders():
        if path not in [Path(p) for p in sys.path]:
            # append path to sys, if not added yet
            sys.path.append(path.as_posix())

    # read the path for several credentials to load per test
    credentials_path = os.environ.get("QGIS_PYTEST_AUTHENTICATION_CONFIG_DIR")
    if credentials_path:
        credentials_path = Path(credentials_path)

    # setup the QgsApplication, setup some sys.paths and start the application
    setup_qgis(credentials_path)

    root_dir = Path(__file__).parent
    root_folders = get_test_folders(root_dir, ends_with=["tests"])

    # set the path to the config file
    config = root_dir / "pytest.ini"

    code = pytest.main([f"--config-file={config.as_posix()}", *root_folders])
    if code != pytest.ExitCode.OK:
        raise TestErrorException(f"Exitcode from pytest is {code}, but {pytest.ExitCode.OK} is expected")


def run_pytest_from_ui(plugin):
    """ Invoke pytest.main from the current Python process. """

    from .submodules.base.functions import get_test_folders

    # ignore paths (absolute or re-pattern)
    ignore_paths = []

    # get the test folders from the current plugin path
    root_folders = get_test_folders(Path(plugin.plugin_dir), ends_with=["tests"], ignore_paths=ignore_paths)
    if not root_folders:
        QMessageBox.warning(plugin.iface.mainWindow(),
                            "pytest",
                            "Keine 'tests'-Ordner gefunden."
                            "Es können keine Tests ausgeführt werden")
        return

    try:
        import pytest

    except ModuleNotFoundError as e:
        QMessageBox.warning(plugin.iface.mainWindow(),
                            "pytest",
                            f"pytest ist nicht für QGIS korrekt installiert:\n{e}")
        return

    # save temporary std-streams
    stderr = sys.stderr
    stdout = sys.stdout
    stdin = sys.stdin

    # create the temporary output file for test results
    stamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S_%f") + ".log"
    python_log_file = Path(plugin.log_dir) / ("python_" + stamp)
    pytest_log_file = Path(plugin.log_dir) / ("pytest_" + stamp)

    # set the absolute path to the pytest ini to be uses in the tests
    config = Path(plugin.plugin_dir) / "pytest.ini"

    env_file_path, _ = QFileDialog.getOpenFileName(
        plugin.iface.mainWindow(),
        "[optional] Umgebungsvariablen-Datei auswählen (oder abbrechen ohne geänderte Umgebungsvariablen)",
        plugin.plugin_dir,
        "INI-/ENV-Dateien (*.env *.ini);;Alle Dateien (*.*)")

    pytest_environment = {}
    if env_file_path:
        env_file = Path(env_file_path)
        if not env_file.is_file():
            QMessageBox.warning(plugin.iface.mainWindow(),
                                "pytest",
                                f"Die Umgebungsvariablen-Datei existiert nicht:\n{env_file}")
            return

        try:
            pytest_environment = load_pytest_environment_variables(env_file)
        except (configparser.Error, OSError, UnicodeDecodeError, ValueError) as error:
            QMessageBox.warning(plugin.iface.mainWindow(),
                                "pytest",
                                f"Die Umgebungsvariablen-Datei ist ungültig:\n{env_file}\n\n{error}")
            return

    dialog = PytestStatusDialog(plugin.iface.mainWindow())
    dialog.show()

    code = None
    previous_environment = {}

    # open the log file and set the file object as std-target
    with python_log_file.open("w+") as file:
        try:
            previous_environment = apply_pytest_environment_variables(pytest_environment)

            sys.stderr, sys.stdout, sys.stdin = file, file, file

            hook = PytestUIPlugin(dialog, pytest)
            code = pytest.main([f"--log-file={pytest_log_file.as_posix()}",
                                f"--config-file={config.as_posix()}",
                                *root_folders],
                               plugins=[hook])

        except Exception:
            file.write("\n" + str(traceback.format_exc()) + "\n")
            code = pytest.ExitCode.INTERNAL_ERROR
            plugin.iface.messageBar().pushWarning("pytest", "Fehler bei Testausführung. Weitere Ergebnisse im Log.")
        finally:
            restore_pytest_environment_variables(previous_environment)

            sys.stderr, sys.stdout, sys.stdin = stderr, stdout, stdin

            if dialog.is_canceled() or code == pytest.ExitCode.INTERRUPTED:
                dialog.finish("pytest wurde abgebrochen")
            elif code == pytest.ExitCode.OK:
                dialog.finish("pytest wurde erfolgreich ausgeführt")
            else:
                dialog.finish("pytest wurde mit Fehlern beendet")

    if dialog.is_canceled() or code == pytest.ExitCode.INTERRUPTED:
        plugin.iface.messageBar().pushWarning(
            "pytest",
            "Die Testausführung wurde abgebrochen. Weitere Ergebnisse im Log.")
    elif code != pytest.ExitCode.OK:
        QMessageBox.warning(plugin.iface.mainWindow(),
                            "pytest",
                            f"Exitcode von pytest ist {code}, aber {pytest.ExitCode.OK} wird erwartet.\n"
                            f"QGIS-Neustart empfohlen!")
        plugin.iface.messageBar().pushCritical(
            "pytest",
            "Die Tests wurden ausgeführt. Weitere Ergebnisse im Log. QGIS-Neustart empfohlen!")
    else:
        plugin.iface.messageBar().pushSuccess(
            "pytest",
            "Die Tests wurden ausgeführt. Weitere Ergebnisse im Log. QGIS-Neustart empfohlen!")
        QMessageBox.information(plugin.iface.mainWindow(),
                                "pytest",
                                "Tests wurden ausgeführt. QGIS-Neustart empfohlen!")

    plugin.webbrowser_open(python_log_file)


if __name__ == "__main__":
    # run from the console only the pytest tests
    run_pytest_from_console()
