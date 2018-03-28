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


class BorderHeightTestCase(unittest.TestCase):

    #  ┌───┬───────┐
    #  │   │   1   │
    #  │ 0 ├───┬───┤
    #  │   │ 2 │ 3 │
    #  ├───┴───┴───┤
    #  │     4     │
    #  └───────────┘
    def setUp(self):
        self.app = QApplication([])
        mock_widget = QWidget()
        self.layout = QTilingLayout(mock_widget, max_span=3)
        self.layout.removeWidget(mock_widget)
        self.ws = [QWidget() for _ in range(7)]
        self.layout.addWidget(self.ws[0], 0, 0, 2, 1)
        self.layout.addWidget(self.ws[1], 0, 1, 1, 2)
        self.layout.addWidget(self.ws[2], 1, 1, 1, 1)
        self.layout.addWidget(self.ws[3], 1, 2, 1, 1)
        self.layout.addWidget(self.ws[4], 2, 0, 1, 2)

    def test_all_heights(self):
        self.assertEqual(self.layout._get_border_height(0, 0, False), 3)
        self.assertEqual(self.layout._get_border_height(0, 1, False), 2)
        self.assertEqual(self.layout._get_border_height(0, 3, False), 3)
        self.assertEqual(self.layout._get_border_height(1, 2, False), 2)


class IndependentBlockTestCase(unittest.TestCase):

    #  ┌───┬───────┬───────┬───┐
    #  │   │   1   │   2   │   │
    #  │ 0 ├───┬───┼───┬───┤ 3 │
    #  │   │ 4 │ 5 │ 6 │ 7 │   │
    #  ├───┴───┴───┼───┴───┼───┤
    #  │     8     │   9   │10 │
    #  └───────────┴───────┴───┘
    def setUp(self):
        self.app = QApplication([])
        mock_widget = QWidget()
        self.layout = QTilingLayout(mock_widget, max_span=1)
        self.layout.removeWidget(mock_widget)
        self.ws = [QWidget() for _ in range(12)]
        self.layout.addWidget(self.ws[0], 0, 0, 2, 1)
        self.layout.addWidget(self.ws[1], 0, 1, 1, 2)
        self.layout.addWidget(self.ws[2], 0, 3, 1, 2)
        self.layout.addWidget(self.ws[3], 0, 5, 2, 1)
        self.layout.addWidget(self.ws[4], 1, 1, 1, 1)
        self.layout.addWidget(self.ws[5], 1, 2, 1, 1)
        self.layout.addWidget(self.ws[6], 1, 3, 1, 1)
        self.layout.addWidget(self.ws[7], 1, 4, 1, 1)
        self.layout.addWidget(self.ws[8], 2, 0, 1, 3)
        self.layout.addWidget(self.ws[9], 2, 3, 1, 2)
        self.layout.addWidget(self.ws[10], 2, 5, 1, 1)

    def test_all_widgets(self):
        self.assertEqual(self.layout._get_independent_block(self.ws[0], False),
                         (0, 3))
        self.assertEqual(self.layout._get_independent_block(self.ws[1], False),
                         (0, 3))
        self.assertEqual(self.layout._get_independent_block(self.ws[2], False),
                         (3, 2))
        self.assertEqual(self.layout._get_independent_block(self.ws[3], False),
                         (5, 1))
        self.assertEqual(self.layout._get_independent_block(self.ws[4], False),
                         (0, 3))
        self.assertEqual(self.layout._get_independent_block(self.ws[5], False),
                         (0, 3))
        self.assertEqual(self.layout._get_independent_block(self.ws[6], False),
                         (3, 2))
        self.assertEqual(self.layout._get_independent_block(self.ws[7], False),
                         (3, 2))
        self.assertEqual(self.layout._get_independent_block(self.ws[8], False),
                         (0, 3))
        self.assertEqual(self.layout._get_independent_block(self.ws[9], False),
                         (3, 2))
        self.assertEqual(self.layout._get_independent_block(self.ws[10],
                                                            False),
                         (5, 1))


if __name__ == '__main__':
    unittest.main()
