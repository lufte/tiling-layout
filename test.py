#!/usr/bin/env python3

import sys
import os
import unittest
from unittest.mock import Mock, patch
from PyQt5.QtWidgets import QWidget, QApplication

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
from tilinglayout import QTilingLayout


class TransposedMethodsTestCase(unittest.TestCase):

    #  ┌───┬──────────┐
    #  │   │    1     │
    #  │ 0 ├───┬──────┤
    #  │   │ 2 │      │
    #  ├───┴───┤  3   │
    #  │   4   │      │
    #  └───────┴──────┘
    def setUp(self):
        self.app = QApplication([])
        self.layout = QTilingLayout()
        self.widgets = [QWidget() for _ in range(5)]
        self.layout.addWidget(self.widgets[0], 0, 0, 2, 1)
        self.layout.addWidget(self.widgets[1], 0, 1, 1, 3)
        self.layout.addWidget(self.widgets[2], 1, 1, 1, 1)
        self.layout.addWidget(self.widgets[3], 1, 2, 2, 2)
        self.layout.addWidget(self.widgets[4], 2, 0, 1, 2)

    def test_add_widget(self):
        new_widget = QWidget()
        self.layout._add_widget(new_widget, 3, 0, 1, 4, False)
        self.assertEqual(
            self.layout.getItemPosition(self.layout.indexOf(new_widget)),
            (3, 0, 1, 4)
        )
        self.layout.removeWidget(new_widget)

        self.layout._add_widget(new_widget, 3, 0, 1, 4, True)
        self.assertEqual(
            self.layout.getItemPosition(self.layout.indexOf(new_widget)),
            (0, 3, 4, 1)
        )
        self.layout.removeWidget(new_widget)

    def test_row_count(self):
        self.assertEqual(self.layout._row_count(False),
                         self.layout.rowCount())
        self.assertEqual(self.layout._row_count(True),
                         self.layout.columnCount())

    def test_column_count(self):
        self.assertEqual(self.layout._column_count(False),
                         self.layout.columnCount())
        self.assertEqual(self.layout._column_count(True),
                         self.layout.rowCount())

    def test_item_at_position(self):
        for i in range(self.layout.rowCount()):
            for j in range(self.layout.columnCount()):
                self.assertEqual(self.layout.itemAtPosition(i, j),
                                 self.layout._item_at_position(i, j, False))
                self.assertEqual(self.layout.itemAtPosition(j, i),
                                 self.layout._item_at_position(i, j, True))

    def test_get_item_position(self):
        for widget in self.widgets:
            pos = self.layout.getItemPosition(self.layout.indexOf(widget))
            self.assertEqual(pos,
                             self.layout._get_item_position(widget, False))
            self.assertEqual((pos[1], pos[0], pos[3], pos[2]),
                             self.layout._get_item_position(widget, True))
        self.assertRaises(ValueError, self.layout._get_item_position,
                          QWidget(), False)
        self.assertRaises(ValueError, self.layout._get_item_position,
                          QWidget(), True)


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
        supporters = self.layout._get_support_widgets(self.widgets[8], False,
                                                      True)
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
        supporters = self.layout._get_support_widgets(self.widgets[12], True,
                                                      False)
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


