from PyQt5.QtWidgets import QGridLayout
from bisect import bisect
import itertools
import pdb

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
                self._adjust_sizes(transpose)
            # self._adjust_sizes2(supporters, transpose)

    def _get_support_widgets(self, widget, before, transpose, level=None):
        """Returns a set of "support" widgets for the specified widget.

        A support widget is a widget that is (directly or indirectly) "pushed"
        by the specified widget when it grows.

        Args:
            widget: The widget for which to find supporters.
            before: The direction in which to find supporters (True for up,
                    False for down).
            transpose: If True, will behave as if the grid was transposed.
            level: How many levels of recursion (support widgets of the support
                   widgets) to process before returning. If None, keep looking
                   for support widgets until the end of the grid.
        """
        supporters = set()
        pos = self._get_item_position(widget, transpose)
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
            self._fill_empty_block(empty_block, support_widgets, transpose)
            self._adjust_sizes2(support_widgets, transpose)

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
                if not self._item_at_position(i, empty_block_start[1]):
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

    def _fill_empty_block(self, empty_block, excluded_widgets, transpose):
        """Finds a critical block to grow and fill the empty space.

        Args:
            empty_block: The position of the empty block in the form
                         (i, j, rowspan, colspan).
            transpose: If True, will behave as if the grid was transposed.
            excluded_widgets: Set of widgets which can't grow so they must
                              not be considered for filling empty spaces.
        """
        base_widget = self._item_at_position(empty_block[0] - 1,
                                             empty_block[1],
                                             transpose).widget()
        base_widget_pos = self._get_item_position(base_widget)
        is_aligned = base_widget_pos[1] == empty_block[1]
        if is_aligned:
            increment = True
            start = base_widget_pos[1]
            end = base_widget_pos[1] + base_widget_pos[3] - 1
        else:
            # This widget isn't aligned with the empty block, so we start
            # on the other end
            increment = False
            base_widget = self._item_at_position(
                empty_block[0] - 1,
                empty_block[1] + empty_block[3] - 1,
                transpose
            ).widget()
            base_widget_pos = self._get_item_position(base_widget)
            start = base_widget_pos[1] + base_widget_pos[3] - 1
            end = base_widget_pos[1]

        # Now to find out the height
        size = base_widget_pos[2]
        next_item = self.itemAtPosition(empty_block[0] - 1 - size, start)
        while next_item and next_item.widget() not in excluded_widgets:
            pos = self._get_item_position(next_item.widget(), transpose)
            size += pos[2]
            next_item = self.itemAtPosition(empty_block[0] - 1 - size, start)

        # Finally, move along the X axis (going right if increment==True, left
        # otherwise) and grow the block until it's rectangular
        is_rectangular = False
        index_limit = empty_block[0] - 1 - size
        while not is_rectangular:
            index = empty_block[0] - 1
            aligned = True
            prev_widget = None
            while aligned and index > index_limit:
                widget = self._item_at_position(index, end, transpose).widget()

                if widget is prev_widget:
                    continue
                prev_widget - widget

                widget_pos = self._get_item_position(widget, transpose)
                edge = (widget_pos[1] if increment
                        else widget_pos[1] + widget_pos[3] - 1)
                aligned = end == edge
                index -= widget_pos[2]

            if aligned:
                is_rectangular = True
            next_neighbor = self.item_at_position(
                empty_block[0] - 1,
                end + (1 if increment else -1),
                transpose).widget()
            next_neighbor_pos = self._get_item_position(next_neighbor,
                                                        transpose)
            end += (1 if increment else -1) * next_neighbor_pos[3]

        i, j, rowspan, colspan = (
            empty_block[0] - size,
            min(start, end),
            size,
            abs(end - start) + 1
        )
        # self._grow_block((i, j, rowspan, colspan), empty_block[2])
        return i, j, rowspan, colspan

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

    def _multiply_spans(self, factor, transpose):
        item = self.itemAt(0)
        widgets = []
        while item:
            pos = self._get_item_position(item.widget(), transpose)
            pos = (pos[0] * factor, pos[1], pos[2] * factor, pos[3])
            widgets.append((item.widget(), pos))
            self.removeWidget(item.widget())
            item = self.itemAt(0)

        for widget, pos in widgets:
            self.layout()._add_widget(widget, *pos, transpose)
