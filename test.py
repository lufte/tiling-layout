#!/usr/bin/env python3

import sys
import os
import unittest
from unittest.mock import Mock, patch
from PyQt5.QtWidgets import QWidget, QApplication

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
from tilinglayout import (QTilingLayout, TreeNode, EmptyBlock, ShortBlock,
                          WidgetInEmptyBlockException, CriticalBlock,
                          EmptySpaceInCriticalBlockException,
                          PointOutsideGridException)


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
        return 'Widget: {}'.format(self.name)

    def __repr__(self):
        return 'Widget: {}'.format(self.name)


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
    #  ├───┴───┤      │
    #  │       │  3   │
    #  │   4   │      │
    #  │       │      │
    #  └───────┴──────┘
    def setUp(self):
        self.app = QApplication([])
        self.widgets = [Widget(i) for i in range(5)]
        self.layout = get_empty_tiling_layout()
        self.layout.addWidget(self.widgets[0], 0, 0, 2, 1)
        self.layout.addWidget(self.widgets[1], 0, 1, 1, 3)
        self.layout.addWidget(self.widgets[2], 1, 1, 1, 1)
        self.layout.addWidget(self.widgets[3], 1, 2, 3, 2)
        self.layout.addWidget(self.widgets[4], 2, 0, 2, 2)

    def test_add_widget(self):
        widget = self.widgets[3]
        self.layout.removeWidget(widget)
        self.layout._add_widget(widget, 1, 2, 3, 2, False)
        self.assertEqual(
            self.layout.getItemPosition(self.layout.indexOf(widget)),
            (1, 2, 3, 2)
        )
        self.layout.removeWidget(widget)

        self.layout._add_widget(widget, 1, 2, 3, 2, True)
        self.assertEqual(
            self.layout.getItemPosition(self.layout.indexOf(widget)),
            (2, 1, 2, 3)
        )
        self.layout.removeWidget(widget)

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
        self.ws = [Widget(i) for i in range(11)]
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
                         CriticalBlock(self.layout, False, 0, 0, 3, 3))
        self.assertEqual(self.layout._get_independent_block(self.ws[1], False),
                         CriticalBlock(self.layout, False, 0, 0, 3, 3))
        self.assertEqual(self.layout._get_independent_block(self.ws[2], False),
                         CriticalBlock(self.layout, False, 0, 3, 3, 2))
        self.assertEqual(self.layout._get_independent_block(self.ws[3], False),
                         CriticalBlock(self.layout, False, 0, 5, 3, 1))
        self.assertEqual(self.layout._get_independent_block(self.ws[4], False),
                         CriticalBlock(self.layout, False, 0, 0, 3, 3))
        self.assertEqual(self.layout._get_independent_block(self.ws[5], False),
                         CriticalBlock(self.layout, False, 0, 0, 3, 3))
        self.assertEqual(self.layout._get_independent_block(self.ws[6], False),
                         CriticalBlock(self.layout, False, 0, 3, 3, 2))
        self.assertEqual(self.layout._get_independent_block(self.ws[7], False),
                         CriticalBlock(self.layout, False, 0, 3, 3, 2))
        self.assertEqual(self.layout._get_independent_block(self.ws[8], False),
                         CriticalBlock(self.layout, False, 0, 0, 3, 3))
        self.assertEqual(self.layout._get_independent_block(self.ws[9], False),
                         CriticalBlock(self.layout, False, 0, 3, 3, 2))
        self.assertEqual(self.layout._get_independent_block(self.ws[10],
                                                            False),
                         CriticalBlock(self.layout, False, 0, 5, 3, 1))


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
        self.ws = [Widget(i) for i in range(7)]
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


