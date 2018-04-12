from PyQt5.QtWidgets import QGridLayout, QWidget
from functools import reduce
from math import gcd as gcd_
import itertools
import pdb


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
        old_widget_pos = self._get_item_position(old_widget, transpose)
        ib = self._get_independent_block(old_widget, transpose)
        index = ib[0]
        top_widgets = []
        while index < sum(ib):
           w = self._item_at_position(0, index, transpose).widget()
           top_widgets.append(w)
           index += self._get_item_position(w, transpose)[2]

        max_height = max(self._get_supporters(widget, False, transpose).height
                         for widget in top_widgets)
        top_supporters = self._get_supporters(old_widget, True, transpose)
        bottom_supporters = self._get_supporters(old_widget, False, transpose)

        splitting_longest_support_line = (max_height == top_supporters.height +
                                          bottom_supporters.height - 1)

        if splitting_longest_support_line:
            new_height = self._row_count(transpose) // (max_height + 1)

            if new_height < 1:
                raise SplitLimitException()

            rem = self._row_count(transpose) % (max_height + 1)
            remspans = [(0, rem)] * self._column_count(transpose)
            longest_branches_widgets = (
                top_supporters.longest_branches_nodes().union(
                     bottom_supporters.longest_branches_nodes()
                )
            )
            widgets = sorted(
                ((widget, self._get_item_position(widget, transpose))
                 for widget in longest_branches_widgets),
                key=lambda w: w[1][0]
            )
            if put_before:
                widgets.insert(widgets.index((old_widget, old_widget_pos)),
                               (new_widget, old_widget_pos))
            else:
                widgets.insert(widgets.index((old_widget, old_widget_pos)) + 1,
                               (new_widget, old_widget_pos))

            for widget, old_pos in widgets:
                self.removeWidget(widget)
                row, curr_rem = max(
                    remspans[old_pos[1]:old_pos[1] + old_pos[3]]
                )
                height = new_height + (1 if curr_rem else 0)
                self._add_widget(widget, row, old_pos[1], height,
                                 old_pos[3], transpose)
                for col in range(old_pos[1], old_pos[1] + old_pos[3]):
                    remspans[col] = (row + height, max(0, curr_rem - 1))

            empty_block = self._find_empty_block(transpose)
            adjusted = longest_branches_widgets.union(new_widget)
            while empty_block:
                # Figure out where to start searching our critical block and in
                # what directions
                top_item = self._item_at_position(empty_block[0] - 1,
                                                  empty_block[1],
                                                  transpose)
                left_item = self._item_at_position(empty_block[0],
                                                   empty_block[1] - 1,
                                                   transpose)
                up = top_item is None or top_item.widget() not in adjusted
                left = left_item is None or left_item.widget() not in adjusted
                i = empty_block[0] + (0 if up else empty_block[2])
                j = empty_block[1] + (empty_block[3] if left else 0)
                critical_block = self._find_critical_block(i, j, up, left,
                                                           transpose)
                # resize block
                adjusted = adjusted.union(critical_block)
        else:
            raise NotImplementedError

    def _get_independent_block(self, widget, transpose):
        pos = self._get_item_position(widget, transpose)
        expected_height = self._row_count(transpose)

        left = pos[1]
        found_left_limit = False
        while not found_left_limit:
            border_height = (
                self._get_border_height(pos[0], left, False,  transpose)
                + self._get_border_height(pos[0], left, True,  transpose)
            )
            if border_height == expected_height:
                found_left_limit = True
            else:
                left_widget = self._item_at_position(pos[0], left - 1,
                                                     transpose).widget()
                left = self._get_item_position(left_widget, transpose)[1]

        right = pos[1] + pos[3]
        found_right_limit = False
        while not found_right_limit:
            border_height = (
                self._get_border_height(pos[0], right, False, transpose)
                + self._get_border_height(pos[0], right, True, transpose)
            )
            if border_height == expected_height:
                found_right_limit = True
            else:
                right_widget = self._item_at_position(pos[0], right,
                                                      transpose).widget()
                right_widget_pos = self._get_item_position(right_widget,
                                                           transpose)
                right = right_widget_pos[1] + right_widget_pos[3]

        return left, right - left

    def _get_border_height(self, row, col, up, transpose):
        rows = self._row_count(transpose)
        if col in (0, self._column_count(transpose)):
            return row if up else (rows - row)
        elif row == 0 and up or row == rows and not up:
            return 0

        index = row
        reached_end = False
        while not reached_end:
            widget = self._item_at_position(index - 1 if up else index,
                                            col, transpose).widget()
            pos = self._get_item_position(widget, transpose)
            if pos[1] == col:
                index = pos[0] if up else pos[0] + pos[2]
                reached_end = index == 0 if up else index == rows
            else:
                reached_end = True

        return row - index if up else index - row

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
        return TreeNode(widget, [self._get_supporters(w, before, transpose)
                                 for w in supporters])

    def _find_empty_block(self, transpose):
        """Finds a block made entirely of empty space.

        Returns a tuple in the form of (i, j, rowspan, colspan). the block is
        of the largest possible size.

        Args:
            transpose: If True, will behave as if the grid was transposed.
        """
        i = -1
        found = False
        while not found and i < self._row_count(transpose):
            i += 1
            j = 0
            while not found and j < self._column_count(transpose):
                item = self._item_at_position(i, j, transpose)
                if item is None:
                    found = True
                else:
                    pos = self._get_item_position(item.widget(), transpose)
                    j += pos[3]

        if not found:
            return None

        rowspan, colspan = 0, 0
        reached_end = False
        while not reached_end:
            rowspan += 1
            reached_end = (i + rowspan >= self._row_count(transpose) or
                           self._item_at_position(i + rowspan, j,
                                                  transpose) is not None)
        reached_end = False
        while not reached_end:
            colspan += 1
            reached_end = (j + colspan >= self._column_count(transpose) or
                           self._item_at_position(i, j + colspan,
                                                  transpose) is not None)

        return i, j, rowspan, colspan

    def _find_critical_block(self, i, j, up, left, transpose):
        """Finds a critical block from the specified starting point.

        A critical block is a group of one or more widgets that form a
        rectangle that can be grown as a whole, with each widget growing in the
        same proportion.
        Args:
            i: Starting row.
            j: Starting column.
            up: If True, go up to find new widgets, else go down.
            left: If True, go left to find new widgets, else go right.
            transpose: If True, will behave as if the grid was transposed.
        """
        first_border = self._get_border_height(i, j, up, transpose)
        is_rectangular = False
        pivot = j
        while not is_rectangular:
            neighbor = self._item_at_position(i - (1 if up else 0),
                                              pivot - (1 if left else 0),
                                              transpose).widget()
            neighbor_pos = self._get_item_position(neighbor, transpose)
            neighbor_border = self._get_border_height(
                i,
                neighbor_pos[1] + (0 if left else neighbor_pos[3]),
                up,
                transpose
            )
            if neighbor_border >= first_border:
                is_rectangular = True
            pivot += (-1 if left else 1) * neighbor_pos[3]

        i, j, rowspan, colspan = (i - (first_border if up else 0),
                                  neighbor_pos[1] if left else j,
                                  first_border,
                                  abs(pivot - j))
        assert self._is_rectangular(i, j, rowspan, colspan, transpose)
        return i, j, rowspan, colspan

    def _is_rectangular(self, i, j, rowspan, colspan, transpose):
        # TODO: refactor to avoid 4 whiles
        try:
            # Left edge
            index = i
            reached_end = False
            while not reached_end:
                widget = self._item_at_position(index, j, transpose).widget()
                pos = self._get_item_position(widget, transpose)
                assert pos[1] == j
                index += pos[2]
                reached_end = index >= i + rowspan

            # Top edge
            index = j
            reached_end = False
            while not reached_end:
                widget = self._item_at_position(i, index, transpose).widget()
                pos = self._get_item_position(widget, transpose)
                assert pos[0] == i
                index += pos[3]
                reached_end = index >= j + colspan

            # Right edge
            index = i
            reached_end = False
            while not reached_end:
                widget = self._item_at_position(index, j + colspan - 1,
                                                transpose).widget()
                pos = self._get_item_position(widget, transpose)
                assert pos[1] + pos[3] == j + colspan
                index += pos[2]
                reached_end = index >= i + rowspan

            # Bottom edge
            index = j
            reached_end = False
            while not reached_end:
                widget = self._item_at_position(i + rowspan - 1,
                                                index, transpose).widget()
                pos = self._get_item_position(widget, transpose)
                assert pos[0] + pos[2] == i + rowspan
                index += pos[3]
                reached_end = index >= j + colspan
            return True
        except (AttributeError, AssertionError):
            return False


class TreeNode:

    def __init__(self, value, children=[]):
        self.value = value
        self.children = children
        self._height = 1 + max((child.height for child in self.children),
                               default=0)

    @property
    def height(self):
        return self._height

    def longest_branches_nodes(self):
        return {self.value}.union(*(child.longest_branches_nodes()
                                    for child in self.children
                                    if child.height == self.height - 1))
