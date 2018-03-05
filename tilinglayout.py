from PyQt5.QtWidgets import QGridLayout, QWidget
from bisect import bisect
from functools import reduce
from math import gcd as gcd_
import itertools
import pdb


def gcd(*numbers):
    """Return the greatest common divisor of the given integers"""
    return reduce(gcd_, numbers)


def lcm(*numbers):
    """Return lowest common multiple."""
    return reduce(lambda a, b: (a * b) // gcd_(a, b), numbers, 1)


class QTilingLayout(QGridLayout):

    MAX_SPAN = 16

    def __init__(self, widget, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._add_widget(widget, 0, 0, self.MAX_SPAN, self.MAX_SPAN, False)

    def _add_widget(self, widget, row, col, rowspan, colspan, transpose):
        """Invokes QGridLayout.addWidget on a possibly transposed grid.

        Args:
            widget: Same as in QGridLayout.addWidget.
            row: Same as in QGridLayout.addWidget.
            col: Same as in QGridLayout.addWidget.
            rowspan: Same as in QGridLayout.addWidget.
            colspan: Same as in QGridLayout.addWidget.
            transpose: If True, will behave as if the grid was transposed.
        """
        if not transpose:
            return self.addWidget(widget, row, col, rowspan, colspan)
        else:
            return self.addWidget(widget, col, row, colspan, rowspan)

    def _column_count(self, transpose):
        """Invokes QGridLayout.columnCount on a possibly transposed grid.

        Args:
            transpose: If True, will behave as if the grid was transposed.
        """
        if not transpose:
            return self.columnCount()
        else:
            return self.rowCount()

    def _get_item_position(self, widget, transpose):
        """Invokes QGridLayout.getItemPosition on a possibly transposed grid.

        Args:
            widget: The widget whose position will be returned.
            transpose: If True, will behave as if the grid was transposed.
        """
        index = self.indexOf(widget)
        if index < 0:
            raise ValueError('QGridLayout.indexOf(widget) returned -1')
        else:
            pos = self.getItemPosition(index)
            return pos if not transpose else (pos[1], pos[0], pos[3], pos[2])

    def _item_at_position(self, row, col, transpose):
        """Invokes QGridLayout.itemAtPosition on a possibly transposed grid.

        Args:
            row: Same as in QGridLayout.itemAtPosition.
            col: Same as in QGridLayout.itemAtPosition.
            transpose: If True, will behave as if the grid was transposed.
        """
        if not transpose:
            return self.itemAtPosition(row, col)
        else:
            return self.itemAtPosition(col, row)

    def _row_count(self, transpose):
        """Invokes QGridLayout.rowCount on a possibly transposed grid.

        Args:
            transpose: If True, will behave as if the grid was transposed.
        """
        if not transpose:
            return self.rowCount()
        else:
            return self.columnCount()

    def hsplit(self, old_widget, new_widget, put_after=True):
        self._split(old_widget, new_widget, False, put_after=put_after)

    def vsplit(self, old_widget, new_widget, put_after=True):
        self._split(old_widget, new_widget, True, put_after=put_after)

    def _split(self, old_widget, new_widget, transpose, put_after):
        curr_pos = self._get_item_position(old_widget, transpose)
        span = curr_pos[2]
        if span % 2 != 0:
            print("Can't split anymore")
            return
        self.removeWidget(old_widget)
        old_widget_pos = (curr_pos[0], curr_pos[1], curr_pos[2] / 2,
                          curr_pos[3])
        new_widget_pos = (curr_pos[0] + (span / 2 ), curr_pos[1],
                          curr_pos[2] / 2, curr_pos[3])
        self._add_widget(old_widget if put_after else new_widget,
                         *old_widget_pos, transpose)
        self._add_widget(new_widget if put_after else old_widget,
                         *new_widget_pos, transpose)
