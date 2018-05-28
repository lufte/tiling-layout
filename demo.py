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
        pane = Pane(self)
        mainLayout = QTilingLayout(pane, max_span=9)
        mainLayout.removeWidget(pane)

        mainLayout.addWidget(pane, 0, 0, 9, 1)
        mainLayout.addWidget(Pane(self), 0, 1, 1, 8)
        mainLayout.addWidget(Pane(self), 1, 3, 3, 3)
        mainLayout.addWidget(Pane(self), 1, 1, 4, 2)
        mainLayout.addWidget(Pane(self), 1, 6, 5, 3)
        mainLayout.addWidget(Pane(self), 4, 3, 2, 3)
        mainLayout.addWidget(Pane(self), 6, 3, 2, 2)
        mainLayout.addWidget(Pane(self), 6, 5, 2, 2)
        mainLayout.addWidget(Pane(self), 8, 6, 1, 2)
        mainLayout.addWidget(Pane(self), 8, 4, 1, 2)
        mainLayout.addWidget(Pane(self), 8, 2, 1, 2)
        mainLayout.addWidget(Pane(self), 8, 1, 1, 1)
        mainLayout.addWidget(Pane(self), 8, 8, 1, 1)
        mainLayout.addWidget(Pane(self), 6, 7, 2, 2)
        mainLayout.addWidget(Pane(self), 5, 1, 3, 2)

        # mainLayout.addWidget(Pane(self), 0, 0, 9, 1)
        # mainLayout.addWidget(Pane(self), 0, 1, 1, 8)
        # mainLayout.addWidget(Pane(self), 1, 1, 1, 2)
        # mainLayout.addWidget(Pane(self), 1, 3, 1, 3)
        # mainLayout.addWidget(Pane(self), 2, 3, 1, 3)
        # mainLayout.addWidget(Pane(self), 1, 6, 1, 3)
        # mainLayout.addWidget(Pane(self), 3, 3, 1, 3)
        # mainLayout.addWidget(Pane(self), 2, 1, 1, 2)
        # mainLayout.addWidget(Pane(self), 4, 3, 1, 2)
        # mainLayout.addWidget(Pane(self), 4, 5, 1, 2)
        # mainLayout.addWidget(Pane(self), 2, 7, 1, 2)
        # mainLayout.addWidget(Pane(self), 3, 1, 1, 1)
        # mainLayout.addWidget(Pane(self), 5, 2, 1, 2)
        # mainLayout.addWidget(Pane(self), 5, 4, 1, 2)
        # mainLayout.addWidget(Pane(self), 5, 6, 1, 2)
        # mainLayout.addWidget(Pane(self), 3, 8, 1, 1)

        # raises NonRectangularRecBlockException when splitting one of the
        # widgets
        # mainLayout.addWidget(Pane(self),0, 0, 9, 1)
        # mainLayout.addWidget(Pane(self),0, 1, 2, 8)
        # mainLayout.addWidget(Pane(self),2, 3, 2, 3)
        # mainLayout.addWidget(Pane(self),4, 3, 1, 3)
        # mainLayout.addWidget(Pane(self),5, 3, 1, 3)
        # mainLayout.addWidget(Pane(self),6, 5, 1, 2)
        # mainLayout.addWidget(Pane(self),7, 3, 1, 2)
        # mainLayout.addWidget(Pane(self),7, 5, 1, 2)
        # mainLayout.addWidget(Pane(self),7, 7, 1, 2)
        # mainLayout.addWidget(Pane(self),8, 1, 1, 1)
        # mainLayout.addWidget(Pane(self),8, 2, 1, 2)
        # mainLayout.addWidget(Pane(self),8, 4, 1, 2)
        # mainLayout.addWidget(Pane(self),8, 6, 1, 2)
        # mainLayout.addWidget(Pane(self),8, 8, 1, 1)
        # mainLayout.addWidget(Pane(self),2, 6, 4, 3)
        # mainLayout.addWidget(Pane(self),2, 1, 3, 2)
        # mainLayout.addWidget(Pane(self),5, 1, 3, 2)
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

