<!--
SPDX-FileCopyrightText: 2026 Deutsche Telekom Technik GmbH
SPDX-License-Identifier: CC-BY-4.0
-->

# Running pytest from QGIS

## Purpose

This developer feature runs the plugin's pytest tests inside the currently running
QGIS process. It is intended for plugin development and is available only while
`force_dev_mode` is enabled.

The menu action is named **pytest ausführen (ohne pytest-Plugins)**. It calls
`run_pytest_from_ui(plugin)` from `test.py`.

## Test discovery

`run_pytest_from_ui()` searches the plugin directory recursively for directories
whose names end with `tests`. Discovered directories include the plugin's own
`tests` directory and matching test directories below submodules.

Directories whose path segments start with `.` are ignored. This excludes local
development directories such as `.venv` and `.git` from test discovery.

pytest is started with `pytest.ini` from the plugin directory:

```text
pytest.main(["--log-file=<path>", "--config-file=<path>", *test_folders])
```

pytest plugin autoload is disabled when QGIS starts the plugin. This avoids loading
plugins that are not compatible with pytest running inside the QGIS application.

## Optional environment variables

Before the test status dialog opens, QGIS shows an optional file selection dialog.
Select an `.env` or `.ini` file to apply temporary environment variables. Cancel
the file dialog to run pytest without additional environment variables.

The file must use the standard INI format and contain the
`[pytest-environment-variables]` section. This section is also the only section
whose entries are loaded.

### Example file

```ini
[pytest-environment-variables]
API_BASE_URL=https://api.example.invalid
TEST_AUTH_CONFIG=test-profile
DISPLAY_COUNTRY=100%
LOG_LEVEL=DEBUG
```

The parser is Python's `configparser.ConfigParser` with interpolation disabled.
`dotenv` is not required or used. The values are strings and are assigned directly
to `os.environ` as text.

Invalid or unusable files prevent pytest from starting. A missing
`[pytest-environment-variables]` section, an empty section, invalid variable names,
null characters, unreadable files, or configparser syntax errors produce a warning
message containing the file path or parser error.

A file containing only variables in a different section is not accepted.

## Running state and status

The status window is a minimal `QDialog`. It contains:

- a title and final status label;
- the currently running pytest node ID;
- a progress bar for the collected tests;
- a completed/total test counter;
- an `Abbrechen` / `Schließen` button.

During collection or execution, `Abbrechen` requests cancellation. The currently
running test call is allowed to finish; pytest is stopped between test boundaries
by pytest hooks. After collection or while another test starts, a pending
cancellation stops pytest before the next test begins.

During the finished state, the window can be closed with:

- the `Schließen` button;
- the window close control;
- Escape.

Closing the window while pytest is still running requests cancellation instead of
closing the status window immediately.

## Environment restoration

Every value from `[pytest-environment-variables]` is temporary. Before applying
it, `run_pytest_from_ui()` records whether the variable existed and its previous
value.

Restoration happens in the `finally` block for all outcomes:

- a variable that existed is restored to its previous value;
- a variable that did not exist is removed from `os.environ`;
- a pytest success, test failure, exception, or cancellation restores the state;
- standard input, output, and error streams are restored separately in the same
  `finally` block.

An environment variable never remains changed after the UI runner exits.

## Test result state

The status dialog is switched to a final state after pytest returns or raises:

- success: "pytest wurde erfolgreich ausgeführt";
- interruption: "pytest wurde abgebrochen";
- error or internal exception: "pytest wurde mit Fehlern beendet".

A successful run updates the QGIS message bar and opens an information dialog.
A test or pytest failure shows the existing warning and critical message paths.
An interruption uses a warning message instead of a failure message.

## Log files

The runner creates two timestamped files below `plugin.log_dir`:

- `python_<timestamp>.log`: Python output and tracebacks;
- `pytest_<timestamp>.log`: pytest logging configured through `--log-file`.

After execution, the Python log file is opened through `plugin.webbrowser_open()`.
A cancellation or failure should therefore be checked in both the status window
and these log files.

## Implementation references

- `run_pytest_from_ui(plugin)` in `test.py` owns the file selection, environment
  snapshot, pytest execution, stream restoration, and result dialog.
- `load_pytest_environment_variables()` validates and reads the INI file.
- `apply_pytest_environment_variables()` applies the temporary values.
- `restore_pytest_environment_variables()` restores the previous state.
- `PytestStatusDialog` renders collection and execution status.
- `PytestUIPlugin` receives pytest collection and test reports.
- `plugin.py` provides the menu action only in plugin developer mode.
