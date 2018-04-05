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


class SplitLimitException(Exception):
    pass


class QTilingLayout(QGridLayout):

    def __init__(self, widget, *args, max_span=60, **kwargs):
        super().__init__(*args, **kwargs)
        self.max_span = max_span
        self._add_widget(widget, 0, 0, self.max_span, self.max_span, False)

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

    def hsplit(self, old_widget, new_widget, put_before=False):
        self._split(old_widget, new_widget, put_before, False)

    def vsplit(self, old_widget, new_widget, put_before=False):
        self._split(old_widget, new_widget, put_before, True)

    def _split(self, old_widget, new_widget, put_before, transpose):
        # 1- Get the independent block of the splitted widget
        # 2- Get the longest support line(s) of the independent block
        # 3- Is the splitted widget in one of those lines?
        # 3.1 - If so, we must take the whole line out and place all the
        #       widgets one at a time using a new calculated height and
        #       remainder. Other widgets in the independent block must be
        #       shrinked or grown.
        # 3.2 - If not, we must take the critical block of the widget and
        #       resize all the widgets in it to make room for the new widget.
        ib = self._get_independent_block(old_widget, transpose)
        index = ib[0]
        top_widgets = []
        while index < sum(ib):
           w = self._item_at_position(0, index, transpose).widget()
           top_widgets.append(w)
           index += self._get_item_position(w, transpose)[2]

        support_lines = list(itertools.chain(*(
            self._get_support_lines(self._get_supporters(widget, False,
                                                              transpose))
            for widget in top_widgets
        )))
        max_height = max(len(line) for line in support_lines)
        longest_support_lines = [line for line in support_lines
                                 if len(line) == max_height]
        splitting_longest_support_line = any(old_widget in line for line
                                             in longest_support_lines)

        if splitting_longest_support_line:
            done = set()
            new_height = self._row_count(transpose) // (max_height + 1)

            if new_height < 1:
                raise SplitLimitException()

            rem = self._row_count(transpose) % (max_height + 1)
            modspans = [(0, rem)] * self._column_count(transpose)
            widgets = (widget
                       for line in longest_support_lines
                       for widget in line)
            for widget in widgets:
                if widget in done:
                    continue

                old_pos = self._get_item_position(widget, transpose)
                self.removeWidget(widget)
                if widget is old_widget:
                    widget1, widget2 = ((new_widget, old_widget) if put_before
                                        else (old_widget, new_widget))
                    modspans = self._append_widget(widget1, modspans,
                                                   old_pos, new_height,
                                                   transpose)
                    modspans = self._append_widget(widget2, modspans,
                                                   old_pos, new_height,
                                                   transpose)
                else:
                    modspans = self._append_widget(widget, modspans,
                                                   old_pos, new_height,
                                                   transpose)
                done.add(widget)
        else:
            raise NotImplementedError

    def _append_widget(self, widget, modspans, old_pos, new_height, transpose):
        curr_row, curr_rem = modspans[old_pos[1]]
        height = new_height + (1 if curr_rem else 0)
        self._add_widget(widget, curr_row, old_pos[1], height, old_pos[3],
                         transpose)

        updated_modspans = list(modspans)
        for col in range(old_pos[1], old_pos[1] + old_pos[3]):
            updated_modspans[col] = (curr_row + height, max(0, curr_rem - 1))

        return updated_modspans

    def _get_independent_block(self, widget, transpose):
        pos = self._get_item_position(widget, transpose)
        expected_height = self._row_count(transpose)

        left = pos[1]
        found_left_limit = False
        while not found_left_limit:
            border_height = self._get_border_height(pos[0], left, transpose)
            if border_height == expected_height:
                found_left_limit = True
            else:
                left_widget = self._item_at_position(pos[0], left - 1,
                                                     transpose).widget()
                left = self._get_item_position(left_widget, transpose)[1]

        right = pos[1] + pos[3]
        found_right_limit = False
        while not found_right_limit:
            border_height = self._get_border_height(pos[0], right, transpose)
            if border_height == expected_height:
                found_right_limit = True
            else:
                right_widget = self._item_at_position(pos[0], right,
                                                      transpose).widget()
                right_widget_pos = self._get_item_position(right_widget,
                                                           transpose)
                right = right_widget_pos[1] + right_widget_pos[3]

        return left, right - left

    def _get_border_height(self, row, col, transpose):
        if col in (0, self._column_count(transpose)):
            return self._row_count(transpose)

        widget = self._item_at_position(row, col, transpose).widget()
        pos = self._get_item_position(widget, transpose)
        assert pos[1] == col

        top, bottom = pos[0], pos[0] + pos[2] - 1

        reached_top = top == 0
        while not reached_top:
            tmp_widget = self._item_at_position(top - 1, col,
                                                transpose).widget()
            tmp_pos = self._get_item_position(tmp_widget, transpose)
            if tmp_pos[1] == col:
                top = tmp_pos[0]
                reached_top = top == 0
            else:
                reached_top = True

        reached_bottom = bottom == self._row_count(transpose) - 1
        while not reached_bottom:
            tmp_widget = self._item_at_position(bottom + 1, col,
                                                transpose).widget()
            tmp_pos = self._get_item_position(tmp_widget, transpose)
            if tmp_pos[1] == col:
                bottom = tmp_pos[0] + tmp_pos[2] - 1
                reached_bottom = bottom == self._row_count(transpose) - 1
            else:
                reached_bottom = True

        return bottom - top + 1

    def _get_supporters(self, widget, before, transpose):
        """Returns a tree of "support" widgets for the specified widget.

        A support widget is a widget that is (directly or indirectly) "pushed"
        by the specified widget when it grows.

        Args:
            block: The widget (or position) for which to find supporters.
            before: The direction in which to find supporters (True for up,
                    False for down).
            transpose: If True, will behave as if the grid was transposed.
        """
        supporters = []
        pos = self._get_item_position(widget, transpose)
        pivot = pos[0] - 1 if before else pos[0] + pos[2]
        col = pos[1]
        upper_limit = self._row_count(transpose)
        within_limits = (pivot >= 0) if before else (pivot < upper_limit)
        if within_limits:
            while col < pos[1] + pos[3]:
                supporter = self._item_at_position(pivot, col,
                                                   transpose).widget()
                supporters.append(supporter)
                supporter_pos = self._get_item_position(supporter, transpose)
                col = supporter_pos[1] + supporter_pos[3]
        return widget, [self._get_supporters(w, before, transpose)
                        for w in supporters]

    def _get_support_lines(self, tree, ancestors=[]):
        if tree[1]:
            for supporter in tree[1]:
                yield from self._get_support_lines(supporter,
                                                   ancestors + [tree[0]])
        else:
            yield ancestors + [tree[0]]