class CriticalBlockTestCase(unittest.TestCase):

    #  ┌───────┬───┬───┬───────┐
    #  │   0   │ 1 │ 2 │   3   │
    #  ├───┬───┼───┴───┼───┬───┤
    #  │░░░│ 4 │   5   │ 6 │░░░│
    #  ├───┴───┼───┬───┼───┴───┤
    #  │   7   │ 8 │ 9 │  10   │
    #  └───────┴───┴───┴───────┘

    def setUp(self):
        app = QApplication([])
        self.layout = get_empty_tiling_layout()
        self.widgets = [Widget(i) for i in range(11)]
        self.layout.addWidget(self.widgets[0], 0, 0, 1, 2)
        self.layout.addWidget(self.widgets[1], 0, 2, 1, 1)
        self.layout.addWidget(self.widgets[2], 0, 3, 1, 1)
        self.layout.addWidget(self.widgets[3], 0, 4, 1, 2)
        self.layout.addWidget(self.widgets[4], 1, 1, 1, 1)
        self.layout.addWidget(self.widgets[5], 1, 2, 1, 2)
        self.layout.addWidget(self.widgets[6], 1, 4, 1, 1)
        self.layout.addWidget(self.widgets[7], 2, 0, 1, 2)
        self.layout.addWidget(self.widgets[8], 2, 2, 1, 1)
        self.layout.addWidget(self.widgets[9], 2, 3, 1, 1)
        self.layout.addWidget(self.widgets[10], 2, 4, 1, 2)

    def test_building_down_right(self):
        build = CriticalBlock.build_from_point
        self.assertEqual(build(self.layout, False, 0, 0, False, False),
                         CriticalBlock(self.layout, False, 0, 0, 1, 2))
        self.assertEqual(build(self.layout, False, 0, 2, False, False),
                         CriticalBlock(self.layout, False, 0, 2, 3, 2))
        with self.assertRaises(PointOutsideGridException):
            build(self.layout, False, 0, 4, False, False)
        self.assertEqual(build(self.layout, False, 1, 1, False, False),
                         CriticalBlock(self.layout, False, 1, 1, 1, 1))
        self.assertEqual(build(self.layout, False, 1, 2, False, False),
                         CriticalBlock(self.layout, False, 1, 2, 2, 2))
        self.assertEqual(build(self.layout, False, 2, 4, False, False),
                         CriticalBlock(self.layout, False, 2, 4, 1, 2))

    def test_building_down_left(self):
        build = CriticalBlock.build_from_point
        self.assertEqual(build(self.layout, False, 0, 6, False, True),
                         CriticalBlock(self.layout, False, 0, 4, 1, 2))
        self.assertEqual(build(self.layout, False, 0, 4, False, True),
                         CriticalBlock(self.layout, False, 0, 2, 3, 2))
        with self.assertRaises(PointOutsideGridException):
            build(self.layout, False, 0, 2, False, True)
        self.assertEqual(build(self.layout, False, 1, 5, False, True),
                         CriticalBlock(self.layout, False, 1, 4, 1, 1))
        self.assertEqual(build(self.layout, False, 1, 4, False, True),
                         CriticalBlock(self.layout, False, 1, 2, 2, 2))
        self.assertEqual(build(self.layout, False, 2, 2, False, True),
                         CriticalBlock(self.layout, False, 2, 0, 1, 2))

    def test_building_up_right(self):
        build = CriticalBlock.build_from_point
        self.assertEqual(build(self.layout, False, 3, 0, True, False),
                         CriticalBlock(self.layout, False, 2, 0, 1, 2))
        self.assertEqual(build(self.layout, False, 3, 2, True, False),
                         CriticalBlock(self.layout, False, 0, 2, 3, 2))
        with self.assertRaises(PointOutsideGridException):
            build(self.layout, False, 3, 4, True, False)
        self.assertEqual(build(self.layout, False, 2, 1, True, False),
                         CriticalBlock(self.layout, False, 1, 1, 1, 1))
        self.assertEqual(build(self.layout, False, 3, 2, True, False),
                         CriticalBlock(self.layout, False, 0, 2, 3, 2))
        self.assertEqual(build(self.layout, False, 1, 4, True, False),
                         CriticalBlock(self.layout, False, 0, 4, 1, 2))

    def test_building_up_left(self):
        build = CriticalBlock.build_from_point
        self.assertEqual(build(self.layout, False, 3, 6, True, True),
                         CriticalBlock(self.layout, False, 2, 4, 1, 2))
        self.assertEqual(build(self.layout, False, 3, 4, True, True),
                         CriticalBlock(self.layout, False, 0, 2, 3, 2))
        with self.assertRaises(PointOutsideGridException):
            build(self.layout, False, 3, 2, True, True)
        self.assertEqual(build(self.layout, False, 2, 5, True, True),
                         CriticalBlock(self.layout, False, 1, 4, 1, 1))
        self.assertEqual(build(self.layout, False, 2, 4, True, True),
                         CriticalBlock(self.layout, False, 0, 2, 2, 2))
        self.assertEqual(build(self.layout, False, 1, 2, True, True),
                         CriticalBlock(self.layout, False, 0, 0, 1, 2))