class EdgeHeightTestCase(unittest.TestCase):

    #  ┌───┬───────┐
    #  │   │   1   │
    #  │   ├───┬───┤
    #  │ 0 │ 2 │ 3 │
    #  │   ├───┼───┤
    #  │   │ 4 │ 5 │
    #  └───┴───┴───┘
    def setUp(self):
        self.app = QApplication([])
        self.layout = QTilingLayout()
        self.ws = [QWidget() for _ in range(7)]
        self.layout.addWidget(self.ws[0], 0, 0, 3, 1)
        self.layout.addWidget(self.ws[1], 0, 1, 1, 2)
        self.layout.addWidget(self.ws[2], 1, 1, 1, 1)
        self.layout.addWidget(self.ws[3], 1, 2, 1, 1)
        self.layout.addWidget(self.ws[4], 2, 1, 1, 1)
        self.layout.addWidget(self.ws[5], 2, 2, 1, 1)

    def test_all_heights(self):
        self.assertEqual(self.layout._get_edge_height(self.ws[0], True,
                         False), 3)
        self.assertEqual(self.layout._get_edge_height(self.ws[0], False,
                         False), 3)
        self.assertEqual(self.layout._get_edge_height(self.ws[1], True,
                         False), 1)
        self.assertEqual(self.layout._get_edge_height(self.ws[1], False,
                         False), 1)
        self.assertEqual(self.layout._get_edge_height(self.ws[2], True,
                         False), 2)
        self.assertEqual(self.layout._get_edge_height(self.ws[2], False,
                         False), 1)
        self.assertEqual(self.layout._get_edge_height(self.ws[3], True,
                         False), 1)
        self.assertEqual(self.layout._get_edge_height(self.ws[3], False,
                         False), 2)
        self.assertEqual(self.layout._get_edge_height(self.ws[4], True,
                         False), 3)
        self.assertEqual(self.layout._get_edge_height(self.ws[4], False,
                         False), 2)
        self.assertEqual(self.layout._get_edge_height(self.ws[5], True,
                         False), 2)
        self.assertEqual(self.layout._get_edge_height(self.ws[5], False,
                         False), 3)


class CriticalBlockTestCase1(unittest.TestCase):

    #  ┌───────┬───────────────┐
    #  │       │       1       │
    #  │   0   ├───────┬───────┤
    #  │       │   2   │   3   │
    #  ├───────┴───┬───┴───────┤
    #  │           │     5     │
    #  │     4     ├───────────┤
    #  │           │     6     │
    #  ├───────────┼───────────┤
    #  │░░░░░░░░░░░│     7     │
    #  └───────────┴───────────┘
    def setUp(self):
        self.app = QApplication([])
        self.layout = QTilingLayout()
        self.widgets = [QWidget() for _ in range(8)]
        self.layout.addWidget(self.widgets[0], 0, 0, 2, 2)
        self.layout.addWidget(self.widgets[1], 0, 2, 1, 4)
        self.layout.addWidget(self.widgets[2], 1, 2, 1, 2)
        self.layout.addWidget(self.widgets[3], 1, 4, 1, 2)
        self.layout.addWidget(self.widgets[4], 2, 0, 2, 3)
        self.layout.addWidget(self.widgets[5], 2, 3, 1, 3)
        self.layout.addWidget(self.widgets[6], 3, 3, 1, 3)
        self.layout.addWidget(self.widgets[7], 4, 3, 1, 3)

    def test_find_empty_block(self):
        self.assertEqual(self.layout._find_empty_block(False),
                         (4, 0, 1, 3))

    def test_find_critical_block(self):
        self.assertEqual(
            self.layout._find_critical_block(
                (4, 0, 1, 3),
                self.layout._get_support_widgets(self.widgets[6], True, False),
                False
            ),
            (2, 0, 2, 3)
        )


