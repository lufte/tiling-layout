#!/usr/bin/env python3

import sys
import os
import unittest
import random
import types
from PyQt5.QtWidgets import QWidget, QApplication

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
from tilinglayout import (QTilingLayout, EmptyBlock, InvalidBlockException,
                          WidgetInEmptyBlockException, CriticalBlock, RecBlock,
                          EmptySpaceInCriticalBlockException, Block,
                          PointOutsideGridException, WidgetOverlapException,
                          SplitLimitException, ImpossibleToBuildBlockException,
                          SplitException, NonRectangularRecBlockException)


class Widget(QWidget):

    def __init__(self, name, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.name = name

    def __str__(self):
        return 'Widget: {}'.format(self.name)

    def __repr__(self):
        return self.__str__()


class SplitExceptionTestCase(unittest.TestCase):

    def test_init(self):
        positions = [(0, 0, 1, 2), (1, 0, 1, 2)]

        hsplit_ex = SplitException(positions, 0, 'hsplit')
        self.assertEqual(hsplit_ex.positions, positions)
        self.assertEqual(hsplit_ex.pos_index, 0)
        self.assertEqual(hsplit_ex.operation, 'hsplit')
        self.assertEqual(
            str(hsplit_ex),
            'Exception raised when performing a "hsplit" operation of the '
            'widget positioned at (0, 0, 1, 2).\n'
            'Positions:\n'
            '(0, 0, 1, 2)\n'
            '(1, 0, 1, 2)'
        )

        vsplit_ex = SplitException(positions, 0, 'vsplit')
        self.assertEqual(vsplit_ex.positions, positions)
        self.assertEqual(vsplit_ex.pos_index, 0)
        self.assertEqual(vsplit_ex.operation, 'vsplit')
        self.assertEqual(
            str(vsplit_ex),
            'Exception raised when performing a "vsplit" operation of the '
            'widget positioned at (0, 0, 1, 2).\n'
            'Positions:\n'
            '(0, 0, 1, 2)\n'
            '(1, 0, 1, 2)'
        )

        delete_ex = SplitException(positions, 0, 'delete')
        self.assertEqual(delete_ex.positions, positions)
        self.assertEqual(delete_ex.pos_index, 0)
        self.assertEqual(delete_ex.operation, 'delete')
        self.assertEqual(
            str(delete_ex),
            'Exception raised when performing a "delete" operation of the '
            'widget positioned at (0, 0, 1, 2).\n'
            'Positions:\n'
            '(0, 0, 1, 2)\n'
            '(1, 0, 1, 2)'
        )

    def test_invalid_operation(self):
        with self.assertRaises(ValueError) as cm:
            SplitException([], 0, 'split')
        self.assertEqual(str(cm.exception), '"operation" must be one of '
                                            "('vsplit', 'hsplit', 'delete')")


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

    def test_split_limit(self):
        self.layout.hsplit(self.ws[0], self.ws[1])
        with self.assertRaises(SplitLimitException):
            self.layout.hsplit(self.ws[0], Widget(2))

    def test_unexpected_error_in_split(self):
        self.layout._get_item_position = types.MethodType(
            lambda *args, **kwargs: 1/0,
            self.layout
        )
        with self.assertRaises(SplitException) as cm:
            self.layout.hsplit(self.ws[0], self.ws[1])
        self.assertEqual(cm.exception.positions, [(0, 0, 2, 2)])
        self.assertEqual(cm.exception.pos_index, 0)
        self.assertEqual(cm.exception.operation, 'hsplit')


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


class HangingWidgetsTestCase(unittest.TestCase):

    def setUp(self):
        self.app = QApplication([])

    #  ┌───┬───────┐
    #  │ 0 │░░░░░░░│
    #  ├───┴───────┤
    #  │░░░░░░░░░░░│
    #  ├───┬───────┤
    #  │░░░│   1   │
    #  └───┴───────┘
    def test_right_space(self):
        layout = get_empty_tiling_layout(3)
        widgets = [Widget(0), Widget(1)]
        layout.addWidget(widgets[0], 0, 0, 1, 1)
        layout.addWidget(widgets[1], 2, 1, 1, 2)
        layout._drop_hanging_widgets(RecBlock(layout, False, 0, 0, 3, 3))
        self.assertEqual(layout._get_item_position(widgets[0], False),
                         (2, 0, 1, 1))
        self.assertEqual(layout._get_item_position(widgets[1], False),
                         (2, 1, 1, 2))

    #  ┌───────┬───┐
    #  │░░░░░░░│ 0 │
    #  ├───────┴───┤
    #  │░░░░░░░░░░░│
    #  ├───────┬───┤
    #  │   1   │░░░│
    #  └───────┴───┘
    def test_left_space(self):
        layout = get_empty_tiling_layout(3)
        widgets = [Widget(0), Widget(1)]
        layout.addWidget(widgets[0], 0, 2, 1, 1)
        layout.addWidget(widgets[1], 2, 0, 1, 2)
        layout._drop_hanging_widgets(RecBlock(layout, False, 0, 0, 3, 3))
        self.assertEqual(layout._get_item_position(widgets[0], False),
                         (2, 2, 1, 1))
        self.assertEqual(layout._get_item_position(widgets[1], False),
                         (2, 0, 1, 2))
    #  ┌───────┬───┐
    #  │░░░░░░░│ 0 │
    #  ├───────┼───┤
    #  │░░░░░░░│ 1 │
    #  ├───────┼───┤
    #  │   2   │░░░│
    #  └───────┴───┘
    def test_not_enough_space(self):
        layout = get_empty_tiling_layout(3)
        widgets = [Widget(0), Widget(1), Widget(2)]
        layout.addWidget(widgets[0], 0, 2, 1, 1)
        layout.addWidget(widgets[1], 1, 2, 1, 1)
        layout.addWidget(widgets[2], 2, 0, 1, 2)
        layout._drop_hanging_widgets(RecBlock(layout, False, 0, 0, 3, 3))
        self.assertEqual(layout._get_item_position(widgets[0], False),
                         (0, 2, 1, 1))
        self.assertEqual(layout._get_item_position(widgets[1], False),
                         (2, 2, 1, 1))
        self.assertEqual(layout._get_item_position(widgets[2], False),
                         (2, 0, 1, 2))

    #  ┌───┬───────┐
    #  │ 0 │░░░░░░░│
    #  ├───┼───────┤
    #  │ 1 │   2   │
    #  ├───┴───────┤
    #  │░░░░░░░░░░░│
    #  └───────────┘
    def test_move_supporters(self):
        layout = get_empty_tiling_layout(3)
        widgets = [Widget(0), Widget(1), Widget(2)]
        layout.addWidget(widgets[0], 0, 0, 1, 1)
        layout.addWidget(widgets[1], 1, 0, 1, 1)
        layout.addWidget(widgets[2], 1, 1, 1, 2)
        layout._drop_hanging_widgets(RecBlock(layout, False, 0, 0, 3, 3))
        self.assertEqual(layout._get_item_position(widgets[0], False),
                         (1, 0, 1, 1))
        self.assertEqual(layout._get_item_position(widgets[1], False),
                         (2, 0, 1, 1))
        self.assertEqual(layout._get_item_position(widgets[2], False),
                         (1, 1, 1, 2))


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


class FillSpacesTestCase(unittest.TestCase):

    def setUp(self):
        self.app = QApplication([])

    #  ┌───┬───────┐
    #  │ 0 │       │
    #  ├───┤   1   │
    #  │ 2 │       │
    #  ├───┴───────┤
    #  │░░░░░░░░░░░│
    #  └───────────┘
    def test_top_block(self):
        layout = get_empty_tiling_layout(3)
        widgets = [Widget(0), Widget(1), Widget(2)]
        layout.addWidget(widgets[0], 0, 0, 1, 1)
        layout.addWidget(widgets[1], 1, 0, 1, 1)
        layout.addWidget(widgets[2], 0, 1, 2, 2)
        layout._fill_spaces(RecBlock(layout, False, 0, 0, 3, 3))
        self.assertEqual(layout._get_item_position(widgets[0], False),
                         (0, 0, 2, 1))
        self.assertEqual(layout._get_item_position(widgets[1], False),
                         (2, 0, 1, 1))
        self.assertEqual(layout._get_item_position(widgets[2], False),
                         (0, 1, 3, 2))

    #  ┌───────────┐
    #  │     0     │
    #  ├───┬───┬───┤
    #  │ 1 │░░░│ 2 │
    #  ├───┘░░░└───┤
    #  │░░░░░░░░░░░│
    #  └───────────┘
    def test_left_block(self):
        layout = get_empty_tiling_layout(3)
        widgets = [Widget(0), Widget(1), Widget(2)]
        layout.addWidget(widgets[0], 0, 0, 1, 3)
        layout.addWidget(widgets[1], 1, 0, 1, 1)
        layout.addWidget(widgets[2], 1, 2, 1, 1)
        layout._fill_spaces(RecBlock(layout, False, 0, 0, 3, 3))
        self.assertEqual(layout._get_item_position(widgets[0], False),
                         (0, 0, 2, 3))
        self.assertEqual(layout._get_item_position(widgets[1], False),
                         (2, 0, 1, 2))
        self.assertEqual(layout._get_item_position(widgets[2], False),
                         (2, 2, 1, 1))

    #  ┌───┬───────┐
    #  │   │   1   │
    #  │ 0 ├───┬───┤
    #  │   │░░░│ 2 │
    #  ├───┘░░░└───┤
    #  │░░░░░░░░░░░│
    #  └───────────┘
    def test_right_block(self):
        layout = get_empty_tiling_layout(3)
        widgets = [Widget(0), Widget(1), Widget(2)]
        layout.addWidget(widgets[0], 0, 0, 2, 1)
        layout.addWidget(widgets[1], 0, 1, 1, 2)
        layout.addWidget(widgets[2], 1, 2, 1, 1)
        layout._fill_spaces(RecBlock(layout, False, 0, 0, 3, 3))
        self.assertEqual(layout._get_item_position(widgets[0], False),
                         (0, 0, 3, 1))
        self.assertEqual(layout._get_item_position(widgets[1], False),
                         (0, 1, 2, 2))
        self.assertEqual(layout._get_item_position(widgets[2], False),
                         (2, 1, 1, 2))

    #  ┌───┬───────┐
    #  │   │   1   │
    #  │ 0 ├───┬───┤
    #  │   │░░░│   │
    #  ├───┼───┤ 2 │
    #  │ 3 │ 4 │   │
    #  └───┴───┴───┘
    def test_no_suitable_block(self):
        layout = get_empty_tiling_layout(3)
        widgets = [Widget(0), Widget(1), Widget(2), Widget(3), Widget(4)]
        layout.addWidget(widgets[0], 0, 0, 2, 1)
        layout.addWidget(widgets[1], 0, 1, 1, 2)
        layout.addWidget(widgets[2], 1, 2, 2, 1)
        layout.addWidget(widgets[3], 2, 0, 1, 1)
        layout.addWidget(widgets[4], 2, 1, 1, 1)
        with self.assertRaises(ImpossibleToBuildBlockException):
            layout._fill_spaces(RecBlock(layout, False, 0, 0, 3, 3))


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


class RecBlockTestCase(unittest.TestCase):

    #  ┌───────┬───────────────────────┐
    #  │       │                       │
    #  │       │            1          │
    #  │   0   │                       │
    #  │       ├───┬───┬───────────────┤
    #  │       │ 2 │░░░│               │
    #  ├───────┴───┴───┤               │
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
        self.layout.addWidget(self.ws[2], 2, 2, 1, 1)
        self.layout.addWidget(self.ws[3], 2, 4, 4, 4)
        self.layout.addWidget(self.ws[4], 3, 0, 5, 4)
        self.layout.addWidget(self.ws[5], 6, 4, 2, 4)

    def test_valid_block(self):
        p =(0, 0, 8, 8)
        block = RecBlock(self.layout, False, *p)
        self.assertEqual((block.i, block.j, block.rowspan, block.colspan), p)

    def test_non_rectangular_blocks(self):
        with self.assertRaises(NonRectangularRecBlockException):
            RecBlock(self.layout, False, 2, 0, 6, 8)
        with self.assertRaises(NonRectangularRecBlockException):
            RecBlock(self.layout, False, 0, 0, 3, 3)
        with self.assertRaises(NonRectangularRecBlockException):
            RecBlock(self.layout, False, 0, 2, 3, 6)
        with self.assertRaises(NonRectangularRecBlockException):
            RecBlock(self.layout, False, 2, 3, 4, 5)

    def test_get_widgets(self):
        self.assertEqual(
            list(RecBlock(self.layout, False, 0, 0, 8, 8).get_widgets()),
            [(self.ws[0], (0, 0, 3, 2)),
             (self.ws[1], (0, 2, 2, 6)),
             (self.ws[2], (2, 2, 1, 1)),
             (self.ws[3], (2, 4, 4, 4)),
             (self.ws[4], (3, 0, 5, 4)),
             (self.ws[5], (6, 4, 2, 4))]
        )

    def test_virtualization(self):
        block = RecBlock(self.layout, False, 0, 0, 8, 8)
        l = self.ws
        self.assertEqual(block._virtualize(),
                         [(l[0], l[0], l[1], l[1], l[1], l[1], l[1], l[1]),
                          (l[0], l[0], l[1], l[1], l[1], l[1], l[1], l[1]),
                          (l[0], l[0], l[2], None, l[3], l[3], l[3], l[3]),
                          (l[4], l[4], l[4], l[4], l[3], l[3], l[3], l[3]),
                          (l[4], l[4], l[4], l[4], l[3], l[3], l[3], l[3]),
                          (l[4], l[4], l[4], l[4], l[3], l[3], l[3], l[3]),
                          (l[4], l[4], l[4], l[4], l[5], l[5], l[5], l[5]),
                          (l[4], l[4], l[4], l[4], l[5], l[5], l[5], l[5])])

    def test_subset_virtualization(self):
        block = RecBlock(self.layout, False, 2, 4, 6, 4)
        self.assertEqual(block._virtualize(),
                         [(self.ws[3], self.ws[3], self.ws[3], self.ws[3]),
                          (self.ws[3], self.ws[3], self.ws[3], self.ws[3]),
                          (self.ws[3], self.ws[3], self.ws[3], self.ws[3]),
                          (self.ws[3], self.ws[3], self.ws[3], self.ws[3]),
                          (self.ws[5], self.ws[5], self.ws[5], self.ws[5]),
                          (self.ws[5], self.ws[5], self.ws[5], self.ws[5])])

    def test_materialization(self):
        block = RecBlock(self.layout, False, 0, 0, 8, 8)
        virtual = block._virtualize()
        self.assertEqual(
            list(RecBlock._materialize_virtual_block(0, 0, virtual)),
            [(w, self.layout._get_item_position(w, False)) for w in self.ws]
        )

    def test_displaced_materialization(self):
        block = RecBlock(self.layout, False, 0, 0, 8, 8)
        virtual = block._virtualize()
        offset = (1, 2)
        expected = [(w, self.layout._get_item_position(w, False))
                    for w in self.ws]
        for i in range(0, len(expected)):
            widget, pos = expected[i]
            expected[i] = (widget, (pos[0] + offset[0], pos[1] + offset[1],
                                    pos[2], pos[3]))
        self.assertEqual(
            list(RecBlock._materialize_virtual_block(*offset, virtual)),
            expected
        )

    def test_shrink_failure(self):
        block = RecBlock(self.layout, False, 0, 0, 8, 8)
        with self.assertRaises(SplitLimitException):
            block.displace_and_resize(0, -5)

    def test_displace_and_resize(self):
        l = self.ws
        block = RecBlock(self.layout, False, 0, 0, 8, 8)
        block.displace_and_resize(4, -4)
        block = RecBlock(self.layout, False, 0, 0, 8, 8)
        self.assertEqual(block._virtualize(),
                         [(None, None, None, None, None, None, None, None),
                          (None, None, None, None, None, None, None, None),
                          (None, None, None, None, None, None, None, None),
                          (None, None, None, None, None, None, None, None),
                          (l[0], l[0], l[1], l[1], l[1], l[1], l[1], l[1]),
                          (l[0], l[0], l[2], None, l[3], l[3], l[3], l[3]),
                          (l[4], l[4], l[4], l[4], l[3], l[3], l[3], l[3]),
                          (l[4], l[4], l[4], l[4], l[5], l[5], l[5], l[5])])
        block.displace_and_resize(-2, 2)
        block = RecBlock(self.layout, False, 0, 0, 8, 8)
        self.assertEqual(block._virtualize(),
                         [(None, None, None, None, None, None, None, None),
                          (None, None, None, None, None, None, None, None),
                          (l[0], l[0], l[1], l[1], l[1], l[1], l[1], l[1]),
                          (l[0], l[0], l[1], l[1], l[1], l[1], l[1], l[1]),
                          (l[0], l[0], l[2], None, l[3], l[3], l[3], l[3]),
                          (l[0], l[0], l[2], None, l[3], l[3], l[3], l[3]),
                          (l[4], l[4], l[4], l[4], l[3], l[3], l[3], l[3]),
                          (l[4], l[4], l[4], l[4], l[5], l[5], l[5], l[5])])


class CriticalBlockTestCase(unittest.TestCase):

    #  ┌───────┬───────┬───────┬───────┬───────┬───────┐
    #  │       │       │       │       │       │   5   │
    #  │   0   │       │       │       │   4   ├───────┤
    #  │       │   1   │   2   │   3   │       │   6   │
    #  ├───────┤       │       │       ├───────┼───────┤
    #  │░░░░░░░│       │       │       │       │   9   │
    #  ├───────┼───────┼───────┼───┬───┤       ├───────┤
    #  │       │       │       │░░░│   │   8   │       │
    #  │  10   │  11   │   7   │░░░│12 │       │  13   │
    #  │       │       │       │░░░│   │       │       │
    #  ├───────┴───────┴───────┴───┴───┴───────┴───────┤
    #  │                                               │
    #  │                      28                       │
    #  │                                               │
    #  ├───────┬───────┬───────┬───┬───┬───────┬───────┤
    #  │       │       │       │░░░│   │       │       │
    #  │  14   │  15   │  16   │░░░│19 │       │  18   │
    #  │       │       │       │░░░│   │  17   │       │
    #  ├───────┼───────┼───────┼───┴───┤       ├───────┤
    #  │       │░░░░░░░│       │       │       │  22   │
    #  │       ├───────┤       │       ├───────┼───────┤
    #  │  23   │       │  24   │  21   │       │  26   │
    #  │       │  20   │       │       │  25   ├───────┤
    #  │       │       │       │       │       │  27   │
    #  └───────┴───────┴───────┴───────┴───────┴───────┘
    def setUp(self):
        self.app = QApplication([])
        self.layout = get_empty_tiling_layout(12)
        self.ws = [Widget(i) for i in range(29)]
        self.layout.addWidget(self.ws[0], 0, 0, 2, 2)
        self.layout.addWidget(self.ws[1], 0, 2, 3, 2)
        self.layout.addWidget(self.ws[2], 0, 4, 3, 2)
        self.layout.addWidget(self.ws[3], 0, 6, 3, 2)
        self.layout.addWidget(self.ws[4], 0, 8, 2, 2)
        self.layout.addWidget(self.ws[5], 0, 10, 1, 2)
        self.layout.addWidget(self.ws[6], 1, 10, 1, 2)
        self.layout.addWidget(self.ws[7], 3, 4, 2, 2)
        self.layout.addWidget(self.ws[8], 2, 8, 3, 2)
        self.layout.addWidget(self.ws[9], 2, 10, 1, 2)
        self.layout.addWidget(self.ws[10], 3, 0, 2, 2)
        self.layout.addWidget(self.ws[11], 3, 2, 2, 2)
        self.layout.addWidget(self.ws[12], 3, 7, 2, 1)
        self.layout.addWidget(self.ws[13], 3, 10, 2, 2)
        self.layout.addWidget(self.ws[14], 7, 0, 2, 2)
        self.layout.addWidget(self.ws[15], 7, 2, 2, 2)
        self.layout.addWidget(self.ws[16], 7, 4, 2, 2)
        self.layout.addWidget(self.ws[17], 7, 8, 3, 2)
        self.layout.addWidget(self.ws[18], 7, 10, 2, 2)
        self.layout.addWidget(self.ws[19], 7, 7, 2, 1)
        self.layout.addWidget(self.ws[20], 10, 2, 2, 2)
        self.layout.addWidget(self.ws[21], 9, 6, 3, 2)
        self.layout.addWidget(self.ws[22], 9, 10, 1, 2)
        self.layout.addWidget(self.ws[23], 9, 0, 3, 2)
        self.layout.addWidget(self.ws[24], 9, 4, 3, 2)
        self.layout.addWidget(self.ws[25], 10, 8, 2, 2)
        self.layout.addWidget(self.ws[26], 10, 10, 1, 2)
        self.layout.addWidget(self.ws[27], 11, 10, 1, 2)
        self.layout.addWidget(self.ws[28], 5, 0, 2, 12)

    def test_valid_block(self):
        p =(7, 8, 5, 4)
        block = CriticalBlock(self.layout, False, *p)
        self.assertEqual((block.i, block.j, block.rowspan, block.colspan), p)

    def test_invalid_block(self):
        p =(7, 6, 5, 6)
        with self.assertRaises(EmptySpaceInCriticalBlockException):
            CriticalBlock(self.layout, False, *p)

    def test_build_up(self):
        with self.assertRaises(ImpossibleToBuildBlockException):
            CriticalBlock.build_from_point(self.layout, False, 12, 0, 4, True)
        self.assertEqual(
            CriticalBlock.build_from_point(self.layout, False, 12, 4, 4, True),
            CriticalBlock(self.layout, False, 9, 4, 3, 4)
        )
        self.assertEqual(
            CriticalBlock.build_from_point(self.layout, False, 12, 8, 4, True),
            CriticalBlock(self.layout, False, 7, 8, 5, 4)
        )
        self.assertEqual(
            CriticalBlock.build_from_point(self.layout, False, 5, 0, 4, True),
            CriticalBlock(self.layout, False, 3, 0, 2, 4)
        )
        with self.assertRaises(ImpossibleToBuildBlockException):
            CriticalBlock.build_from_point(self.layout, False, 5, 4, 4, True)
        self.assertEqual(
            CriticalBlock.build_from_point(self.layout, False, 5, 8, 4, True),
            CriticalBlock(self.layout, False, 0, 8, 5, 4)
        )

    def test_build_down(self):
        with self.assertRaises(ImpossibleToBuildBlockException):
            CriticalBlock.build_from_point(self.layout, False, 0, 0, 4, False)
        self.assertEqual(
            CriticalBlock.build_from_point(self.layout, False, 0, 4, 4, False),
            CriticalBlock(self.layout, False, 0, 4, 3, 4)
        )
        self.assertEqual(
            CriticalBlock.build_from_point(self.layout, False, 0, 8, 4, False),
            CriticalBlock(self.layout, False, 0, 8, 5, 4)
        )
        self.assertEqual(
            CriticalBlock.build_from_point(self.layout, False, 7, 0, 4, False),
            CriticalBlock(self.layout, False, 7, 0, 2, 4)
        )
        with self.assertRaises(ImpossibleToBuildBlockException):
            CriticalBlock.build_from_point(self.layout, False, 7, 4, 4, False)
        self.assertEqual(
            CriticalBlock.build_from_point(self.layout, False, 7, 8, 4, False),
            CriticalBlock(self.layout, False, 7, 8, 5, 4)
        )


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
