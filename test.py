# -*- coding: utf-8 -*-
# SPDX-FileCopyrightText: 2025 Deutsche Telekom Technik GmbH <f.vonstudsinske@telekom.de>
# SPDX-License-Identifier: GPL-3.0-only

import sys
import traceback
import os

from datetime import datetime
from pathlib import Path

from qgis.PyQt.QtWidgets import QMessageBox


def run_pytest_from_console():

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

    code = pytest.main([f"--config-file={config.as_posix()}"] + root_folders)
    if code != pytest.ExitCode.OK:
        raise TestErrorException(f"Exitcode from pytest is {code}, but {pytest.ExitCode.OK} is expected")


def run_pytest_from_ui(plugin):
    """
    Invoking pytest.main from the current Python process.
    """

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

    # open the log file and set the file object as std-target
    with python_log_file.open("w+") as file:
        try:
            # setup the logging file name
            sys.stderr = file
            sys.stdout = file
            sys.stdin = file

            # run pytest
            code = pytest.main([f"--log-file={pytest_log_file.as_posix()}",
                                f"--config-file={config.as_posix()}"]
                               + root_folders)

            if code != pytest.ExitCode.OK:
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
                                    f"Tests wurden ausgeführt. QGIS-Neustart empfohlen!")

        except Exception as e:
            # write the exception to the log file
            file.write("\n" + str(traceback.format_exc()) + "\n")

            plugin.iface.messageBar().pushWarning("pytest", "Fehler bei Testausführung. Weitere Ergebnisse im Log.")

    # restore the previous std-streams
    sys.stderr = stderr
    sys.stdout = stdout
    sys.stdin = stdin

    plugin.webbrowser_open(python_log_file)


if __name__ == "__main__":
    # run from the console only the pytest tests
    run_pytest_from_console()