class CriticalBlockTestCase2(unittest.TestCase):

    #  ┌───────────────┐
    #  │       0       │
    #  ├───────┬───────┤
    #  │   1   │   2   │
    #  ├───┬───┼───┬───┤
    #  │ 3 │ 4 │ 5 │ 6 │
    #  ├───┼───┼───┴───┤
    #  │ 7 │ 8 │░░░░░░░│
    #  └───┴───┴───────┘
    def setUp(self):
        self.app = QApplication([])
        self.layout = QTilingLayout()
        self.widgets = [QWidget() for _ in range(10)]
        self.layout.addWidget(self.widgets[0], 0, 0, 1, 4)
        self.layout.addWidget(self.widgets[1], 1, 0, 1, 2)
        self.layout.addWidget(self.widgets[2], 1, 2, 1, 2)
        self.layout.addWidget(self.widgets[3], 2, 0, 1, 1)
        self.layout.addWidget(self.widgets[4], 2, 1, 1, 1)
        self.layout.addWidget(self.widgets[5], 2, 2, 1, 1)
        self.layout.addWidget(self.widgets[6], 2, 3, 1, 1)
        self.layout.addWidget(self.widgets[7], 3, 0, 1, 1)
        self.layout.addWidget(self.widgets[8], 3, 1, 1, 1)

    def test_find_empty_block(self):
        self.assertEqual(self.layout._find_empty_block(False),
                         (3, 2, 1, 2))

    def test_find_critical_block(self):
        self.assertEqual(
            self.layout._find_critical_block(
                (3, 2, 1, 2),
                self.layout._get_support_widgets(self.widgets[8], True, False),
                False
            ),
            (1, 2, 2, 2)
        )


class CriticalBlockTestCase3(unittest.TestCase):

    #  ┌───────────────┐
    #  │       0       │
    #  ├───────┬───────┤
    #  │   1   │   2   │
    #  ├───┬───┼───┬───┤
    #  │ 3 │ 4 │ 5 │ 6 │
    #  ├───┴───┼───┼───┤
    #  │░░░░░░░│ 7 │ 8 │
    #  └───────┴───┴───┘
    def setUp(self):
        self.app = QApplication([])
        self.layout = QTilingLayout()
        self.widgets = [QWidget() for _ in range(10)]
        self.layout.addWidget(self.widgets[0], 0, 0, 1, 4)
        self.layout.addWidget(self.widgets[1], 1, 0, 1, 2)
        self.layout.addWidget(self.widgets[2], 1, 2, 1, 2)
        self.layout.addWidget(self.widgets[3], 2, 0, 1, 1)
        self.layout.addWidget(self.widgets[4], 2, 1, 1, 1)
        self.layout.addWidget(self.widgets[5], 2, 2, 1, 1)
        self.layout.addWidget(self.widgets[6], 2, 3, 1, 1)
        self.layout.addWidget(self.widgets[7], 3, 2, 1, 1)
        self.layout.addWidget(self.widgets[8], 3, 3, 1, 1)

    def test_find_empty_block(self):
        self.assertEqual(self.layout._find_empty_block(False),
                         (3, 0, 1, 2))

    def test_find_critical_block(self):
        self.assertEqual(
            self.layout._find_critical_block(
                (3, 0, 1, 2),
                self.layout._get_support_widgets(self.widgets[7], True, False),
                False
            ),
            (1, 0, 2, 2)
        )


class CriticalBlockTestCase4(unittest.TestCase):

    #  ┌─────────┬─────────┐
    #  │    0    │    1    │
    #  ├───┬─────┴─────────┤
    #  │   │       3       │
    #  │   ├───────┬───────┤
    #  │   │   4   │   5   │
    #  │ 2 ├───┬───┼───┬───┤
    #  │   │ 6 │ 7 │ 8 │ 9 │
    #  │   ├───┴───┼───┼───┤
    #  │   │░░░░░░░│10 │11 │
    #  └───┴───────┴───┴───┘
    def setUp(self):
        self.app = QApplication([])
        self.layout = QTilingLayout()
        self.widgets = [QWidget() for _ in range(13)]
        self.layout.addWidget(self.widgets[0], 0, 0, 1, 5)
        self.layout.addWidget(self.widgets[1], 0, 5, 1, 5)
        self.layout.addWidget(self.widgets[2], 1, 0, 4, 2)
        self.layout.addWidget(self.widgets[3], 1, 2, 1, 8)
        self.layout.addWidget(self.widgets[4], 2, 2, 1, 4)
        self.layout.addWidget(self.widgets[5], 2, 6, 1, 4)
        self.layout.addWidget(self.widgets[6], 3, 2, 1, 2)
        self.layout.addWidget(self.widgets[7], 3, 4, 1, 2)
        self.layout.addWidget(self.widgets[8], 3, 6, 1, 2)
        self.layout.addWidget(self.widgets[9], 3, 8, 1, 2)
        self.layout.addWidget(self.widgets[10], 4, 6, 1, 2)
        self.layout.addWidget(self.widgets[11], 4, 8, 1, 2)

    def test_find_empty_block(self):
        self.assertEqual(self.layout._find_empty_block(False),
                         (4, 2, 1, 4))

    def test_find_critical_block(self):
        self.assertEqual(
            self.layout._find_critical_block(
                (4, 2, 1, 4),
                self.layout._get_support_widgets(self.widgets[10], True, False),
                False
            ),
            (2, 2, 2, 4)
        )


