<!--
SPDX-FileCopyrightText: 2025 Deutsche Telekom AG

SPDX-License-Identifier: CC0-1.0
-->

# QGIS Plugin Template

[![GNU GPLv3](https://img.shields.io/badge/license-%20%20GNU%20GPLv3%20-green?style=plastic)](https://img.shields.io/badge/license-%20%20GNU%20GPLv3%20-green?style=plastic)
[![OpenSSF Scorecard Score](https://api.scorecard.dev/projects/github.com/telekom/qgis_plugin_template/badge)](https://scorecard.dev/viewer/?uri=github.com/telekom/qgis_plugin_template/badge)
[![REUSE Compliance Check](https://github.com/telekom/qgis_plugin_template/actions/workflows/reuse-compliance.yml/badge.svg)](https://github.com/telekom/qgis_plugin_template/actions/workflows/reuse-compliance.yml)

## Description
This repository is a template structure for QGIS plugins.

## Configuration files

Some folders requires extra config files.
Those files are listed here:

* No extra files for the default implementation

## Plugin Template Version
[TEMPLATE_VERSION in plugin.py](./plugin.py) sets the latest template version.
This version number will be saved in the user's profile in the plugin area with e.g. `plugin.get_option()`.

## Testing with pytest

### Test requirements
`pytest` required. No additional pytest plugins needed.

Install the requirements like this:
```cmd
pip install pytest
```

### Test configuration
Create subfolders named `tests`.

With e.g., PyCharm, you can run the tests per (test) folder, file or function.

### Run tests for the plugin

When loading the plugin into QGIS (with the classFactory function),
the environment variable to disable the pytest plugin loading will be set.
Setting this variable will prevent pytest from loading other pytest plugins e.g., pytest-qgis.

The plugin `pytest-qgis` can break the existing QGIS application with the active GUI.

**Run from the user interface** by clicking on the pytest-action in the menu's toolbar.
QGIS may crash instantly after running tests within the QGIS interface or will no more work as excepted.

**QGIS restart recommended**.

**Run the QGIS Python Interpreter (.bat-file) with the [./test.py](test.py) file.
The OS environment variable `QGIS_PYTEST_AUTHENTICATION_CONFIG_DIR` is used
to load authentication configuration files to the temporary QGIS instance.

## Modules and submodules
This plugin template includes default submodules via `git` and provides usages for internal modules within this plugin structure, e.g. loading ui files in existing Qt widgets etc.

### Add a git submodule

```bash
# Change working dir to <plugin>/submodules
cd ../submodules

# Add the submodule
git submodule add https://url.de/to.git <foldername>

# Init the submodule(s)
git submodule update --init --recursive
```

### Remove a git submodule

```bash
# Remove the submodule entry from .git/config
git submodule deinit -f path/to/submodule

# Remove the submodule directory from the superproject's .git/modules directory
rm -rf .git/modules/path/to/submodule

# Remove the entry in .gitmodules and remove the submodule directory located at path/to/submodule
git rm -f path/to/submodule
```

## ToDos for you, when you use this template
1. Edit [metadata.txt](metadata.txt) with basic information about author, name description, version etc.
   1. Edit the contact information (emailBugs)
2. Edit [plugin.py](plugin.py)
   1. rename class to your new plugin name (keep in mind to use meaningful names in PEP8 style)
   2. Go to method `initGui` and look for `test_dockwidget.init` and show what it does
      1. comment it out, if you do not need any examples
   3. Plugin class must inherit [class Plugin](modules/template/base_class.py)
3. Edit [ui_control.py](utilities/ui_control.py)
   1. rename plugin class
   2. in `load_tool_bar` add you actions, you want to add to QGIS at the end of `initGui` call
      1. keep `initGui` method clean!
4. Edit [__init__.py](__init__.py)
   1. change class import to your new class name from plugin.py
5. Do your changes

## Additional information
Some integration tests will be done, when adding modules, inheriting classes etc.

### Git - stay up to date
It is recommended to keep your plugin up to date, based on this template.
E.g. get major updates in [plugin.py](plugin.py) and [base_class.py](modules/template/base_class.py).

If you want to do so, you can add an extra origin url to your cloned repository.
Do not name it `origin`, you can name it like `mirror`.

When you want to update your cloned plugin you can pull from your new origin-url.

Warning: Maybe merge conflicts will come up, when you did some changes in main functionalities.

## Code of Conduct

This project has adopted the [Contributor Covenant](https://www.contributor-covenant.org/) in version 2.1 as our code of conduct. Please see the details in our [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md). All contributors must abide by the code of conduct.

By participating in this project, you agree to abide by its [Code of Conduct](./CODE_OF_CONDUCT.md) at all times.

## Licensing
Copyright (c) 2025 Deutsche Telekom AG

All content in this repository is licensed under at least one of the licenses found in [./LICENSES](./LICENSES); you may not use this file, or any other file in this repository, except in compliance with the Licenses. 
You may obtain a copy of the Licenses by reviewing the files found in the [./LICENSES](./LICENSES) folder.

Unless required by applicable law or agreed to in writing, software distributed under the Licenses is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See in the [./LICENSES](./LICENSES) folder for the specific language governing permissions and limitations under the Licenses.

This project follows the [REUSE standard for software licensing](https://reuse.software/). 
Each file contains copyright and license information, and license texts can be found in the [./LICENSES](./LICENSES) folder. For more information visit https://reuse.software/.
You can find a guide for developers at https://telekom.github.io/reuse-template/.
