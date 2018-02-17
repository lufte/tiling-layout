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


class SupportWidgetsTestCase(unittest.TestCase):

    #  ┌───┬───┬───────┬───┐
    #  │   │ 1 │   2   │ 3 │
    #  │ 0 ├───┼───┬───┼───┤
    #  │   │ 4 │   │ 6 │ 7 │
    #  ├───┴───┤ 5 ├───┼───┤
    #  │   8   │   │ 9 │   │
    #  ├───┬───┼───┴───┤10 │
    #  │11 │12 │  13   │   │
    #  ├───┴───┴───────┼───┤
    #  │       14      │15 │
    #  └───────────────┴───┘
    def setUp(self):
        self.app = QApplication([])
        self.layout = QTilingLayout()
        self.widgets = [QWidget() for _ in range(16)]
        self.layout.addWidget(self.widgets[0], 0, 0, 2, 1)
        self.layout.addWidget(self.widgets[1], 0, 1, 1, 1)
        self.layout.addWidget(self.widgets[2], 0, 2, 1, 2)
        self.layout.addWidget(self.widgets[3], 0, 4, 1, 1)
        self.layout.addWidget(self.widgets[4], 1, 1, 1, 1)
        self.layout.addWidget(self.widgets[5], 1, 2, 2, 1)
        self.layout.addWidget(self.widgets[6], 1, 3, 1, 1)
        self.layout.addWidget(self.widgets[7], 1, 4, 1, 1)
        self.layout.addWidget(self.widgets[8], 2, 0, 1, 2)
        self.layout.addWidget(self.widgets[9], 2, 3, 1, 1)
        self.layout.addWidget(self.widgets[10], 2, 4, 2, 1)
        self.layout.addWidget(self.widgets[11], 3, 0, 1, 1)
        self.layout.addWidget(self.widgets[12], 3, 1, 1, 1)
        self.layout.addWidget(self.widgets[13], 3, 2, 1, 2)
        self.layout.addWidget(self.widgets[14], 4, 0, 1, 4)
        self.layout.addWidget(self.widgets[15], 4, 4, 1, 1)

    def test_horizontal_before_support_widgets(self):
        supporters = self.layout._get_support_widgets(self.widgets[10], True,
                                                      True)
        self.assertIn(self.widgets[0], supporters)
        self.assertNotIn(self.widgets[1], supporters)
        self.assertNotIn(self.widgets[2], supporters)
        self.assertNotIn(self.widgets[3], supporters)
        self.assertIn(self.widgets[4], supporters)
        self.assertIn(self.widgets[5], supporters)
        self.assertNotIn(self.widgets[6], supporters)
        self.assertNotIn(self.widgets[7], supporters)
        self.assertIn(self.widgets[8], supporters)
        self.assertIn(self.widgets[9], supporters)
        self.assertNotIn(self.widgets[10], supporters)
        self.assertIn(self.widgets[11], supporters)
        self.assertIn(self.widgets[12], supporters)
        self.assertIn(self.widgets[13], supporters)
        self.assertNotIn(self.widgets[14], supporters)
        self.assertNotIn(self.widgets[15], supporters)

    def test_horizontal_after_support_widgets(self):
        supporters = self.layout._get_support_widgets(self.widgets[8], True,
                                                      False)
        self.assertNotIn(self.widgets[0], supporters)
        self.assertNotIn(self.widgets[1], supporters)
        self.assertNotIn(self.widgets[2], supporters)
        self.assertNotIn(self.widgets[3], supporters)
        self.assertNotIn(self.widgets[4], supporters)
        self.assertIn(self.widgets[5], supporters)
        self.assertIn(self.widgets[6], supporters)
        self.assertIn(self.widgets[7], supporters)
        self.assertNotIn(self.widgets[8], supporters)
        self.assertIn(self.widgets[9], supporters)
        self.assertIn(self.widgets[10], supporters)
        self.assertNotIn(self.widgets[11], supporters)
        self.assertNotIn(self.widgets[12], supporters)
        self.assertNotIn(self.widgets[13], supporters)
        self.assertNotIn(self.widgets[14], supporters)
        self.assertNotIn(self.widgets[15], supporters)

    def test_vertical_before_support_widgets(self):
        supporters = self.layout._get_support_widgets(self.widgets[12], False,
                                                      True)
        self.assertIn(self.widgets[0], supporters)
        self.assertIn(self.widgets[1], supporters)
        self.assertNotIn(self.widgets[2], supporters)
        self.assertNotIn(self.widgets[3], supporters)
        self.assertIn(self.widgets[4], supporters)
        self.assertNotIn(self.widgets[5], supporters)
        self.assertNotIn(self.widgets[6], supporters)
        self.assertNotIn(self.widgets[7], supporters)
        self.assertIn(self.widgets[8], supporters)
        self.assertNotIn(self.widgets[9], supporters)
        self.assertNotIn(self.widgets[10], supporters)
        self.assertNotIn(self.widgets[11], supporters)
        self.assertNotIn(self.widgets[12], supporters)
        self.assertNotIn(self.widgets[13], supporters)
        self.assertNotIn(self.widgets[14], supporters)
        self.assertNotIn(self.widgets[15], supporters)

    def test_vertical_after_support_widgets(self):
        supporters = self.layout._get_support_widgets(self.widgets[2], False,
                                                      False)
        self.assertNotIn(self.widgets[0], supporters)
        self.assertNotIn(self.widgets[1], supporters)
        self.assertNotIn(self.widgets[2], supporters)
        self.assertNotIn(self.widgets[3], supporters)
        self.assertNotIn(self.widgets[4], supporters)
        self.assertIn(self.widgets[5], supporters)
        self.assertIn(self.widgets[6], supporters)
        self.assertNotIn(self.widgets[7], supporters)
        self.assertNotIn(self.widgets[8], supporters)
        self.assertIn(self.widgets[9], supporters)
        self.assertNotIn(self.widgets[10], supporters)
        self.assertNotIn(self.widgets[11], supporters)
        self.assertNotIn(self.widgets[12], supporters)
        self.assertIn(self.widgets[13], supporters)
        self.assertIn(self.widgets[14], supporters)
        self.assertNotIn(self.widgets[15], supporters)

if __name__ == '__main__':
    unittest.main()
