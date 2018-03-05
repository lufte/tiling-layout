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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

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
        self._split(old_widget, new_widget, True, put_before=put_before)

    def vsplit(self, old_widget, new_widget, put_before=False):
        self._split(old_widget, new_widget, False, put_before=put_before)

    def _tmux_split(self, old_widget, new_widget, horizontal,
                    put_before=False):
        transpose = not horizontal
        curr_pos = self._get_item_position(old_widget, transpose)
        span = curr_pos[2]
        if span % 2 != 0:
            self._multiply_spans(2, transpose)
            curr_pos = self._get_item_position(old_widget, transpose)
            span = curr_pos[2]
        self.removeWidget(old_widget)
        old_widget_pos = (curr_pos[0], curr_pos[1], curr_pos[2] / 2,
                          curr_pos[3])
        new_widget_pos = (curr_pos[0] + (span / 2 ), curr_pos[1],
                          curr_pos[2] / 2, curr_pos[3])
        self._add_widget(old_widget, *old_widget_pos, transpose)
        self._add_widget(new_widget, *new_widget_pos, transpose)

    def _split(self, old_widget, new_widget, horizontal, put_before=False):
        """Splits old_widget and inserts new_widget in the available space.

        This method (and all other custom methods used in here) works assuming
        an horizontal split. If the split is vertical, the layout has special
        replacements for QGridLayout's built-in methods that allow passing an
        extra argument indicating that the grid is transposed. This allows us
        to implement the splitting algorithm only for the horizontal case and
        make it work also for the vertical case without changes.

        Args:
            old_widget: The widget to be splitted.
            new_widget: The widget to insert in the new available space.
            horizontal: True if splitting in the X axis, False for Y.
            put_before: True if new_widget is to be put before old_widget.
        """
        transpose = not horizontal
        curr_pos = self._get_item_position(old_widget, transpose)
        span = curr_pos[2]
        prev_supporters = self._get_support_widgets(old_widget, True,
                                                    transpose)
        next_supporters = self._get_support_widgets(old_widget, False,
                                                    transpose)
        supporters = prev_supporters.union(next_supporters)
        max_span = max(
            (self._get_item_position(w, transpose)[2]
            for w in supporters
        )) if supporters else 0

        if span >= max_span * 2:
            if span % 2 != 0:
                self._multiply_spans(2, transpose)
                curr_pos = self._get_item_position(old_widget, transpose)
                span = curr_pos[2]
            self.removeWidget(old_widget)
            old_widget_pos = (curr_pos[0], curr_pos[1], curr_pos[2] / 2,
                              curr_pos[3])
            new_widget_pos = (curr_pos[0] + (span / 2 ), curr_pos[1],
                              curr_pos[2] / 2, curr_pos[3])
            self._add_widget(old_widget, *old_widget_pos, transpose)
            self._add_widget(new_widget, *new_widget_pos, transpose)
        else:
            # TODO: optimize this, we iterate supporters like a thousand times
            # TODO: using the old_widget's span and leaving everything else
            # unotuched is not enough. if the new_widget's span does not equal
            # the support line's minimum, we should adjust some of the other
            # sizes as well
            widgets_to_displace = [
                (widget, self._get_item_position(widget, transpose))
                for widget in next_supporters
            ]
            for widget in next_supporters:
                self.removeWidget(widget)
            for widget, pos in widgets_to_displace:
                new_pos = (pos[0] + span, pos[1], pos[2], pos[3])
                self._add_widget(widget, *new_pos, transpose)
            new_widget_pos = (curr_pos[0] + span, curr_pos[1], curr_pos[2],
                              curr_pos[3])
            self._add_widget(new_widget, *new_widget_pos, transpose)
            adjust = True
            # pdb.set_trace()
            if adjust:
                #self._adjust_sizes(transpose)
                self._adjust_sizes2(supporters, transpose)

    def _get_support_widgets(self, block, before, transpose, level=None):
        """Returns a set of "support" widgets for the specified widget.

        A support widget is a widget that is (directly or indirectly) "pushed"
        by the specified widget when it grows.

        Args:
            block: The widget (or position) for which to find supporters.
            before: The direction in which to find supporters (True for up,
                    False for down).
            transpose: If True, will behave as if the grid was transposed.
            level: How many levels of recursion (support widgets of the support
                   widgets) to process before returning. If None, keep looking
                   for support widgets until the end of the grid.
        """
        supporters = set()
        pos = self._get_item_position(block, transpose) \
              if isinstance(block, QWidget) else block
        pivot = pos[0] - 1 if before else pos[0] + pos[2]
        start = pos[1]
        end = pos[1] + pos[3]
        upper_limit = self._row_count(transpose)
        within_limits = (pivot >= 0) if before else (pivot < upper_limit)
        if within_limits:
            for index in range(start, end):
                item = self._item_at_position(pivot, index, transpose)
                if item:  # this function can be called in the resizing process
                    supporters.add(item.widget())
        if level == 0:
            return supporters
        else:
            next_level = None if level is None else level - 1
            return supporters.union(
                *(self._get_support_widgets(w, before, transpose, level)
                  for w in supporters)
            )

    def _adjust_sizes2(self, support_widgets, transpose):
        empty_block = self._find_empty_block(transpose)
        if empty_block:
            critical_block = self._find_critical_block(empty_block,
                                                       support_widgets,
                                                       transpose)
            widgets_in_block = self._get_widgets_in_block(*critical_block,
                                                         transpose)

            height = critical_block[2]
            new_height = height + empty_block[2]
            denom = height // gcd(height, new_height)
            non_divisible_spans = set(
                self._get_item_position(w, transpose)[2]
                for w in widgets_in_block
                if self._get_item_position(w, transpose)[2] % denom != 0
            )

            if non_divisible_spans:
                factor = lcm(denom, *non_divisible_spans)
                self._multiply_spans(factor, transpose)
                height *= factor
                new_height *= factor
                critical_block = (
                    critical_block[0] * factor,
                    critical_block[1],
                    critical_block[2] * factor,
                    critical_block[3]
                )
                empty_block = (
                    empty_block[0] * factor,
                    empty_block[1],
                    empty_block[2] * factor,
                    empty_block[3]
                )

            critical_block_bottom_supporters = self._get_support_widgets(
                critical_block,
                False,
                transpose
            )
            supporters_cache = []
            for supporter in critical_block_bottom_supporters:
                pos = self._get_item_position(supporter, transpose)
                pos = (pos[0] + empty_block[2], pos[1], pos[2], pos[3])
                supporters_cache.append((supporter, pos))
                self.removeWidget(supporter)
            for supporter, pos in supporters_cache:
                self._add_widget(supporter, *pos, transpose)

            critical_block_top_supporters = self._get_support_widgets(
                critical_block,
                True,
                transpose
            )
            self._multiply_spans(new_height / height, transpose,
                                 widgets_in_block)
            new_supporters = support_widgets.union(
                widgets_in_block,
                critical_block_bottom_supporters,
                critical_block_top_supporters
            )
            self._adjust_sizes2(new_supporters, transpose)

    def _get_widgets_in_block(self, row, col, rowspan, colspan, transpose):
        widgets = set()
        for i in range(row, row + rowspan):
            for j in range(col, col + colspan):
                item = self._item_at_position(i, j, transpose)
                if item:
                    widgets.add(item.widget())
        return widgets

    def _find_empty_block(self, transpose):
        """Finds a block made entirely of empty space.

        Returns a tuple in the form of (i, j, rowspan, colspan). the block is
        of the largest possible size.

        Args:
            transpose: If True, will behave as if the grid was transposed.
        """
        positions = (
            (row, col)
            for row in
            range(0, self._row_count(transpose))
            for col in
            range(0, self._column_count(transpose))
        )

        empty_block_start = None
        for pos in positions:
            item = self._item_at_position(*pos, transpose)
            if item is None:
                empty_block_start = pos
                break

        if empty_block_start:
            # We know where it starts, now find its dimensions
            rowspan = colspan = 1
            for i in range(empty_block_start[0] + 1,
                           self._row_count(transpose)):
                if not self._item_at_position(i, empty_block_start[1],
                                              transpose):
                    rowspan += 1
                else:
                    break
            for j in range(empty_block_start[1] + 1,
                           self._column_count(transpose)):
                if not self._item_at_position(empty_block_start[0], j,
                                              transpose):
                    colspan += 1
                else:
                    break
            return (*empty_block_start, rowspan, colspan)
        else:
            # No empty blocks
            return None

    def _find_critical_block(self, empty_block, excluded_widgets, transpose):
        """Finds a critical block to grow and fill the empty space.

        A critical block is a group of one or more widgets that form a
        rectangle that can be grown as a whole, with each widget growing in the
        same proportion.

        Args:
            empty_block: The position of the empty block in the form
                         (i, j, rowspan, colspan).
            transpose: If True, will behave as if the grid was transposed.
            excluded_widgets: Set of widgets which can't grow so they must
                              not be considered for filling empty spaces.
        """
        # Move up on each side until one of the ends hits either the end of the
        # grid or a support widget. The side with the shortest distance is our
        # pivot, and we can grow the other end horizontally until we can reach
        # the same distance vertically.
        bottom_left = self._item_at_position(empty_block[0] - 1,
                                             empty_block[1],
                                             transpose).widget()
        bottom_left_pos = self._get_item_position(bottom_left, transpose)
        left_height = self._get_edge_height(bottom_left, True, transpose)
        top_left = self._item_at_position(
            bottom_left_pos[0] + bottom_left_pos[2] - left_height - 1,
            bottom_left_pos[1],
            transpose
        )
        top_left = top_left and top_left.widget()

        bottom_right = self._item_at_position(
            empty_block[0] - 1,
            empty_block[1] + empty_block[3] - 1,
            transpose
        ).widget()
        bottom_right_pos = self._get_item_position(bottom_right, transpose)
        right_height = self._get_edge_height(bottom_right, False, transpose)
        top_right = self._item_at_position(
            bottom_right_pos[0] + bottom_right_pos[2] - right_height - 1,
            bottom_right_pos[1] + bottom_right_pos[3] - 1,
            transpose
        )
        top_right = top_right and top_right.widget()

        is_rectangular = False
        if not top_left and not top_right:
            # We reached the end of the grid on both sides, so we already have
            # our critical block
            is_rectangular = grow_right = True
        elif not top_left and top_right in excluded_widgets:
            grow_right = False
        elif not top_left and top_right not in excluded_widgets:
            grow_right = True
        elif not top_right and top_left in excluded_widgets:
            grow_right = True
        elif not top_right and top_left not in excluded_widgets:
            grow_right = False
        elif top_left not in excluded_widgets:
            grow_right = False
        elif top_right not in excluded_widgets:
            grow_right = True
        elif left_height == right_height:
            # Both sides hit the same support widget
            is_rectangular = grow_right = True
        else:
            # Both sides hit different support widgets, the shortest side is
            # the pivot
            grow_right = left_height < right_height

        height = left_height if grow_right else right_height
        if not is_rectangular and grow_right:
            start = bottom_left_pos[1]
            end = bottom_left_pos[1] + bottom_left_pos[3] - 1
        elif not is_rectangular and not grow_right:
            start = bottom_right_pos[1] + bottom_right_pos[3] - 1
            end = bottom_right_pos[1]
        else:
            start = bottom_left_pos[1]
            end = bottom_right_pos[1] + bottom_right_pos[3] - 1

        # Finally, move along the X axis (going right if grow_right==True, left
        # otherwise) and grow the block until it's rectangular
        while not is_rectangular:
            neighbor = self._item_at_position(empty_block[0] - 1, end,
                                              transpose).widget()
            neighbor_height = self._get_edge_height(neighbor, not grow_right,
                                                    transpose)
            if neighbor_height >= height:
                is_rectangular = True
            else:
                neighbor_pos = self._get_item_position(neighbor, transpose)
                end += (1 if grow_right else -1) * neighbor_pos[3]
        return (
            empty_block[0] - height,
            min(start, end),
            height,
            abs(end - start) + 1
        )

    def _get_edge_height(self, widget, left, transpose):
        """Calculates the height of a widget's "edge".

        Given a widget and a side (left==True or left==False), this function
        returns the widget's height plus the height of all consecutive widgets
        on top of it as long as they are aligned (on the proper side) with it.
        It can be thought as following the line on the specified side of the
        widget upwards until it reaches either the end of the grid or another
        widget in the middle.
        """
        pos = self._get_item_position(widget, transpose)
        height = pos[2]
        floor = pos[0] + pos[2] - 1
        reached_top = False
        while not reached_top:
            up_item = self._item_at_position(
                floor - height,
                pos[1] + (0 if left else pos[3] - 1),
                transpose
            )
            if not up_item:
                reached_top = True
            else:
                up_item_pos = self._get_item_position(up_item.widget(),
                                                      transpose)
                reached_top = not (
                    (up_item_pos[1] == pos[1]) if left
                    else (up_item_pos[1] + up_item_pos[3] == pos[1] + pos[3])
                )
                if not reached_top:
                    height += up_item_pos[2]
        return height

    def _grow_block(block, space, transpose):
        pass

    def _multiply_spans(self, factor, transpose, widgets=None):
        """Multiplies the rowspan of widgets by a specified factor.

        Multiplies the rowspan of all widgets (if widgets is None, otherwise
        only specified widgets) by a specified factor. Their position is also
        adjusted to match their new height. If a widget is not included in
        "widgets" but their position could be affected by the change of another
        widget's rowspan, it must be solved before invoking this function.

        Args:
            factor: Factor by which to multiply all rowspans.
            transpose: If True, will behave as if the grid was transposed.
            widgets: List of widgets whose rowspan to multiply. If omitted, all
                     widgets are affected.
        """
        if widgets is None:
            widgets = [self.itemAt(i).widget() for i in range(self.count())]
            offset = 0
        else:
            # If not every widget is to be resized, we assume the rest of the
            # widgets form a critical block. We need to know at which row the
            # block is positioned and take this offset into account when
            # setting the new positions of the resized widgets.
            offset = min((self._get_item_position(w, transpose)[0]
                          for w in widgets))
        cache = []
        for widget in widgets:
            pos = self._get_item_position(widget, transpose)
            pos = ((pos[0] - offset) * factor + offset, pos[1],
                   pos[2] * factor, pos[3])
            cache.append((widget, pos))
            self.removeWidget(widget)

        for widget, pos in cache:
            self.layout()._add_widget(widget, *pos, transpose)

    def _adjust_sizes(self, transpose):
        """Resizes all widgets that have available space to grow.

        Args:
            transpose: If True, will behave as if the grid was transposed.
        """
        widget_to_grow = self._find_growable_widget(transpose)
        if widget_to_grow:
            self._grow(widget_to_grow, transpose)
            self._adjust_sizes(transpose)

    def _find_growable_widget(self, transpose):
        visited_widgets = []

        for row in range(0, self._row_count(transpose)):
            for col in range(0, self._column_count(transpose)):
                item = self._item_at_position(row, col, transpose)

                if not item or item.widget() in visited_widgets:
                    continue

                visited_widgets.append(item.widget())
                if self._grow_space(item.widget(), transpose):
                    return item.widget()

        return None


    def _grow_space(self, widget, transpose):
        """Returns the amount of space a widget has available to grow.

        Args:
            transpose: If True, will behave as if the grid was transposed.
        """
        pos = self._get_item_position(widget, transpose)
        pivot, start, end = (pos[0] + pos[2], pos[1], pos[1] + pos[3])
        limit = self._row_count(transpose)
        if pivot < limit:
            for index in range(start, end):
                item = self._item_at_position(pivot, index, transpose)
                if not item:
                    space = 0
                    while not item and pivot < limit:
                        space += 1
                        pivot += 1
                        item = self._item_at_position(pivot, index, transpose)
                    return space
        return 0

    def _grow(self, widget, transpose):
        """Resizes a particular widget.

        Args:
            transpose: If True, will behave as if the grid was transposed.
        """
        # We need to ask again, because after one widget has grown it's
        # possible that another one that previously could, now can't anymore.
        space = self._grow_space(widget, transpose)

        next_supporters = self._get_support_widgets(widget, False, transpose)
        # TODO: resize the critical block,not only "widget"
        widgets_to_displace = [
            (widget, self._get_item_position(widget, transpose))
            for widget in next_supporters
        ]
        for supporter in next_supporters:
            self.removeWidget(supporter)
        for supporter, pos in widgets_to_displace:
            new_pos = (pos[0] + space, pos[1], pos[2], pos[3])
            self._add_widget(supporter, *new_pos, transpose)
        curr_pos = self._get_item_position(widget, transpose)
        new_widget_pos = (curr_pos[0], curr_pos[1], curr_pos[2] + space,
                          curr_pos[3])
        self.removeWidget(widget)
        self._add_widget(widget, *new_widget_pos, transpose)