class CriticalBlockTestCase5(unittest.TestCase):

    #  ┌─────────┬─────────┐
    #  │    0    │    1    │
    #  ├─────────┴─────┬───┤
    #  │       2       │   │
    #  ├───────┬───────┤   │
    #  │   4   │   5   │   │
    #  ├───┬───┼───┬───┤ 3 │
    #  │ 6 │ 7 │ 8 │ 9 │   │
    #  ├───┼───┼───┴───┤   │
    #  │10 │11 │░░░░░░░│   │
    #  └───┴───┴───────┴───┘
    def setUp(self):
        self.app = QApplication([])
        self.layout = QTilingLayout()
        self.widgets = [QWidget() for _ in range(13)]
        self.layout.addWidget(self.widgets[0], 0, 0, 1, 5)
        self.layout.addWidget(self.widgets[1], 0, 5, 1, 5)
        self.layout.addWidget(self.widgets[2], 1, 0, 1, 8)
        self.layout.addWidget(self.widgets[3], 1, 8, 4, 2)
        self.layout.addWidget(self.widgets[4], 2, 0, 1, 4)
        self.layout.addWidget(self.widgets[5], 2, 4, 1, 4)
        self.layout.addWidget(self.widgets[6], 3, 0, 1, 2)
        self.layout.addWidget(self.widgets[7], 3, 2, 1, 2)
        self.layout.addWidget(self.widgets[8], 3, 4, 1, 2)
        self.layout.addWidget(self.widgets[9], 3, 6, 1, 2)
        self.layout.addWidget(self.widgets[10], 4, 0, 1, 2)
        self.layout.addWidget(self.widgets[11], 4, 2, 1, 2)

    def test_find_empty_block(self):
        self.assertEqual(self.layout._find_empty_block(False),
                         (4, 4, 1, 4))

    def test_find_critical_block(self):
        self.assertEqual(
            self.layout._find_critical_block(
                (4, 4, 1, 4),
                self.layout._get_support_widgets(self.widgets[11], True, False),
                False
            ),
            (2, 4, 2, 4)
        )


