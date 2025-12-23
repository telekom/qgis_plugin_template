# -*- coding: utf-8 -*-
# SPDX-FileCopyrightText: 2025 Deutsche Telekom Technik GmbH <f.vonstudsinske@telekom.de>
# SPDX-License-Identifier: GPL-3.0-only


"""
this script only works with the SOURCE CODE from QGIS

Source: https://github.com/qgis/QGIS

When you downloaded or cloned it, then use the path to

    <root>/images/themes/default


"""
from pathlib import Path
from typing import Optional
from os import remove


def files(path: Path):

    for p in path.iterdir():
        if p.is_file():
            yield p
        elif p.is_dir():
            yield from files(p)


def run(folder: Optional[str] = None):
    if not folder:
        path = Path(input("QGIS theme default path: "))
    else:
        path = Path(folder)

    if not path:
        raise ValueError("missing path")

    if not path.is_dir():
        raise NotADirectoryError(f"'{path}' not found")

    writ_to_file = Path(__file__).parent / "qgis_default_icons.txt"
    if writ_to_file.is_file():
        remove(writ_to_file)

    with open(str(writ_to_file), "a", encoding="utf-8") as f:
        for file_path in files(path):
            file_path_str = str(file_path.parent)
            if file_path_str == str(path):
                # is in root folder
                name = file_path.name
            else:
                # remove path to root folder to only have relative path in default theme
                name = str(file_path).replace(str(path), "").replace("\\", "/")[1:]
            f.write(name + "\n")


if __name__ == "__main__":
    # path to the cloned QGIS repository
    run(r"C:\dev\Git Repositorys\Github\QGIS_3_40_7\images\themes\default")
