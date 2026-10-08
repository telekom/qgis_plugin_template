"""Regression checks for UI roots that could collide with QGIS' main window."""

from pathlib import Path
from xml.etree import ElementTree

import pytest


PLUGIN_ROOT = Path(__file__).resolve().parents[1]
UI_FILES = tuple(sorted(PLUGIN_ROOT.rglob("*.ui")))


@pytest.mark.parametrize("ui_file", UI_FILES, ids=lambda path: path.relative_to(PLUGIN_ROOT).as_posix())
def test_ui_root_object_name_does_not_collide_with_qgis_main_window(ui_file: Path):
    """ QGIS must not mistake a plugin UI root for its own MainWindow. 
        Otherwise it can happen that QGIS openes the first found MainWindow widget to focus on after login with OAuth2
        and redirect from webbrowser to QGIS.
    """
    relative_path = ui_file.relative_to(PLUGIN_ROOT).as_posix()
    root_widget = ElementTree.parse(ui_file).getroot().find("widget")

    assert root_widget is not None, f"No root widget found in {relative_path}"
    assert root_widget.get("name") != "MainWindow", (
        f"{relative_path} declares a top-level widget named 'MainWindow'"
    )
