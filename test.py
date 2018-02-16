#!/usr/bin/env python3

import sys
import os
import unittest
from unittest.mock import Mock, patch
from PyQt5.QtWidgets import QWidget, QApplication

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
from tilinglayout import QTilingLayout


class IndependentBlocksTestCase1(unittest.TestCase):

    # ┌─┬─┬─┬─┐
    # ├─┤ │ │ │
    # ├─┼─┴─┼─┤
    # ├─┤   │ │
    # └─┴───┴─┘
    def setUp(self):
        self.app = QApplication([])
        self.layout = QTilingLayout()
        self.layout.addWidget(QWidget(), 0, 0, 1, 1)
        self.layout.addWidget(QWidget(), 1, 0, 1, 1)
        self.layout.addWidget(QWidget(), 0, 1, 2, 1)
        self.layout.addWidget(QWidget(), 0, 2, 2, 1)
        self.layout.addWidget(QWidget(), 0, 3, 2, 1)
        self.layout.addWidget(QWidget(), 2, 0, 1, 1)
        self.layout.addWidget(QWidget(), 3, 0, 1, 1)
        self.layout.addWidget(QWidget(), 2, 1, 2, 2)
        self.layout.addWidget(QWidget(), 2, 3, 2, 1)

    def test_horizontal_independent_blocks(self):
        self.assertEqual(self.layout._get_independent_blocks(True), [0, 2])

    def test_vertical_independent_blocks(self):
        self.assertEqual(self.layout._get_independent_blocks(False), [0, 1, 3])


class IndependentBlocksTestCase2(unittest.TestCase):

    # ┌─┐
    # └─┘
    def setUp(self):
        self.app = QApplication([])
        self.layout = QTilingLayout()
        self.layout.addWidget(QWidget(), 0, 0, 1, 1)

    def test_horizontal_independent_blocks(self):
        self.assertEqual(self.layout._get_independent_blocks(True), [0])

    def test_vertical_independent_blocks(self):
        self.assertEqual(self.layout._get_independent_blocks(False), [0])


class IndependentBlocksTestCase3(unittest.TestCase):

    # ┌─┬─┬─┬─┐
    # ├─┼─┼─┼─┤
    # ├─┼─┼─┼─┤
    # ├─┼─┼─┼─┤
    # └─┴─┴─┴─┘
    def setUp(self):
        self.app = QApplication([])
        self.layout = QTilingLayout()
        self.layout.addWidget(QWidget(), 0, 0, 1, 1)
        self.layout.addWidget(QWidget(), 0, 1, 1, 1)
        self.layout.addWidget(QWidget(), 0, 2, 1, 1)
        self.layout.addWidget(QWidget(), 0, 3, 1, 1)
        self.layout.addWidget(QWidget(), 1, 0, 1, 1)
        self.layout.addWidget(QWidget(), 1, 1, 1, 1)
        self.layout.addWidget(QWidget(), 1, 2, 1, 1)
        self.layout.addWidget(QWidget(), 1, 3, 1, 1)
        self.layout.addWidget(QWidget(), 2, 0, 1, 1)
        self.layout.addWidget(QWidget(), 2, 1, 1, 1)
        self.layout.addWidget(QWidget(), 2, 2, 1, 1)
        self.layout.addWidget(QWidget(), 2, 3, 1, 1)
        self.layout.addWidget(QWidget(), 3, 0, 1, 1)
        self.layout.addWidget(QWidget(), 3, 1, 1, 1)
        self.layout.addWidget(QWidget(), 3, 2, 1, 1)
        self.layout.addWidget(QWidget(), 3, 3, 1, 1)

    def test_horizontal_independent_blocks(self):
        self.assertEqual(self.layout._get_independent_blocks(True),
                         [0, 1, 2, 3])

    def test_vertical_independent_blocks(self):
        self.assertEqual(self.layout._get_independent_blocks(False),
                         [0, 1, 2, 3])


if __name__ == '__main__':
    unittest.main()
