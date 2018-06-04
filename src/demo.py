#!/usr/bin/env python3

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
from tilinglayout import *
from PyQt5.QtCore import pyqtRemoveInputHook, Qt
from PyQt5.QtWidgets import (QApplication, QLabel, QVBoxLayout, QWidget,
                             QMainWindow)


class CentralWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        pane = Pane(self, text='Left click to split horizontally\n'
                               'Right click to split vertically\n'
                               'Middle click to delete')
        mainLayout = QTilingLayout(pane)
        self.setLayout(mainLayout)

    def hsplit(self, pane):
        self.layout().hsplit(pane, Pane(self))
        self.update_names()

    def vsplit(self, pane):
        self.layout().vsplit(pane, Pane(self))
        self.update_names()

    def delete(self, pane):
        self.layout().remove_widget(pane)
        self.update_names()

    def update_names(self):
        for i in range(self.layout().count()):
            pane = self.layout().itemAt(i).widget()
            pos = self.layout().getItemPosition(i)
            pane.layout().itemAt(0).widget().setText(str(pos))


class Pane(QWidget):
    def __init__(self, parent=None, text=None):
        super().__init__(parent)
        label = QLabel(text or '')
        label.setAlignment(Qt.AlignCenter)
        mainLayout = QVBoxLayout()
        mainLayout.addWidget(label)
        self.setObjectName('pane')
        self.setStyleSheet('* {background-color: #4c60dc; color: white;}')
        self.setLayout(mainLayout)

    def mousePressEvent(self, event):
        if event.button() == 1:
            self.parent().hsplit(self)
        elif event.button() == 2:
            self.parent().vsplit(self)
        else:
            self.parent().delete(self)


if __name__ == '__main__':

    app = QApplication(sys.argv)
    pyqtRemoveInputHook()
    window = QMainWindow()
    cw = CentralWidget(window)
    window.setCentralWidget(cw)
    window.showMaximized()
    sys.exit(app.exec_())