class CriticalBlockTestCase6(unittest.TestCase):

    #  ┌─────────┬─────────┐
    #  │    0    │    1    │
    #  ├───┬─────┴─┬───────┤
    #  │   │   3   │   4   │
    #  │   ├───┬───┼───────┤
    #  │   │   │   │   7   │
    #  │ 2 │ 5 │ 6 ├───┬───┤
    #  │   │   │   │ 8 │ 9 │
    #  │   ├───┴───┼───┼───┤
    #  │   │░░░░░░░│10 │11 │
    #  └───┴───────┴───┴───┘
    def setUp(self):
        self.app = QApplication([])
        self.layout = QTilingLayout()
        self.widgets = [QWidget() for _ in range(13)]
        self.layout.addWidget(self.widgets[0], 0, 0, 1, 5)
        self.layout.addWidget(self.widgets[1], 0, 5, 1, 5)
        self.layout.addWidget(self.widgets[2], 1, 0, 4, 2)
        self.layout.addWidget(self.widgets[3], 1, 2, 1, 4)
        self.layout.addWidget(self.widgets[4], 1, 6, 1, 4)
        self.layout.addWidget(self.widgets[5], 2, 2, 2, 2)
        self.layout.addWidget(self.widgets[6], 2, 4, 2, 2)
        self.layout.addWidget(self.widgets[7], 2, 6, 1, 4)
        self.layout.addWidget(self.widgets[8], 3, 6, 1, 2)
        self.layout.addWidget(self.widgets[9], 3, 8, 1, 2)
        self.layout.addWidget(self.widgets[10], 4, 6, 1, 2)
        self.layout.addWidget(self.widgets[11], 4, 8, 1, 2)

    def test_find_empty_block(self):
        self.assertEqual(self.layout._find_empty_block(False),
                         (4, 2, 1, 4))

    def test_find_critical_block(self):
        self.assertEqual(
            self.layout._find_critical_block(
                (4, 2, 1, 4),
                self.layout._get_support_widgets(self.widgets[10], True, False),
                False
            ),
            (1, 2, 3, 4)
        )


class CriticalBlockTestCase7(unittest.TestCase):

    #  ┌───┬───────┬───────┐
    #  │   │   1   │   2   │
    #  │   ├───────┼───────┤
    #  │   │       │   4   │
    #  │ 0 │   3   ├───┬───┤
    #  │   │       │ 5 │ 6 │
    #  │   ├───────┼───┼───┤
    #  │   │░░░░░░░│ 7 │ 8 │
    #  └───┴───────┴───┴───┘
    def setUp(self):
        self.app = QApplication([])
        self.layout = QTilingLayout()
        self.widgets = [QWidget() for _ in range(10)]
        self.layout.addWidget(self.widgets[0], 0, 0, 4, 2)
        self.layout.addWidget(self.widgets[1], 0, 2, 1, 4)
        self.layout.addWidget(self.widgets[2], 0, 6, 1, 4)
        self.layout.addWidget(self.widgets[3], 1, 2, 2, 4)
        self.layout.addWidget(self.widgets[4], 1, 6, 1, 4)
        self.layout.addWidget(self.widgets[5], 2, 6, 1, 2)
        self.layout.addWidget(self.widgets[6], 2, 8, 1, 2)
        self.layout.addWidget(self.widgets[7], 3, 6, 1, 2)
        self.layout.addWidget(self.widgets[8], 3, 6, 1, 2)

    def test_find_empty_block(self):
        self.assertEqual(self.layout._find_empty_block(False),
                         (3, 2, 1, 4))

    def test_find_critical_block(self):
        self.assertEqual(
            self.layout._find_critical_block(
                (3, 2, 1, 4),
                self.layout._get_support_widgets(self.widgets[7], True, False),
                False
            ),
            (0, 2, 3, 4)
        )


class CriticalBlockTestCase8(unittest.TestCase):

    #  ┌───────┬───────┐
    #  │   0   │   1   │
    #  ├───┬───┼───┬───┤
    #  │ 2 │ 3 │ 4 │ 5 │
    #  ├───┼───┼───┴───┤
    #  │░░░│ 6 │   7   │
    #  └───┴───┴───────┘
    def setUp(self):
        self.app = QApplication([])
        self.layout = QTilingLayout()
        self.widgets = [QWidget() for _ in range(9)]
        self.layout.addWidget(self.widgets[0], 0, 0, 1, 2)
        self.layout.addWidget(self.widgets[1], 0, 2, 1, 2)
        self.layout.addWidget(self.widgets[2], 1, 0, 1, 1)
        self.layout.addWidget(self.widgets[3], 1, 1, 1, 1)
        self.layout.addWidget(self.widgets[4], 1, 2, 1, 1)
        self.layout.addWidget(self.widgets[5], 1, 3, 1, 1)
        self.layout.addWidget(self.widgets[6], 2, 1, 1, 1)
        self.layout.addWidget(self.widgets[7], 2, 2, 1, 2)

    def test_find_empty_block(self):
        self.assertEqual(self.layout._find_empty_block(False),
                         (2, 0, 1, 1))

    def test_find_critical_block(self):
        self.assertEqual(
            self.layout._find_critical_block(
                (2, 0, 1, 1),
                self.layout._get_support_widgets(self.widgets[7], True, False),
                False
            ),
            (0, 0, 2, 2)
        )


