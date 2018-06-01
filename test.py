#!/usr/bin/env python3

import sys
import os
import unittest
import random
from unittest.mock import Mock, patch
from PyQt5.QtWidgets import QWidget, QApplication

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
from tilinglayout import (QTilingLayout, EmptyBlock, SplitLimitException,
                          WidgetInEmptyBlockException, CriticalBlock, RecBlock,
                          EmptySpaceInCriticalBlockException, Block,
                          PointOutsideGridException, WidgetOverlapException,
                          InvalidBlockException)


class Widget(QWidget):

    def __init__(self, name, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.name = name

    def __str__(self):
        return 'Widget: {}'.format(self.name)

    def __repr__(self):
        return self.__str__()


@unittest.skipUnless('RandomSplitsTestCase' in sys.argv,
                     'Only run if explicitly called')
class RandomSplitsTestCase(unittest.TestCase):

    def setUp(self):
        self.app = QApplication([])
        self.max_span = 9
        self.initial_positions = [(0, 0, *[self.max_span]*2)]
        self.widgets = [Widget(i) for i in range(self.max_span**2)]
        self.new_widget = Widget('new')
        self.trace = []

    def test(self):
        self._split(self.max_span, self.initial_positions, 0,
                    random.randint(0, 1))

    def _split(self, max_span, positions, widget_to_split, split_horizontally):
        self.trace.append((positions[widget_to_split], split_horizontally))
        layout = QTilingLayout(self.widgets[0], max_span=max_span)
        layout.removeWidget(self.widgets[0])
        for i in range(len(positions)):
            layout._add_widget(self.widgets[i], *positions[i], False)
        try:
            if split_horizontally:
                layout.hsplit(self.widgets[widget_to_split], self.new_widget)
            else:
                layout.vsplit(self.widgets[widget_to_split], self.new_widget)
        except SplitLimitException:
            return
        except Exception as e:
            for entry in self.trace:
                print(entry)
            raise e
        new_positions = [layout.getItemPosition(i)
                         for i in range(layout.count())]
        self._split(max_span, new_positions,
                    random.randrange(len(new_positions)),
                    random.randint(0, 1))


def get_empty_tiling_layout(max_span):
    mock_widget = QWidget()
    layout = QTilingLayout(mock_widget, max_span=max_span)
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
        self.layout = get_empty_tiling_layout(4)
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
        self.layout.removeWidget(self.widgets[2])
        self.layout.removeWidget(self.widgets[4])

        self.layout._add_widget(widget, 1, 2, 3, 2, True)
        self.assertEqual(
            self.layout.getItemPosition(self.layout.indexOf(widget)),
            (2, 1, 2, 3)
        )
        self.layout.removeWidget(widget)

    def test_failed_add_widget(self):
        widget = Widget('new')
        with self.assertRaises(WidgetOverlapException):
            self.layout._add_widget(widget, 1, 1, 2, 2, False)
        with self.assertRaises(WidgetOverlapException):
            self.layout._add_widget(widget, -1, -1, 2, 2, False)

    def test_item_at_position(self):
        for i in range(self.layout.rowCount()):
            for j in range(self.layout.columnCount()):
                self.assertEqual(self.layout.itemAtPosition(i, j),
                                 self.layout._item_at_position(i, j, False))
                self.assertEqual(self.layout.itemAtPosition(j, i),
                                 self.layout._item_at_position(i, j, True))

    def test_failed_item_at_position(self):
        with self.assertRaises(PointOutsideGridException):
            self.layout._item_at_position(-1, 0, False)
        with self.assertRaises(PointOutsideGridException):
            self.layout._item_at_position(0, -1, False)
        with self.assertRaises(PointOutsideGridException):
            self.layout._item_at_position(self.layout.max_span, 0, False)
        with self.assertRaises(PointOutsideGridException):
            self.layout._item_at_position(0, self.layout.max_span, False)
        with self.assertRaises(PointOutsideGridException):
            self.layout._item_at_position(-1, 0, True)
        with self.assertRaises(PointOutsideGridException):
            self.layout._item_at_position(0, -1, True)
        with self.assertRaises(PointOutsideGridException):
            self.layout._item_at_position(self.layout.max_span, 0, True)
        with self.assertRaises(PointOutsideGridException):
            self.layout._item_at_position(0, self.layout.max_span, True)

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


class StateTestCase(unittest.TestCase):

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
        self.layout = get_empty_tiling_layout(4)
        self.layout.addWidget(self.widgets[0], 0, 0, 2, 1)
        self.layout.addWidget(self.widgets[1], 0, 1, 1, 3)
        self.layout.addWidget(self.widgets[2], 1, 1, 1, 1)
        self.layout.addWidget(self.widgets[3], 1, 2, 3, 2)
        self.layout.addWidget(self.widgets[4], 2, 0, 2, 2)

    def test_get_state(self):
        self.assertEqual(self.layout._get_state(),
                         [(self.widgets[0], (0, 0, 2, 1)),
                          (self.widgets[1], (0, 1, 1, 3)),
                          (self.widgets[2], (1, 1, 1, 1)),
                          (self.widgets[3], (1, 2, 3, 2)),
                          (self.widgets[4], (2, 0, 2, 2))])

    def test_restore_state(self):
        state = [(self.widgets[0], (0, 0, 3, 5)),
                 (self.widgets[1], (3, 0, 2, 5))]
        self.layout._restore_state(state)
        self.assertEqual(
            self.layout._get_item_position(self.widgets[0],  False),
            (0, 0, 3, 5)
        )
        self.assertEqual(
            self.layout._get_item_position(self.widgets[1],  False),
            (3, 0, 2, 5)
        )


@unittest.skip('Until we finish coverage')
class SplitsTestCase(unittest.TestCase):

    #  ┌───────┐
    #  │       │
    #  │   0   │
    #  │       │
    #  └───────┘
    def setUp(self):
        self.app = QApplication([])
        self.ws = [Widget(i) for i in range(2)]
        self.layout = get_empty_tiling_layout(2)
        self.layout.addWidget(self.ws[0], 0, 0, 2, 2)

    def test_hsplit_after(self):
        self.layout.hsplit(self.ws[0], self.ws[1])
        self.assertEqual(self.layout._get_item_position(self.ws[0], False),
                         (0, 0, 1, 2))
        self.assertEqual(self.layout._get_item_position(self.ws[1], False),
                         (1, 0, 1, 2))

    def test_hsplit_before(self):
        self.layout.hsplit(self.ws[0], self.ws[1], True)
        self.assertEqual(self.layout._get_item_position(self.ws[0], False),
                         (1, 0, 1, 2))
        self.assertEqual(self.layout._get_item_position(self.ws[1], False),
                         (0, 0, 1, 2))

    def test_vsplit_after(self):
        self.layout.vsplit(self.ws[0], self.ws[1])
        self.assertEqual(self.layout._get_item_position(self.ws[0], False),
                         (0, 0, 2, 1))
        self.assertEqual(self.layout._get_item_position(self.ws[1], False),
                         (0, 1, 2, 1))

    def test_vsplit_before(self):
        self.layout.vsplit(self.ws[0], self.ws[1], True)
        self.assertEqual(self.layout._get_item_position(self.ws[0], False),
                         (0, 1, 2, 1))
        self.assertEqual(self.layout._get_item_position(self.ws[1], False),
                         (0, 0, 2, 1))




class IndependentBlockTestCase(unittest.TestCase):

    #  ┌───┬───────┬───────┬───┐
    #  │   │       │       │   │
    #  │   │   1   │   2   │   │
    #  │   │       │       │   │
    #  │ 0 ├───┬───┼───┬───┤ 3 │
    #  │   │   │   │   │   │   │
    #  │   │ 4 │ 5 │ 6 │ 7 │   │
    #  │   │   │   │   │   │   │
    #  ├───┴───┴───┼───┴───┼───┤
    #  │           │       │   │
    #  │     8     │   9   │10 │
    #  │           │       │   │
    #  └───────────┴───────┴───┘
    def setUp(self):
        self.app = QApplication([])
        self.layout = get_empty_tiling_layout(6)
        self.ws = [Widget(i) for i in range(11)]
        self.layout.addWidget(self.ws[0], 0, 0, 4, 1)
        self.layout.addWidget(self.ws[1], 0, 1, 2, 2)
        self.layout.addWidget(self.ws[2], 0, 3, 2, 2)
        self.layout.addWidget(self.ws[3], 0, 5, 4, 1)
        self.layout.addWidget(self.ws[4], 2, 1, 2, 1)
        self.layout.addWidget(self.ws[5], 2, 2, 2, 1)
        self.layout.addWidget(self.ws[6], 2, 3, 2, 1)
        self.layout.addWidget(self.ws[7], 2, 4, 2, 1)
        self.layout.addWidget(self.ws[8], 4, 0, 2, 3)
        self.layout.addWidget(self.ws[9], 4, 3, 2, 2)
        self.layout.addWidget(self.ws[10], 4, 5, 2, 1)

    def test_all_widgets(self):
        self.assertEqual(self.layout._get_independent_block(self.ws[0], False),
                         CriticalBlock(self.layout, False, 0, 0, 6, 3))
        self.assertEqual(self.layout._get_independent_block(self.ws[1], False),
                         CriticalBlock(self.layout, False, 0, 0, 6, 3))
        self.assertEqual(self.layout._get_independent_block(self.ws[2], False),
                         CriticalBlock(self.layout, False, 0, 3, 6, 2))
        self.assertEqual(self.layout._get_independent_block(self.ws[3], False),
                         CriticalBlock(self.layout, False, 0, 5, 6, 1))
        self.assertEqual(self.layout._get_independent_block(self.ws[4], False),
                         CriticalBlock(self.layout, False, 0, 0, 6, 3))
        self.assertEqual(self.layout._get_independent_block(self.ws[5], False),
                         CriticalBlock(self.layout, False, 0, 0, 6, 3))
        self.assertEqual(self.layout._get_independent_block(self.ws[6], False),
                         CriticalBlock(self.layout, False, 0, 3, 6, 2))
        self.assertEqual(self.layout._get_independent_block(self.ws[7], False),
                         CriticalBlock(self.layout, False, 0, 3, 6, 2))
        self.assertEqual(self.layout._get_independent_block(self.ws[8], False),
                         CriticalBlock(self.layout, False, 0, 0, 6, 3))
        self.assertEqual(self.layout._get_independent_block(self.ws[9], False),
                         CriticalBlock(self.layout, False, 0, 3, 6, 2))
        self.assertEqual(self.layout._get_independent_block(self.ws[10],
                                                            False),
                         CriticalBlock(self.layout, False, 0, 5, 6, 1))


class SupportersTestCase(unittest.TestCase):

    #  ┌───────────────────┐
    #  │         0         │
    #  ├───────────┬───────┤
    #  │           │   2   │
    #  │           ├───┬───┤
    #  │     1     │   │ 4 │
    #  │           │ 3 ├───┤
    #  │           │   │ 5 │
    #  ├───────────┴───┴───┤
    #  │         6         │
    #  └───────────────────┘
    def setUp(self):
        self.app = QApplication([])
        self.layout = get_empty_tiling_layout(5)
        self.ws = [Widget(i) for i in range(7)]
        self.layout.addWidget(self.ws[0], 0, 0, 1, 5)
        self.layout.addWidget(self.ws[1], 1, 0, 3, 3)
        self.layout.addWidget(self.ws[2], 1, 3, 1, 2)
        self.layout.addWidget(self.ws[3], 2, 3, 2, 1)
        self.layout.addWidget(self.ws[4], 2, 4, 1, 1)
        self.layout.addWidget(self.ws[5], 3, 4, 1, 1)
        self.layout.addWidget(self.ws[6], 4, 0, 1, 5)

    def test_down_supporters(self):
        self.assertEqual(self.layout._get_supporters(self.ws[0], False),
                         {self.ws[1], self.ws[2], self.ws[3], self.ws[4],
                          self.ws[5], self.ws[6]})
        self.assertEqual(self.layout._get_supporters(self.ws[1], False),
                         {self.ws[6]})
        self.assertEqual(self.layout._get_supporters(self.ws[2], False),
                         {self.ws[3], self.ws[4], self.ws[5], self.ws[6]})
        self.assertEqual(self.layout._get_supporters(self.ws[3], False),
                         {self.ws[6]})
        self.assertEqual(self.layout._get_supporters(self.ws[4], False),
                         {self.ws[5], self.ws[6]})
        self.assertEqual(self.layout._get_supporters(self.ws[5], False),
                         {self.ws[6]})
        self.assertEqual(self.layout._get_supporters(self.ws[6], False),
                         set())


class VirtualBlockTestCase(unittest.TestCase):

    #  ┌───────┬───────────────────────┐
    #  │       │                       │
    #  │       │            1          │
    #  │   0   │                       │
    #  │       ├───────┬───────────────┤
    #  │       │   2   │               │
    #  ├───────┴───────┤               │
    #  │               │               │
    #  │               │       3       │
    #  │               │               │
    #  │               │               │
    #  │       4       │               │
    #  │               ├───────────────┤
    #  │               │               │
    #  │               │       5       │
    #  │               │               │
    #  └───────────────┴───────────────┘
    def setUp(self):
        self.app = QApplication([])
        self.layout = get_empty_tiling_layout(8)
        self.ws = [Widget(i) for i in range(6)]
        self.layout.addWidget(self.ws[0], 0, 0, 3, 2)
        self.layout.addWidget(self.ws[1], 0, 2, 2, 6)
        self.layout.addWidget(self.ws[2], 2, 2, 1, 2)
        self.layout.addWidget(self.ws[3], 2, 4, 4, 4)
        self.layout.addWidget(self.ws[4], 3, 0, 5, 4)
        self.layout.addWidget(self.ws[5], 6, 4, 2, 4)

    def test_virtualization(self):
        block = CriticalBlock(self.layout, False, 0, 0, 8, 8)
        l = self.ws
        self.assertEqual(block._virtualize(),
                         [(l[0], l[0], l[1], l[1], l[1], l[1], l[1], l[1]),
                          (l[0], l[0], l[1], l[1], l[1], l[1], l[1], l[1]),
                          (l[0], l[0], l[2], l[2], l[3], l[3], l[3], l[3]),
                          (l[4], l[4], l[4], l[4], l[3], l[3], l[3], l[3]),
                          (l[4], l[4], l[4], l[4], l[3], l[3], l[3], l[3]),
                          (l[4], l[4], l[4], l[4], l[3], l[3], l[3], l[3]),
                          (l[4], l[4], l[4], l[4], l[5], l[5], l[5], l[5]),
                          (l[4], l[4], l[4], l[4], l[5], l[5], l[5], l[5])])

    def test_subset_virtualization(self):
        block = CriticalBlock(self.layout, False, 2, 4, 6, 4)
        self.assertEqual(block._virtualize(),
                         [(self.ws[3], self.ws[3], self.ws[3], self.ws[3]),
                          (self.ws[3], self.ws[3], self.ws[3], self.ws[3]),
                          (self.ws[3], self.ws[3], self.ws[3], self.ws[3]),
                          (self.ws[3], self.ws[3], self.ws[3], self.ws[3]),
                          (self.ws[5], self.ws[5], self.ws[5], self.ws[5]),
                          (self.ws[5], self.ws[5], self.ws[5], self.ws[5])])

    def test_materialization(self):
        block = CriticalBlock(self.layout, False, 0, 0, 8, 8)
        virtual = block._virtualize()
        self.assertEqual(
            list(CriticalBlock.materialize_virtual_block(0, 0, virtual)),
            [(w, self.layout._get_item_position(w, False)) for w in self.ws]
        )

    def test_displaced_materialization(self):
        block = CriticalBlock(self.layout, False, 0, 0, 8, 8)
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

    def test_shrink_failure(self):
        block = CriticalBlock(self.layout, False, 0, 0, 8, 8)
        with self.assertRaises(SplitLimitException):
            block.displace_and_resize(0, -5)

    def test_displace_and_resize(self):
        l = self.ws
        block = CriticalBlock(self.layout, False, 0, 0, 8, 8)
        block.displace_and_resize(4, -4)
        block = RecBlock(self.layout, False, 0, 0, 8, 8)
        self.assertEqual(block._virtualize(),
                         [(None, None, None, None, None, None, None, None),
                          (None, None, None, None, None, None, None, None),
                          (None, None, None, None, None, None, None, None),
                          (None, None, None, None, None, None, None, None),
                          (l[0], l[0], l[1], l[1], l[1], l[1], l[1], l[1]),
                          (l[0], l[0], l[2], l[2], l[3], l[3], l[3], l[3]),
                          (l[4], l[4], l[4], l[4], l[3], l[3], l[3], l[3]),
                          (l[4], l[4], l[4], l[4], l[5], l[5], l[5], l[5])])
        block.displace_and_resize(-2, 2)
        block = RecBlock(self.layout, False, 0, 0, 8, 8)
        self.assertEqual(block._virtualize(),
                         [(None, None, None, None, None, None, None, None),
                          (None, None, None, None, None, None, None, None),
                          (l[0], l[0], l[1], l[1], l[1], l[1], l[1], l[1]),
                          (l[0], l[0], l[1], l[1], l[1], l[1], l[1], l[1]),
                          (l[0], l[0], l[2], l[2], l[3], l[3], l[3], l[3]),
                          (l[0], l[0], l[2], l[2], l[3], l[3], l[3], l[3]),
                          (l[4], l[4], l[4], l[4], l[3], l[3], l[3], l[3]),
                          (l[4], l[4], l[4], l[4], l[5], l[5], l[5], l[5])])


class BlockTestCase(unittest.TestCase):
    #  ┌───────────┐
    #  │░░░░░░░░░░░│
    #  │░░░░░░░┌───┤
    #  │░░░░░░░│ 0 │
    #  │░░░┌───┴───┤
    #  │░░░│   1   │
    #  └───┴───────┘
    def setUp(self):
        self.app = QApplication([])
        self.layout = get_empty_tiling_layout(3)
        self.ws = [Widget(i) for i in range(2)]
        self.layout.addWidget(self.ws[0], 1, 3, 1, 1)
        self.layout.addWidget(self.ws[1], 2, 1, 1, 2)

    def test_valid_block(self):
        p =(0, 0, 3, 2)
        block = Block(self.layout, False, *p)
        self.assertEqual((block.i, block.j, block.rowspan, block.colspan), p)

    def test_outside_block(self):
        with self.assertRaises(InvalidBlockException):
            Block(self.layout, False, -1, 0, 3, 3)
        with self.assertRaises(InvalidBlockException):
            Block(self.layout, False, 0, -1, 3, 3)
        with self.assertRaises(InvalidBlockException):
            Block(self.layout, False, 0, 0, 4, 3)
        with self.assertRaises(InvalidBlockException):
            Block(self.layout, False, 0, 0, 3, 4)

    def test_no_area_block(self):
        with self.assertRaises(InvalidBlockException):
            Block(self.layout, False, 0, 0, 0, 3)
        with self.assertRaises(InvalidBlockException):
            Block(self.layout, False, 0, 0, 3, 0)


    def test_repr(self):
        block = Block(self.layout, False, 0, 1, 3, 2)
        self.assertEqual(repr(block), 'Block: 0, 1, 3, 2')


class EmptyBlockTestCase(unittest.TestCase):

    #  ┌───────────────────┬───┐
    #  │         0         │   │
    #  ├───┬───────────┬───┤   │
    #  │   │░░░░░░░░░░░│   │   │
    #  │   │░░░░░░░┌───┤   │   │
    #  │   │░░░░░░░│ 3 │   │ 6 │
    #  │ 1 │░░░┌───┼───┤ 2 │   │
    #  │   │░░░│ 4 │ 5 │   │   │
    #  │   │░░░└───┴───┤   │   │
    #  │   │░░░░░░░░░░░│   │   │
    #  ├───┴───────────┴───┴───┤
    #  │           7           │
    #  └───────────────────────┘
    def setUp(self):
        self.app = QApplication([])
        self.layout = get_empty_tiling_layout(6)
        self.ws = [Widget(i) for i in range(8)]
        self.layout.addWidget(self.ws[0], 0, 0, 1, 5)
        self.layout.addWidget(self.ws[1], 1, 0, 4, 1)
        self.layout.addWidget(self.ws[2], 1, 4, 4, 1)
        self.layout.addWidget(self.ws[3], 2, 3, 1, 1)
        self.layout.addWidget(self.ws[4], 3, 2, 1, 1)
        self.layout.addWidget(self.ws[5], 3, 3, 1, 1)
        self.layout.addWidget(self.ws[6], 0, 5, 5, 1)
        self.layout.addWidget(self.ws[7], 5, 0, 1, 6)

    def test_find(self):
        self.assertEqual(
            EmptyBlock.find_in_block(RecBlock(self.layout, False, 0, 0, 5, 5)),
            EmptyBlock(self.layout, False, 1, 1, 1, 3)
        )
        self.assertEqual(
            EmptyBlock.find_in_block(Block(self.layout, False, 1, 1, 3, 2)),
            EmptyBlock(self.layout, False, 1, 1, 2, 2)
        )
        self.assertEqual(
            EmptyBlock.find_in_block(Block(self.layout, False, 3, 1, 3, 3)),
            EmptyBlock(self.layout, False, 3, 1, 2, 1)
        )

    def test_bad_block(self):
        with self.assertRaises(WidgetInEmptyBlockException) as cm:
            EmptyBlock(self.layout, False, 1, 1, 2, 3)
        self.assertEqual(cm.exception.widget_pos, (2, 3))

    def test_no_block(self):
        self.assertIsNone(EmptyBlock.find_in_block(Block(self.layout, False,
                                                         0, 0, 1, 5)))


if __name__ == '__main__': unittest.main()
