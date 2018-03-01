#!/usr/bin/env python3

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
from tilinglayout import QTilingLayout
from PyQt5.QtCore import QFileInfo, pyqtRemoveInputHook
from PyQt5.QtWidgets import (QApplication, QCheckBox, QDialog,
        QDialogButtonBox, QFrame, QGroupBox, QLabel, QLineEdit, QListWidget,
        QTabWidget, QVBoxLayout, QWidget, QMainWindow)


class CentralWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        mainLayout = QTilingLayout()
        mainLayout.addWidget(Pane(self), 0, 0, 1, 1)
        # pos = [(0, 3, 3, 1), (1, 2, 2, 1), (1, 0, 1, 2), (0, 0, 1, 3), (3, 1, 1, 1), (3, 0, 1, 1), (2, 0, 1, 2)]
        # pos = [(0, 3, 3, 1), (1, 0, 1, 2), (0, 0, 1, 3), (3, 1, 1, 1), (3, 0, 1, 1), (2, 0, 1, 2), (0, 2, 3, 1)]
        # pos = [(3, 0, 3, 2), (9, 1, 3, 1), (9, 0, 3, 1), (6, 0, 3, 2), (0, 3, 12, 1), (0, 2, 12, 1), (0, 0, 4, 3)]
        # for p in pos:
        #   mainLayout.addWidget(Pane(self), *p)
        self.setLayout(mainLayout)

    def hsplit(self, pane):
        self.layout().hsplit(pane, Pane(self))

    def vsplit(self, pane):
        self.layout().vsplit(pane, Pane(self))


class Pane(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        fileNameLabel = QLabel(str(id(self)))
        mainLayout = QVBoxLayout()
        mainLayout.addWidget(fileNameLabel)
        self.setObjectName('pane')
        self.setStyleSheet('* {background-color: red; color: white;}')
        self.setLayout(mainLayout)

    def mousePressEvent(self, event):
        if event.button() == 1:
            self.parent().hsplit(self)
        elif event.button() == 2:
            self.parent().vsplit(self)


if __name__ == '__main__':

    app = QApplication(sys.argv)
    pyqtRemoveInputHook()
    window = QMainWindow()
    cw = CentralWidget(window)
    window.setCentralWidget(cw)
    window.showMaximized()
    sys.exit(app.exec_())

