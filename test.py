#!/usr/bin/env python3

import sys
import os
import unittest
from unittest.mock import Mock, patch
from PyQt5.QtWidgets import QWidget, QApplication

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
from tilinglayout import QTilingLayout, TreeNode


class TreeNodeTestCase(unittest.TestCase):

    def test_one_node_tree(self):
        tree = TreeNode(0)
        self.assertEqual(tree.height, 1)
        self.assertEqual(tree.longest_branches_nodes(), {0})

    def test_taller_tree(self):
        tree = TreeNode(
            0,
            [
                TreeNode(
                    1,
                    [
                        TreeNode(2),
                        TreeNode(3)
                    ]
                ),
                TreeNode(4)
            ]
        )
        self.assertEqual(tree.height, 3)
        self.assertEqual(tree.longest_branches_nodes(), {0, 1, 2, 3})


class Widget(QWidget):

    def __init__(self, name, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.name = name

    def __str__(self):
        return str(self.name)

    def __repr__(self):
        return str(self.name)


def get_empty_tiling_layout():
    mock_widget = QWidget()
    layout = QTilingLayout(mock_widget, max_span=1)
    layout.removeWidget(mock_widget)
    return layout


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
        self.widgets = [Widget(i) for i in range(5)]
        self.layout = get_empty_tiling_layout()
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
    #  ├───┴───┼───┤
    #  │   4   │ 5 │
    #  └───────┴───┘
    def setUp(self):
        self.app = QApplication([])
        self.layout = get_empty_tiling_layout()
        self.ws = [Widget(i) for i in range(7)]
        self.layout.addWidget(self.ws[0], 0, 0, 2, 1)
        self.layout.addWidget(self.ws[1], 0, 1, 1, 2)
        self.layout.addWidget(self.ws[2], 1, 1, 1, 1)
        self.layout.addWidget(self.ws[3], 1, 2, 1, 1)
        self.layout.addWidget(self.ws[4], 2, 0, 1, 2)
        self.layout.addWidget(self.ws[5], 2, 2, 1, 1)

    def test_all_heights(self):
        self.assertEqual(self.layout._get_border_height(0, 0, False, False), 3)
        self.assertEqual(self.layout._get_border_height(0, 0, True, False), 0)
        self.assertEqual(self.layout._get_border_height(0, 1, False, False), 2)
        self.assertEqual(self.layout._get_border_height(0, 1, True, False), 0)
        self.assertEqual(self.layout._get_border_height(0, 2, False, False), 0)
        self.assertEqual(self.layout._get_border_height(0, 2, True, False), 0)
        self.assertEqual(self.layout._get_border_height(1, 0, False, False), 2)
        self.assertEqual(self.layout._get_border_height(1, 0, True, False), 1)
        self.assertEqual(self.layout._get_border_height(1, 1, False, False), 1)
        self.assertEqual(self.layout._get_border_height(1, 1, True, False), 1)
        self.assertEqual(self.layout._get_border_height(1, 2, False, False), 2)
        self.assertEqual(self.layout._get_border_height(1, 2, True, False), 0)
        self.assertEqual(self.layout._get_border_height(2, 0, False, False), 1)
        self.assertEqual(self.layout._get_border_height(2, 0, True, False), 2)
        self.assertEqual(self.layout._get_border_height(2, 1, False, False), 0)
        self.assertEqual(self.layout._get_border_height(2, 1, True, False), 2)
        self.assertEqual(self.layout._get_border_height(2, 2, False, False), 1)
        self.assertEqual(self.layout._get_border_height(2, 2, True, False), 1)


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
        self.layout = get_empty_tiling_layout()
        self.ws = [Widget(i) for i in range(12)]
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
        # self.assertEqual(self.layout._get_independent_block(self.ws[0], False),
        #                  (0, 3))
        # self.assertEqual(self.layout._get_independent_block(self.ws[1], False),
        #                  (0, 3))
        # self.assertEqual(self.layout._get_independent_block(self.ws[2], False),
        #                  (3, 2))
        # self.assertEqual(self.layout._get_independent_block(self.ws[3], False),
        #                  (5, 1))
        # self.assertEqual(self.layout._get_independent_block(self.ws[4], False),
        #                  (0, 3))
        # self.assertEqual(self.layout._get_independent_block(self.ws[5], False),
        #                  (0, 3))
        # self.assertEqual(self.layout._get_independent_block(self.ws[6], False),
        #                  (3, 2))
        # self.assertEqual(self.layout._get_independent_block(self.ws[7], False),
        #                  (3, 2))
        # self.assertEqual(self.layout._get_independent_block(self.ws[8], False),
        #                  (0, 3))
        # self.assertEqual(self.layout._get_independent_block(self.ws[9], False),
        #                  (3, 2))
        # self.assertEqual(self.layout._get_independent_block(self.ws[10],
        #                                                     False),
        #                  (5, 1))
        self.assertEqual(self.layout._get_border_height(0, 3, False, False), 3)


class SupportersTestCase(unittest.TestCase):

    #  ┌───────────┐
    #  │     0     │
    #  ├───┬───────┤
    #  │   │   2   │
    #  │   ├───┬───┤
    #  │ 1 │   │ 4 │
    #  │   │ 3 ├───┤
    #  │   │   │ 5 │
    #  ├───┴───┴───┤
    #  │     6     │
    #  └───────────┘
    def setUp(self):
        self.app = QApplication([])
        self.layout = get_empty_tiling_layout()
        self.ws = [Widget(i) for i in range(8)]
        self.layout.addWidget(self.ws[0], 0, 0, 1, 3)
        self.layout.addWidget(self.ws[1], 1, 0, 3, 1)
        self.layout.addWidget(self.ws[2], 1, 1, 1, 2)
        self.layout.addWidget(self.ws[3], 2, 1, 2, 1)
        self.layout.addWidget(self.ws[4], 2, 2, 1, 1)
        self.layout.addWidget(self.ws[5], 3, 2, 1, 1)
        self.layout.addWidget(self.ws[6], 4, 0, 1, 3)

    def test_down_supporters(self):
        supporters = self.layout._get_supporters(self.ws[0], False, False)
        self.assertEqual(supporters.value, self.ws[0])
        self.assertEqual(supporters.children[0].value, self.ws[1])
        self.assertEqual(supporters.children[0].children[0].value, self.ws[6])
        self.assertEqual(supporters.children[1].value, self.ws[2])
        self.assertEqual(supporters.children[1].children[0].value, self.ws[3])
        self.assertEqual(supporters.children[1].children[0].children[0].value,
                         self.ws[6])
        self.assertEqual(supporters.children[1].children[1].value, self.ws[4])
        self.assertEqual(supporters.children[1].children[1].children[0].value,
                         self.ws[5])
        self.assertEqual(
            supporters.children[1].children[1].children[0].children[0].value,
            self.ws[6]
        )
        self.assertEqual(supporters.children[0].children[0].children, [])

    def test_up_supporters(self):
        supporters = self.layout._get_supporters(self.ws[6], True, False)
        self.assertEqual(supporters.value, self.ws[6])
        self.assertEqual(supporters.children[0].value, self.ws[1])
        self.assertEqual(supporters.children[0].children[0].value, self.ws[0])
        self.assertEqual(supporters.children[1].value, self.ws[3])
        self.assertEqual(supporters.children[1].children[0].value, self.ws[2])
        self.assertEqual(supporters.children[1].children[0].children[0].value,
                         self.ws[0])
        self.assertEqual(supporters.children[2].value, self.ws[5])
        self.assertEqual(supporters.children[2].children[0].value, self.ws[4])
        self.assertEqual(supporters.children[2].children[0].children[0].value,
                         self.ws[2])
        self.assertEqual(
            supporters.children[2].children[0].children[0].children[0].value,
            self.ws[0]
        )
        self.assertEqual(supporters.children[0].children[0].children, [])


class EmptyBlockTestCase(unittest.TestCase):

    #  ┌───────────┬───┐
    #  │░░░░░░░░░░░│   │
    #  │░░░░░░░░░░░│   │
    #  │░░░░░░░░░░░│ 0 │
    #  ├───────────┤   │
    #  │     1     │   │
    #  └───────────┴───┘
    def test_find_empty_block1(self):
        app = QApplication([])
        layout = get_empty_tiling_layout()
        widgets = [QWidget() for _ in range(3)]
        layout.addWidget(widgets[0], 0, 3, 3, 1)
        layout.addWidget(widgets[1], 2, 0, 1, 3)
        self.assertEqual(layout._find_empty_block(False), (0, 0, 2, 3))

    #  ┌───────┬───────┐
    #  │░░░░░░░│   0   │
    #  ├───┬───┼───┬───┤
    #  │ 1 │ 2 │ 3 │ 4 │
    #  ├───┼───┼───┼───┤
    #  │ 5 │ 6 │ 7 │ 8 │
    #  └───┴───┴───┴───┘
    def test_find_empty_block2(self):
        app = QApplication([])
        layout = get_empty_tiling_layout()
        widgets = [QWidget() for _ in range(10)]
        layout.addWidget(widgets[0], 0, 2, 1, 2)
        layout.addWidget(widgets[1], 1, 0, 1, 1)
        layout.addWidget(widgets[2], 1, 1, 1, 1)
        layout.addWidget(widgets[3], 1, 2, 1, 1)
        layout.addWidget(widgets[4], 1, 3, 1, 1)
        layout.addWidget(widgets[5], 2, 0, 1, 1)
        layout.addWidget(widgets[6], 2, 1, 1, 1)
        layout.addWidget(widgets[7], 2, 2, 1, 1)
        layout.addWidget(widgets[8], 2, 3, 1, 1)
        self.assertEqual(layout._find_empty_block(False), (0, 0, 1, 2))

    #  ┌───┬───┬───────┐
    #  │ 0 │ 1 │   2   │
    #  ├───┴───┼───┬───┤
    #  │░░░░░░░│ 3 │ 4 │
    #  ├───┬───┼───┼───┤
    #  │ 5 │ 6 │ 7 │ 8 │
    #  └───┴───┴───┴───┘
    def test_find_empty_block3(self):
        app = QApplication([])
        layout = get_empty_tiling_layout()
        widgets = [QWidget() for _ in range(10)]
        layout.addWidget(widgets[0], 0, 0, 1, 1)
        layout.addWidget(widgets[1], 0, 1, 1, 1)
        layout.addWidget(widgets[2], 0, 2, 1, 2)
        layout.addWidget(widgets[3], 1, 2, 1, 1)
        layout.addWidget(widgets[4], 1, 3, 1, 1)
        layout.addWidget(widgets[5], 2, 0, 1, 1)
        layout.addWidget(widgets[6], 2, 1, 1, 1)
        layout.addWidget(widgets[7], 2, 2, 1, 1)
        layout.addWidget(widgets[8], 2, 3, 1, 1)
        self.assertEqual(layout._find_empty_block(False), (1, 0, 1, 2))

    #  ┌───┬───┬───────┐
    #  │ 1 │ 2 │   0   │
    #  ├───┼───┼───┬───┤
    #  │ 3 │ 4 │ 3 │ 4 │
    #  ├───┴───┼───┼───┤
    #  │░░░░░░░│ 5 │ 6 │
    #  └───────┴───┴───┘
    def test_find_empty_block4(self):
        app = QApplication([])
        layout = get_empty_tiling_layout()
        widgets = [QWidget() for _ in range(10)]
        layout.addWidget(widgets[0], 0, 0, 1, 1)
        layout.addWidget(widgets[1], 0, 1, 1, 1)
        layout.addWidget(widgets[2], 0, 2, 1, 2)
        layout.addWidget(widgets[3], 1, 0, 1, 1)
        layout.addWidget(widgets[4], 1, 1, 1, 1)
        layout.addWidget(widgets[5], 1, 2, 1, 1)
        layout.addWidget(widgets[6], 1, 3, 1, 1)
        layout.addWidget(widgets[7], 2, 2, 1, 1)
        layout.addWidget(widgets[8], 2, 3, 1, 1)
        self.assertEqual(layout._find_empty_block(False), (2, 0, 1, 2))

    #  ┌───┬───────┬───┐
    #  │ 0 │░░░░░░░│ 1 │
    #  ├───┼───┬───┼───┤
    #  │ 2 │ 3 │ 4 │ 5 │
    #  ├───┼───┼───┼───┤
    #  │ 6 │ 7 │ 8 │ 9 │
    #  └───┴───┴───┴───┘
    def test_find_empty_block5(self):
        app = QApplication([])
        layout = get_empty_tiling_layout()
        widgets = [QWidget() for _ in range(11)]
        layout.addWidget(widgets[0], 0, 0, 1, 1)
        layout.addWidget(widgets[1], 0, 3, 1, 1)
        layout.addWidget(widgets[2], 1, 0, 1, 1)
        layout.addWidget(widgets[3], 1, 1, 1, 1)
        layout.addWidget(widgets[4], 1, 2, 1, 1)
        layout.addWidget(widgets[5], 1, 3, 1, 1)
        layout.addWidget(widgets[6], 2, 0, 1, 1)
        layout.addWidget(widgets[7], 2, 1, 1, 1)
        layout.addWidget(widgets[8], 2, 2, 1, 1)
        layout.addWidget(widgets[9], 2, 3, 1, 1)
        self.assertEqual(layout._find_empty_block(False), (0, 1, 1, 2))

    #  ┌───┬───┬───┬───┐
    #  │ 0 │ 1 │ 2 │ 3 │
    #  ├───┼───┴───┼───┤
    #  │ 4 │░░░░░░░│ 5 │
    #  ├───┼───┬───┼───┤
    #  │ 6 │ 7 │ 8 │ 9 │
    #  └───┴───┴───┴───┘
    def test_find_empty_block6(self):
        app = QApplication([])
        layout = get_empty_tiling_layout()
        widgets = [QWidget() for _ in range(11)]
        layout.addWidget(widgets[0], 0, 0, 1, 1)
        layout.addWidget(widgets[1], 0, 1, 1, 1)
        layout.addWidget(widgets[2], 0, 2, 1, 1)
        layout.addWidget(widgets[3], 0, 3, 1, 1)
        layout.addWidget(widgets[4], 1, 0, 1, 1)
        layout.addWidget(widgets[5], 1, 3, 1, 1)
        layout.addWidget(widgets[6], 2, 0, 1, 1)
        layout.addWidget(widgets[7], 2, 1, 1, 1)
        layout.addWidget(widgets[8], 2, 2, 1, 1)
        layout.addWidget(widgets[9], 2, 3, 1, 1)
        self.assertEqual(layout._find_empty_block(False), (1, 1, 1, 2))

    #  ┌───┬───┬───┬───┐
    #  │ 0 │ 1 │ 2 │ 3 │
    #  ├───┼───┼───┼───┤
    #  │ 4 │ 5 │ 6 │ 7 │
    #  ├───┼───┴───┼───┤
    #  │ 8 │░░░░░░░│ 9 │
    #  └───┴───────┴───┘
    def test_find_empty_block7(self):
        app = QApplication([])
        layout = get_empty_tiling_layout()
        widgets = [QWidget() for _ in range(11)]
        layout.addWidget(widgets[0], 0, 0, 1, 1)
        layout.addWidget(widgets[1], 0, 1, 1, 1)
        layout.addWidget(widgets[2], 0, 2, 1, 1)
        layout.addWidget(widgets[3], 0, 3, 1, 1)
        layout.addWidget(widgets[4], 1, 0, 1, 1)
        layout.addWidget(widgets[5], 1, 1, 1, 1)
        layout.addWidget(widgets[6], 1, 2, 1, 1)
        layout.addWidget(widgets[7], 1, 3, 1, 1)
        layout.addWidget(widgets[8], 2, 0, 1, 1)
        layout.addWidget(widgets[9], 2, 3, 1, 1)
        self.assertEqual(layout._find_empty_block(False), (2, 1, 1, 2))

    #  ┌───┬───┬───────┐
    #  │ 0 │ 1 │░░░░░░░│
    #  ├───┼───┼───┬───┤
    #  │ 2 │ 3 │ 4 │ 5 │
    #  ├───┼───┼───┼───┤
    #  │ 6 │ 7 │ 8 │ 9 │
    #  └───┴───┴───┴───┘
    def test_find_empty_block8(self):
        app = QApplication([])
        layout = get_empty_tiling_layout()
        widgets = [QWidget() for _ in range(11)]
        layout.addWidget(widgets[0], 0, 0, 1, 1)
        layout.addWidget(widgets[1], 0, 1, 1, 1)
        layout.addWidget(widgets[2], 1, 0, 1, 1)
        layout.addWidget(widgets[3], 1, 1, 1, 1)
        layout.addWidget(widgets[4], 1, 2, 1, 1)
        layout.addWidget(widgets[5], 1, 3, 1, 1)
        layout.addWidget(widgets[6], 2, 0, 1, 1)
        layout.addWidget(widgets[7], 2, 1, 1, 1)
        layout.addWidget(widgets[8], 2, 2, 1, 1)
        layout.addWidget(widgets[9], 2, 3, 1, 1)
        self.assertEqual(layout._find_empty_block(False), (0, 2, 1, 2))

    #  ┌───┬───┬───┬───┐
    #  │ 1 │ 2 │ 1 │ 2 │
    #  ├───┼───┼───┴───┤
    #  │ 3 │ 4 │░░░░░░░│
    #  ├───┼───┼───┬───┤
    #  │ 5 │ 4 │ 3 │ 6 │
    #  └───┴───┴───┴───┘
    def test_find_empty_block9(self):
        app = QApplication([])
        layout = get_empty_tiling_layout()
        widgets = [QWidget() for _ in range(11)]
        layout.addWidget(widgets[0], 0, 0, 1, 1)
        layout.addWidget(widgets[1], 0, 1, 1, 1)
        layout.addWidget(widgets[2], 0, 2, 1, 1)
        layout.addWidget(widgets[3], 0, 3, 1, 1)
        layout.addWidget(widgets[4], 1, 0, 1, 1)
        layout.addWidget(widgets[5], 1, 1, 1, 1)
        layout.addWidget(widgets[6], 2, 0, 1, 1)
        layout.addWidget(widgets[7], 2, 1, 1, 1)
        layout.addWidget(widgets[8], 2, 2, 1, 1)
        layout.addWidget(widgets[9], 2, 3, 1, 1)
        self.assertEqual(layout._find_empty_block(False), (1, 2, 1, 2))

    #  ┌───┬───┬───┬───┐
    #  │ 0 │ 1 │ 2 │ 3 │
    #  ├───┼───┼───┼───┤
    #  │ 4 │ 5 │ 6 │ 7 │
    #  ├───┼───┼───┴───┤
    #  │ 8 │ 9 │░░░░░░░│
    #  └───┴───┴───────┘
    def test_find_empty_block10(self):
        app = QApplication([])
        layout = get_empty_tiling_layout()
        widgets = [QWidget() for _ in range(11)]
        layout.addWidget(widgets[0], 0, 0, 1, 1)
        layout.addWidget(widgets[1], 0, 1, 1, 1)
        layout.addWidget(widgets[2], 0, 2, 1, 1)
        layout.addWidget(widgets[3], 0, 3, 1, 1)
        layout.addWidget(widgets[4], 1, 0, 1, 1)
        layout.addWidget(widgets[5], 1, 1, 1, 1)
        layout.addWidget(widgets[6], 1, 2, 1, 1)
        layout.addWidget(widgets[7], 1, 3, 1, 1)
        layout.addWidget(widgets[8], 2, 0, 1, 1)
        layout.addWidget(widgets[9], 2, 1, 1, 1)
        self.assertEqual(layout._find_empty_block(False), (2, 2, 1, 2))


class CriticalBlockTestCase(unittest.TestCase):

    #  ┌───────────────────────────┐
    #  │             0             │
    #  ├───┬───────────────────┬───┤
    #  │ 1 │         2         │ 3 │
    #  ├───┴───┬───┬───┬───┬───┴───┤
    #  │       │ 5 │   │ 7 │       │
    #  │   4   ├───┤ 6 ├───┤   8   │
    #  │       │ 9 │   │10 │       │
    #  ├───┬───┴───┴───┴───┴───┬───┤
    #  │11 │        12         │13 │
    #  ├───┴───────────────────┴───┤
    #  │            14             │
    #  └───────────────────────────┘
    def setUp(self):
        app = QApplication([])
        self.layout = get_empty_tiling_layout()
        self.widgets = [QWidget() for _ in range(16)]
        self.layout.addWidget(self.widgets[0], 0, 0, 1, 7)
        self.layout.addWidget(self.widgets[1], 1, 0, 1, 1)
        self.layout.addWidget(self.widgets[2], 1, 1, 1, 5)
        self.layout.addWidget(self.widgets[3], 1, 6, 1, 1)
        self.layout.addWidget(self.widgets[4], 2, 0, 2, 2)
        self.layout.addWidget(self.widgets[5], 2, 2, 1, 1)
        self.layout.addWidget(self.widgets[6], 2, 3, 2, 1)
        self.layout.addWidget(self.widgets[7], 2, 4, 1, 1)
        self.layout.addWidget(self.widgets[8], 2, 5, 2, 2)
        self.layout.addWidget(self.widgets[9], 3, 2, 1, 1)
        self.layout.addWidget(self.widgets[10], 3, 4, 1, 1)
        self.layout.addWidget(self.widgets[11], 4, 0, 1, 1)
        self.layout.addWidget(self.widgets[12], 4, 1, 1, 5)
        self.layout.addWidget(self.widgets[13], 4, 6, 1, 1)
        self.layout.addWidget(self.widgets[14], 5, 0, 1, 7)

    def test_critical_block1(self):
        self.assertEqual(
            self.layout._find_critical_block(2, 1, True, True, False),
            (1, 0, 1, 1)
        )
        self.assertEqual(
            self.layout._find_critical_block(2, 6, True, False, False),
            (1, 6, 1, 1)
        )
        self.assertEqual(
            self.layout._find_critical_block(4, 1, False, True, False),
            (4, 0, 1, 1)
        )
        self.assertEqual(
            self.layout._find_critical_block(4, 6, False, False, False),
            (4, 6, 1, 1)
        )

    def test_critical_block2(self):
        self.assertEqual(
            self.layout._find_critical_block(4, 3, True, True, False),
            (2, 2, 2, 1)
        )
        self.assertEqual(
            self.layout._find_critical_block(4, 4, True, False, False),
            (2, 4, 2, 1)
        )
        self.assertEqual(
            self.layout._find_critical_block(2, 3, False, True, False),
            (2, 2, 2, 1)
        )
        self.assertEqual(
            self.layout._find_critical_block(2, 4, False, False, False),
            (2, 4, 2, 1)
        )

    def test_critical_block3(self):
        self.assertEqual(
            self.layout._find_critical_block(5, 7, True, True, False),
            (0, 0, 5, 7)
        )
        self.assertEqual(
            self.layout._find_critical_block(5, 0, True, False, False),
            (0, 0, 5, 7)
        )
        self.assertEqual(
            self.layout._find_critical_block(1, 7, False, True, False),
            (1, 0, 5, 7)
        )
        self.assertEqual(
            self.layout._find_critical_block(1, 0, False, False, False),
            (1, 0, 5, 7)
        )

if __name__ == '__main__':
    unittest.main()
