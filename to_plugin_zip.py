# -*- coding: utf-8 -*-
# SPDX-FileCopyrightText: 2025 Deutsche Telekom Technik GmbH <f.vonstudsinske@telekom.de>
# SPDX-License-Identifier: GPL-3.0-only

import os
import sys
import getopt

from typing import Optional, List
from pathlib import Path


def build(zip_file_name, repo_location, destination_zip_file, *, ignore_paths: Optional[List[str]] = None):

    if not ignore_paths:
        # non or empty list
        ignore_paths = []

    ignore_paths = ignore_paths + [
        # root folder
        ".idea", ".editorconfig", ".gitignore", ".gitignore", ".git", ".vscode",
        ".mypy_cache", ".gitlab-ci.yml", ".gitlab",
        "_cicd", "README.md",
        "docs",

        # submodules/base (plugin_base)
        "submodules/base/.git", "submodules/base/.gitignore", "submodules/base/.editorconfig",
        "submodules/base/docs", "submodules/base/tests",

        # add other folders here to ignore
    ]

    p = os.path.dirname(__file__)
    sys.path.insert(0, p)

    from submodules.base.create_plugin_zip import CreatePluginZip
    obj = CreatePluginZip(zip_file_name,
                          repo_location,
                          destination_zip_file,
                          ignore_paths=ignore_paths,
                          overwrite=True)
    return obj


def from_sys_args(argv):
    """ Run this script from console with or without argument.

        Arguments:

            * `-o` with destination zip file name like "path/to/archive.zip", defaults to this file location
            * `-x` with ";" path list "path/to/file.y;path/to/test.a" (relative or absolute paths)

    """

    # read the cmd arguments
    opts, args = getopt.getopt(argv, "o:x:", [])
    map_ = dict(opts)
    destination_zip_file = map_.get("-o", (Path(__file__).parent / f"{Path(__file__).parent.name}.zip").as_posix())
    ignore_paths = [path for path in map_.get("-x", "").split(";")]

    zip_file_name = os.path.basename(destination_zip_file)
    zip_file_name = ".".join(zip_file_name.split(".")[:-1])

    repo_location = Path(__file__).parent

    return build(zip_file_name, repo_location, destination_zip_file, ignore_paths=ignore_paths)


if __name__ == "__main__":
    from_sys_args(sys.argv[1:])