class VirtualBlockTestCase(unittest.TestCase):

    #  ┌───┬───────────┐
    #  │   │     1     │
    #  │ 0 ├───┬───────┤
    #  │   │ 2 │       │
    #  ├───┴───┤   3   │
    #  │       │       │
    #  │   4   ├───────┤
    #  │       │   5   │
    #  └───────┴───────┘
    def setUp(self):
        self.app = QApplication([])
        self.layout = get_empty_tiling_layout()
        self.ws = [Widget(i) for i in range(6)]
        self.layout.addWidget(self.ws[0], 0, 0, 2, 1)
        self.layout.addWidget(self.ws[1], 0, 1, 1, 3)
        self.layout.addWidget(self.ws[2], 1, 1, 1, 1)
        self.layout.addWidget(self.ws[3], 1, 2, 2, 2)
        self.layout.addWidget(self.ws[4], 2, 0, 2, 2)
        self.layout.addWidget(self.ws[5], 3, 2, 1, 2)

    def test_virtualization(self):
        block = CriticalBlock(self.layout, False, 0, 0, 4, 4)
        self.assertEqual(block._virtualize(),
                        [(self.ws[0], self.ws[1], self.ws[1], self.ws[1]),
                         (self.ws[0], self.ws[2], self.ws[3], self.ws[3]),
                         (self.ws[4], self.ws[4], self.ws[3], self.ws[3]),
                         (self.ws[4], self.ws[4], self.ws[5], self.ws[5])])

    def test_subset_virtualization(self):
        block = CriticalBlock(self.layout, False, 1, 2, 3, 2)
        self.assertEqual(block._virtualize(),
                        [(self.ws[3], self.ws[3]),
                         (self.ws[3], self.ws[3]),
                         (self.ws[5], self.ws[5])])

    def test_materialization(self):
        block = CriticalBlock(self.layout, False, 0, 0, 4, 4)
        virtual = block._virtualize()
        self.assertEqual(
            list(CriticalBlock.materialize_virtual_block(0, 0, virtual)),
            [(w, self.layout._get_item_position(w, False)) for w in self.ws]
        )

    def test_displaced_materialization(self):
        block = CriticalBlock(self.layout, False, 0, 0, 4, 4)
        virtual = block._virtualize()
        offset = (1, 2)
        expected = [(w, self.layout._get_item_position(w, False))
                    for w in self.ws]
        for i in range(0, len(expected)):
            widget, pos = expected[i]
            expected[i] = (widget, (pos[0] + offset[0], pos[1] + offset[1],
                                    pos[2], pos[3]))
        self.assertEqual(
            list(CriticalBlock.materialize_virtual_block(*offset, virtual)),
            expected
        )

    def test_grow(self):
        block = CriticalBlock(self.layout, False, 0, 0, 4, 4)
        block.displace_and_resize(0, 4)
        self.assertEqual(block._virtualize(),
                        [(self.ws[0], self.ws[1], self.ws[1], self.ws[1]),
                         (self.ws[0], self.ws[1], self.ws[1], self.ws[1]),
                         (self.ws[0], self.ws[2], self.ws[3], self.ws[3]),
                         (self.ws[0], self.ws[2], self.ws[3], self.ws[3]),
                         (self.ws[4], self.ws[4], self.ws[3], self.ws[3]),
                         (self.ws[4], self.ws[4], self.ws[3], self.ws[3]),
                         (self.ws[4], self.ws[4], self.ws[5], self.ws[5]),
                         (self.ws[4], self.ws[4], self.ws[5], self.ws[5])])

    def test_shrink(self):
        block = CriticalBlock(self.layout, False, 0, 0, 4, 4)
        block.displace_and_resize(0, 4)
        block.displace_and_resize(0, -4)
        self.assertEqual(block._virtualize(),
                        [(self.ws[0], self.ws[1], self.ws[1], self.ws[1]),
                         (self.ws[0], self.ws[2], self.ws[3], self.ws[3]),
                         (self.ws[4], self.ws[4], self.ws[3], self.ws[3]),
                         (self.ws[4], self.ws[4], self.ws[5], self.ws[5])])


class EmptyBlockTestCase1(unittest.TestCase):

    #  ┌─────────┐
    #  │░░░░░░░░░│
    #  │░░░░░░░░░│
    #  │░░░░░░░░░│
    #  │░░░░░░░░░│
    #  │░░░░░░░░░│
    #  │░░░░░░░░░│
    #  │░░░░░░░░░│
    #  └─────────┘
    def setUp(self):
        self.app = QApplication([])
        self.layout = get_empty_tiling_layout()
        widget = Widget(0)
        self.layout.addWidget(widget, 0, 0, 4, 3)
        self.layout.removeWidget(widget)

    def test_down_right(self):
        empty_block = EmptyBlock.build_from_point(self.layout, False, 0, 0,
                                                  False, False)
        self.assertEqual((empty_block.i, empty_block.j, empty_block.rowspan,
                          empty_block.colspan), (0, 0, 4, 3))

    def test_down_left(self):
        empty_block = EmptyBlock.build_from_point(self.layout, False, 0, 3,
                                                  False, True)
        self.assertEqual((empty_block.i, empty_block.j, empty_block.rowspan,
                          empty_block.colspan), (0, 0, 4, 3))

    def test_up_right(self):
        empty_block = EmptyBlock.build_from_point(self.layout, False, 4, 0,
                                                  True, False)
        self.assertEqual((empty_block.i, empty_block.j, empty_block.rowspan,
                          empty_block.colspan), (0, 0, 4, 3))

    def test_up_left(self):
        empty_block = EmptyBlock.build_from_point(self.layout, False, 4, 3,
                                                  True, True)
        self.assertEqual((empty_block.i, empty_block.j, empty_block.rowspan,
                          empty_block.colspan), (0, 0, 4, 3))