class CriticalBlockTestCase9(unittest.TestCase):

    #  ┌───────┬───────┐
    #  │   0   │   1   │
    #  ├───┬───┼───┬───┤
    #  │ 2 │ 3 │ 4 │ 5 │
    #  ├───┼───┼───┴───┤
    #  │ 6 │░░░│   7   │
    #  └───┴───┴───────┘
    def setUp(self):
        self.app = QApplication([])
        self.layout = QTilingLayout()
        self.widgets = [QWidget() for _ in range(9)]
        self.layout.addWidget(self.widgets[0], 0, 0, 1, 2)
        self.layout.addWidget(self.widgets[1], 0, 2, 1, 2)
        self.layout.addWidget(self.widgets[2], 1, 0, 1, 1)
        self.layout.addWidget(self.widgets[3], 1, 1, 1, 1)
        self.layout.addWidget(self.widgets[4], 1, 2, 1, 1)
        self.layout.addWidget(self.widgets[5], 1, 3, 1, 1)
        self.layout.addWidget(self.widgets[6], 2, 0, 1, 1)
        self.layout.addWidget(self.widgets[7], 2, 2, 1, 2)

    def test_find_empty_block(self):
        self.assertEqual(self.layout._find_empty_block(False),
                         (2, 1, 1, 1))

    def test_find_critical_block(self):
        self.assertEqual(
            self.layout._find_critical_block(
                (2, 1, 1, 1),
                self.layout._get_support_widgets(self.widgets[7], True, False),
                False
            ),
            (0, 0, 2, 2)
        )


class CriticalBlockTestCase10(unittest.TestCase):

    #  ┌─────────┬─────────┐
    #  │    0    │    1    │
    #  ├───────┬─┴─────┬───┤
    #  │   2   │   3   │   │
    #  ├───┬───┼───────┤   │
    #  │   │   │   7   │   │
    #  │ 5 │ 6 ├───┬───┤ 4 │
    #  │   │   │ 8 │ 9 │   │
    #  ├───┼───┼───┴───┤   │
    #  │10 │11 │░░░░░░░│   │
    #  └───┴───┴───────┴───┘
    def setUp(self):
        self.app = QApplication([])
        self.layout = QTilingLayout()
        self.widgets = [QWidget() for _ in range(13)]
        self.layout.addWidget(self.widgets[0], 0, 0, 1, 5)
        self.layout.addWidget(self.widgets[1], 0, 5, 1, 5)
        self.layout.addWidget(self.widgets[2], 1, 0, 1, 4)
        self.layout.addWidget(self.widgets[3], 1, 4, 1, 4)
        self.layout.addWidget(self.widgets[4], 1, 8, 4, 2)
        self.layout.addWidget(self.widgets[5], 2, 0, 2, 2)
        self.layout.addWidget(self.widgets[6], 2, 2, 2, 2)
        self.layout.addWidget(self.widgets[7], 2, 4, 1, 4)
        self.layout.addWidget(self.widgets[8], 3, 4, 1, 2)
        self.layout.addWidget(self.widgets[9], 3, 6, 1, 2)
        self.layout.addWidget(self.widgets[10], 4, 0, 1, 2)
        self.layout.addWidget(self.widgets[11], 4, 2, 1, 2)

    def test_find_empty_block(self):
        self.assertEqual(self.layout._find_empty_block(False),
                         (4, 4, 1, 4))

    def test_find_critical_block(self):
        self.assertEqual(
            self.layout._find_critical_block(
                (4, 4, 1, 4),
                self.layout._get_support_widgets(self.widgets[11], True, False),
                False
            ),
            (1, 4, 3, 4)
        )


