# -*- coding: utf-8 -*-
# SPDX-FileCopyrightText: 2025 Deutsche Telekom Technik GmbH <f.vonstudsinske@telekom.de>
# SPDX-License-Identifier: GPL-3.0-only

import sys
from math import ceil
from pathlib import Path

from typing import Optional, List
from qgis.PyQt.QtCore import QSize, Qt
from qgis.PyQt.uic import loadUiType
from qgis.PyQt.QtWidgets import (QTableWidget, QWidget, QMainWindow,
                                 QApplication, QToolButton, QPlainTextEdit,
                                 QSlider, QProgressBar, QStatusBar,
                                 QLineEdit)
from qgis.PyQt.QtGui import QIcon
from qgis.core import QgsApplication


class Table(QTableWidget):

    def __init__(self, parent=None):
        super().__init__(parent)


FORM_CLASS = loadUiType(str(Path(__file__).parent / "qgis_theme_icons.ui"))[0]


class QgisDefaultThemeTable(QMainWindow, FORM_CLASS):
    """ A small ui to preview all available icons in QGIS from default theme. """
    PlainEdit_Code: QPlainTextEdit
    slider_columns: QSlider
    slider_size: QSlider

    def __init__(self, parent: Optional[QWidget] = None):
        super(QMainWindow, self).__init__(parent)
        self.setupUi(self)

        self._files: List[str] = []

        self.setStatusBar(QStatusBar())
        self.search = QLineEdit()
        self.search.setPlaceholderText("type to search for name")
        self.search.setClearButtonEnabled(True)
        self.statusBar().addWidget(self.search)
        self.progress = QProgressBar()
        self.progress.valueChanged.connect(lambda: QgsApplication.processEvents())
        self.statusBar().addWidget(self.progress)
        self.show()

        # define the column count
        self.c = self.slider_columns.value()
        self.r = ceil(len(self.files) / self.c)

        # read existing icons from source txt file
        path = Path(__file__).parent / "qgis_default_icons.txt"
        if path.is_file():

            files = path.read_text("utf-8").split("\n")
            self.progress.setValue(0)
            self.progress.setFormat(f"Lese {path.name}")
            self.progress.setMaximum(len(files))

            for file in files:
                # get QIcon, QPixmap is possible to
                icon: QIcon = QgsApplication.getThemeIcon(file)
                self.progress.setValue(self.progress.value() + 1)
                if icon.isNull() or not file:
                    # empty string or no icon found
                    continue
                self._files.append(file)
        self._files.sort()

        # resize connections
        self.slider_columns.sliderReleased.connect(self.reset_table)
        self.slider_size.sliderReleased.connect(self.reset_table)
        self.slider_columns.valueChanged.connect(self.set_slider_label_text)
        self.slider_columns.valueChanged.connect(self.reset_table)
        self.slider_size.valueChanged.connect(self.set_slider_label_text)
        self.slider_size.valueChanged.connect(self.reset_table)
        self.search.editingFinished.connect(self.reset_table)
        self.search.returnPressed.connect(self.reset_table)
        self.set_slider_label_text()

        self.setWindowTitle(f"{len(self.files)} icon(s)")
        self.setWindowIcon(QgsApplication.getThemeIcon("mActionShowAllLayers.svg"))

        # load table
        self.reset_table()

    def button_clicked(self, icon: str):
        """ displays code to load this icon """
        code = f'#   "{icon}"\n'
        code += f'icon: QIcon = QgsApplication.getThemeIcon("{icon}")\n'
        code += f'pix: QPixmap = QgsApplication.getThemePixmap("{icon}", ' \
                f'QColor(0, 0, 0, 0), QColor(0, 0, 0, 0), size=64)'

        # create url to Github
        base_url = "https://github.com/qgis/QGIS/tree/master/images/themes/default/"
        base_url += icon

        code += f"\n\n{base_url}\n"

        self.PlainEdit_Code.setPlainText(code)

    def set_slider_label_text(self):
        self.label_columns.setText(f"Columns ({self.slider_columns.value()} / {self.slider_columns.maximum()}):")
        self.label_size.setText(f"Icon Size ({self.slider_size.value()} / {self.slider_size.maximum()}):")

    def reset_table(self):
        self.search.setStyleSheet("")

        if self.slider_size.isSliderDown() or self.slider_columns.isSliderDown():
            # still moving...
            return

        files = self.files
        if not files:
            self.search.setStyleSheet("QLineEdit { background: rgb(255, 0, 0, 60);}")
            return

        QApplication.setOverrideCursor(Qt.BusyCursor)
        self.setEnabled(False)
        self.Table_Icons.clear()
        self.c = self.slider_columns.value()
        self.r = ceil(len(files) / self.c)
        self.Table_Icons.setColumnCount(self.c)
        self.Table_Icons.setRowCount(self.r)
        self.resize_cells()
        # extra width is the size of everything around the table
        extra_width = self.width() - self.Table_Icons.viewport().width()
        # new width is the width around the table + the width of the table with all icons
        new_width = extra_width + self.Table_Icons.horizontalHeader().length()
        self.resize(new_width, self.height())
        self.setEnabled(True)
        QApplication.restoreOverrideCursor()

    @property
    def files(self) -> List[str]:
        search = self.search.text()
        if search:
            files = [f for f in self._files if search.lower() in f.lower()]
        else:
            files = self._files

        return files

    def resize_cells(self):

        size = self.slider_size.value()

        # Headereinstellungen setzen, damit Header eine feste Breite & Höhe haben
        self.Table_Icons.horizontalHeader().setMinimumSectionSize(size)
        self.Table_Icons.verticalHeader().setMinimumSectionSize(size)
        self.Table_Icons.horizontalHeader().setMaximumSectionSize(size)
        self.Table_Icons.verticalHeader().setMaximumSectionSize(size)

        files = self.files

        # progressbar
        self.progress.setValue(0)
        self.progress.setMaximum(len(files))
        self.progress.setFormat("Lade Tabelle")

        i = -1
        for row in range(self.r):

            if i > len(files) - 1:
                break

            for col in range(self.c):
                i += 1
                self.progress.setValue(self.progress.value() + 1)

                if i > len(files) - 1:
                    break

                icon = QIcon(QgsApplication.getThemeIcon(files[i]))

                button = QToolButton()
                button.setText("")
                button.setToolTip(f"{files[i]}")
                button.clicked.connect(lambda *_, file=files[i]: self.button_clicked(file))
                button.setIcon(icon)
                button.setIconSize(QSize(int(size * 0.9), int(size * 0.9)))

                self.Table_Icons.setCellWidget(row, col, button)
                self.Table_Icons.setColumnWidth(col, size)
                self.Table_Icons.setRowHeight(row, size)

        self.progress.setFormat(f"Tabelle geladen mit {len(files)} Icons.")

    def closeEvent(self, a0) -> None:
        self.Table_Icons.clear()
        a0.accept()


if __name__ == "__main__":
    app = QApplication([])
    # Write your code here to load some layers, use processing
    # algorithms, etc.
    w = QgisDefaultThemeTable()

    # Finally, exitQgis() is called to remove the
    # provider and layer registries from memory
    sys.exit(app.exec_())