class EmptyBlockTestCase2(unittest.TestCase):

    #  ┌─────────┐
    #  │░░░░░░░░░│
    #  │░░┌───┐░░│
    #  │░░│ 0 │░░│
    #  │░░└───┘░░│
    #  │░░░░░░░░░│
    #  └─────────┘
    def setUp(self):
        self.app = QApplication([])
        self.layout = get_empty_tiling_layout()
        widget = Widget(0)
        self.layout.addWidget(widget, 0, 0, 3, 3)
        self.layout.removeWidget(widget)
        self.layout.addWidget(widget, 1, 1, 1, 1)

    def test_widget_exception(self):
        with self.assertRaises(WidgetInEmptyBlockException):
            EmptyBlock.build_from_point(self.layout, False, 0, 0, False, False)


class EmptyBlockTestCase3(unittest.TestCase):

    #  ┌───────────────┐
    #  │       0       │
    #  ├───┬───────┬───┤
    #  │   │░░░░░░░│   │
    #  │ 1 │░░░░░░░│ 2 │
    #  │   │░░░░░░░│   │
    #  ├───┴───────┴───┤
    #  │       3       │
    #  └───────────────┘
    def setUp(self):
        self.app = QApplication([])
        self.layout = get_empty_tiling_layout()
        self.ws = [Widget(i) for i in range(4)]
        self.layout.addWidget(self.ws[0], 0, 0, 1, 4)
        self.layout.addWidget(self.ws[1], 1, 0, 2, 1)
        self.layout.addWidget(self.ws[2], 1, 3, 2, 1)
        self.layout.addWidget(self.ws[3], 3, 0, 1, 4)

    def test_down_right(self):
        empty_block = EmptyBlock.build_from_point(self.layout, False, 1, 1,
                                                  False, False)
        self.assertEqual((empty_block.i, empty_block.j, empty_block.rowspan,
                          empty_block.colspan), (1, 1, 2, 2))

    def test_down_left(self):
        empty_block = EmptyBlock.build_from_point(self.layout, False, 1, 3,
                                                  False, True)
        self.assertEqual((empty_block.i, empty_block.j, empty_block.rowspan,
                          empty_block.colspan), (1, 1, 2, 2))

    def test_up_right(self):
        empty_block = EmptyBlock.build_from_point(self.layout, False, 3, 1,
                                                  True, False)
        self.assertEqual((empty_block.i, empty_block.j, empty_block.rowspan,
                          empty_block.colspan), (1, 1, 2, 2))

    def test_up_left(self):
        empty_block = EmptyBlock.build_from_point(self.layout, False, 3, 3,
                                                  True, True)
        self.assertEqual((empty_block.i, empty_block.j, empty_block.rowspan,
                          empty_block.colspan), (1, 1, 2, 2))


class ShortBlockTestCase(unittest.TestCase):

    #  ┌───┬───┬───┐
    #  │░░░│░░░│   │
    #  │░░░├───┤ 2 │
    #  ├───┤   │   │
    #  │   │ 1 │   │
    #  │ 0 │   ├───┤
    #  │   ├───┤░░░│
    #  │   │░░░│░░░│
    #  └───┴───┴───┘
    def setUp(self):
        self.app = QApplication([])
        self.layout = get_empty_tiling_layout()
        self.ws = [Widget(i) for i in range(3)]
        self.layout.addWidget(self.ws[0], 2, 0, 3, 1)
        self.layout.addWidget(self.ws[1], 1, 1, 2, 1)
        self.layout.addWidget(self.ws[2], 0, 2, 3, 1)

    def test_grow(self):
        short_block1 = ShortBlock(self.layout, False, 2, 0, 3, 1)
        short_block1.grow()
        self.assertEqual(self.layout._get_item_position(self.ws[0], False),
                         (0, 0, 5, 1))

if __name__ == '__main__':
    unittest.main()