class CriticalBlockTestCase11(unittest.TestCase):

    #  ┌───┬───┬───────────┐
    #  │   │   │     2     │
    #  │ 0 │ 1 ├───┬───┬───┤
    #  │   │   │ 3 │ 4 │   │
    #  ├───┼───┼───┼───┤ 5 │
    #  │ 6 │ 7 │ 8 │░░░│   │
    #  └───┴───┴───┴───┴───┘
    def setUp(self):
        self.app = QApplication([])
        self.layout = QTilingLayout()
        self.widgets = [QWidget() for _ in range(10)]
        self.layout.addWidget(self.widgets[0], 0, 0, 2, 1)
        self.layout.addWidget(self.widgets[1], 0, 1, 2, 1)
        self.layout.addWidget(self.widgets[2], 0, 2, 1, 3)
        self.layout.addWidget(self.widgets[3], 1, 2, 1, 1)
        self.layout.addWidget(self.widgets[4], 1, 3, 1, 1)
        self.layout.addWidget(self.widgets[5], 1, 4, 2, 1)
        self.layout.addWidget(self.widgets[6], 2, 0, 1, 1)
        self.layout.addWidget(self.widgets[7], 2, 1, 1, 1)
        self.layout.addWidget(self.widgets[8], 2, 2, 1, 1)

    def test_find_empty_block(self):
        self.assertEqual(self.layout._find_empty_block(False),
                         (2, 3, 1, 1))

    def test_find_critical_block(self):
        self.assertEqual(
            self.layout._find_critical_block(
                (2, 3, 1, 1),
                self.layout._get_support_widgets(self.widgets[5], True, False),
                False
            ),
            (1, 3, 1, 1)
        )


class CriticalBlockTestCase12(unittest.TestCase):

    #  ┌───────────┬───────────┬───────────┬───────────┐
    #  │     0     │     1     │     2     │     3     │
    #  ├───────────┴───┬───────┴───────┬───┴───────────┤
    #  │       4       │               │       6       │
    #  ├───────────────┤       5       ├───────────────┤
    #  │       7       │               │░░░░░░░░░░░░░░░│
    #  ├───────────────┴───────┬───────┴───────────────┤
    #  │           8           │           9           │
    #  └───────────────────────┴───────────────────────┘
    def setUp(self):
        self.app = QApplication([])
        self.layout = QTilingLayout()
        self.widgets = [QWidget() for _ in range(11)]
        self.layout.addWidget(self.widgets[0], 0, 0, 1, 3)
        self.layout.addWidget(self.widgets[1], 0, 3, 1, 3)
        self.layout.addWidget(self.widgets[2], 0, 6, 1, 3)
        self.layout.addWidget(self.widgets[3], 0, 9, 1, 3)
        self.layout.addWidget(self.widgets[4], 1, 0, 1, 4)
        self.layout.addWidget(self.widgets[5], 1, 4, 2, 4)
        self.layout.addWidget(self.widgets[6], 1, 8, 1, 4)
        self.layout.addWidget(self.widgets[7], 2, 0, 1, 4)
        self.layout.addWidget(self.widgets[8], 3, 0, 1, 6)
        self.layout.addWidget(self.widgets[9], 3, 6, 1, 6)

    def test_find_empty_block(self):
        self.assertEqual(self.layout._find_empty_block(False),
                         (2, 8, 1, 4))

    def test_find_critical_block(self):
        self.assertEqual(
            self.layout._find_critical_block(
                (2, 8, 1, 4),
                self.layout._get_support_widgets(self.widgets[7], True, False),
                False
            ),
            (1, 8, 1, 4)
        )


if __name__ == '__main__':
    unittest.main()
