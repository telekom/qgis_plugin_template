# -*- coding: utf-8 -*-
# SPDX-FileCopyrightText: 2025 Deutsche Telekom Technik GmbH <f.vonstudsinske@telekom.de>
# SPDX-License-Identifier: GPL-3.0-only

import tempfile

from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED

from ..to_plugin_zip import build

def test_build_plugin_zip():
    repo_source = Path(__file__).parent.parent
    file_name = f"{repo_source.name}.zip"

    # test the creation of the zip file
    with tempfile.TemporaryDirectory() as tempdir:
        temp_path = Path(tempdir)
        destination_zip_file = temp_path / file_name
        build(file_name, repo_source, destination_zip_file)
        assert destination_zip_file.is_file()

    # test ignore paths
    with tempfile.TemporaryDirectory() as tempdir:
        temp_path = Path(tempdir)
        destination_zip_file = temp_path / file_name
        ignore_paths = ["plugin.py", "templates"]
        build(file_name, repo_source, destination_zip_file, ignore_paths=ignore_paths)
        assert destination_zip_file.is_file()

        with ZipFile(destination_zip_file, mode="r", compression=ZIP_DEFLATED) as zip_:
            for zip_file in zip_.filelist:
                if zip_file.filename in [f"{file_name}/plugin.py", f"{file_name}/templates"]:
                    raise FileExistsError(f"{zip_file.filename} must be not part of the zip due to ignore file")
