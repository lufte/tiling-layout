from PyQt5.QtWidgets import QGridLayout
from bisect import bisect
import itertools
import pdb

class QTilingLayout(QGridLayout):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def hsplit(self, old_widget, new_widget, put_before=False):
        self._split(old_widget, new_widget, True, put_before=put_before)

    def vsplit(self, old_widget, new_widget, put_before=False):
        self._split(old_widget, new_widget, False, put_before=put_before)

    def _split(self, old_widget, new_widget, horizontal, put_before=False):
        """Splits old_widget and inserts new_widget in the available space.

        Args:
            old_widget: The widget to be splitted.
            new_widget: The widget to insert in the new available space.
            horizontal: True if splitting in the X axis, False for Y.
            put_before: True if new_widget is to be put before old_widget.
        """
        curr_pos = self.getItemPosition(self.indexOf(old_widget))
        span = curr_pos[2] if horizontal else curr_pos[3]
        prev_supporters = self._get_support_widgets(old_widget, not horizontal,
                                                    True)
        next_supporters = self._get_support_widgets(old_widget, not horizontal,
                                                    False)
        supporters = prev_supporters.union(next_supporters)
        max_span = max((
            (self.getItemPosition(self.indexOf(w))[2]
             if horizontal else
             self.getItemPosition(self.indexOf(w))[3])
            for w in supporters
        )) if supporters else 0

        if span >= max_span * 2:
            if span % 2 != 0:
                self._multiply_spans(horizontal, 2)
                curr_pos = self.getItemPosition(self.indexOf(old_widget))
                span = curr_pos[2] if horizontal else curr_pos[3]
            self.removeWidget(old_widget)
            old_widget_pos = (curr_pos[0],
                              curr_pos[1],
                              curr_pos[2] / (2 if horizontal else 1),
                              curr_pos[3] / (1 if horizontal else 2))
            new_widget_pos = (curr_pos[0] + (span / 2 if horizontal else 0),
                              curr_pos[1] + (0 if horizontal else span / 2),
                              curr_pos[2] / (2 if horizontal else 1),
                              curr_pos[3] / (1 if horizontal else 2))
            self.addWidget(old_widget, *old_widget_pos)
            self.addWidget(new_widget, *new_widget_pos)
        else:
            # TODO: optimize this, we iterate supporters like a thousand times
            # TODO: using the old_widget's span and leaving everything else
            # unotuched is not enough. if the new_widget's span does not equal
            # the support line's minimum, we should adjust some of the other
            # sizes as well
            widgets_to_displace = [
                (widget, self.getItemPosition(self.indexOf(widget)))
                for widget in next_supporters
            ]
            for widget in next_supporters:
                self.removeWidget(widget)
            for widget, pos in widgets_to_displace:
                new_pos = (pos[0] + (span if horizontal else 0),
                           pos[1] + (0 if horizontal else span),
                           pos[2],
                           pos[3])
                self.addWidget(widget, *new_pos)
            new_widget_pos = (curr_pos[0] + (span if horizontal else 0),
                              curr_pos[1] + (0 if horizontal else span),
                              curr_pos[2],
                              curr_pos[3])
            self.addWidget(new_widget, *new_widget_pos)
            adjust = True
            pdb.set_trace()
            if adjust:
                self._adjust_sizes(not horizontal)
            # self._adjust_sizes2(not horizontal, supporters)

    def _get_support_widgets(self, widget, horizontal, before, level=None):
        """Returns a set of "support" widgets for the specified widget.

        A support widget is a widget that is (directly or indirectly) "pushed"
        by the specified widget when it grows. A widget has support widgets in
        four directions: up (horizontal=False, before=True), right
        (horizontal=True, before, False), down (horizontal=False, before=False)
        and left (horizontal=True, before=True).

        Args:
            widget: The widget for which to find supporters.
            horizontal: The axis in which to find supporters (always the
                        opposite of the splitting axis).
            before: The direction in which to find supporters (True for
                    left/up, False for right/down; depending on horizontal).
            level: How many levels of recursion (support widgets of the support
                   widgets) to process before returning. If None, keep looking
                   for support widgets until the end of the grid.
        """
        supporters = set()
        pos = self.getItemPosition(self.indexOf(widget))
        if horizontal:
            pivot = pos[1] - 1 if before else pos[1] + pos[3]
            start = pos[0]
            end = pos[0] + pos[2]
        else:
            pivot = pos[0] - 1 if before else pos[0] + pos[2]
            start = pos[1]
            end = pos[1] + pos[3]
        upper_limit = self.columnCount() if horizontal else self.rowCount()
        within_limits = (pivot >= 0) if before else (pivot < upper_limit)
        if within_limits:
            for index in range(start, end):
                curr_pos = (index, pivot) if horizontal else (pivot, index)
                item = self.itemAtPosition(*curr_pos)
                if item:  # this function can be called in the resizing process
                    supporters.add(item.widget())
        if level == 0:
            return supporters
        else:
            next_level = None if level is None else level - 1
            return supporters.union(
                *(self._get_support_widgets(w, horizontal, before, level)
                  for w in supporters)
            )

    def _adjust_sizes2(self, horizontal, support_widgets):
        empty_block = self._find_empty_block(horizontal)
        if empty_block:
            self._fill_empty_block(empty_block, horizontal, support_widgets)
            self._adjust_sizes2(horizontal, support_widgets)

    def _find_empty_block(self, horizontal):
        """Finds a block made entirely of empty space.

        Returns a tuple in the form of (i, j, rowspan, colspan). the block is
        of the largest possible size.

        Args:
            horizontal: If true, the block is searched from left to right
                        scanning each column at a time, else it is search from
                        top to bottom scanning each row at a time. It's always
                        the opposite of the splitting axis.
        """
        positions = (
            (inner, outer) if horizontal else (outer, inner)
            for outer in
            range(0, self.columnCount() if horizontal else self.rowCount())
            for inner in
            range(0, self.rowCount() if horizontal else self.columnCount())
        )

        empty_block_start = None
        for pos in positions:
            item = self.itemAtPosition(*pos)
            if item is None:
                empty_block_start = pos
                break

        if empty_block_start:
            # We know where it starts, now find its dimensions
            rowspan = colspan = 1
            for i in range(empty_block_start[0] + 1, self.rowCount()):
                if not self.itemAtPosition(i, empty_block_start[1]):
                    rowspan += 1
                else:
                    break
            for j in range(empty_block_start[1] + 1, self.columnCount()):
                if not self.itemAtPosition(empty_block_start[0], j):
                    colspan += 1
                else:
                    break
            return (*empty_block_start, rowspan, colspan)
        else:
            # No empty blocks
            return None

    def _fill_empty_block(self, empty_block, horizontal, excluded_widgets):
        """Finds a critical block to grow and fill the empty space.

        Args:
            empty_block: The position of the empty block in the form
                         (i, j, rowspan, colspan).
            hozirontal: If true, the widgets are searched to the left of the
                        empty block, otherwise they are searched upwards. It's
                        always the opposite of the splitting axis.
            excluded_widgets: Set of widgets which can't grow so they must
                              not be considered for filling empty spaces.
        """
        if horizontal:
            pass
        else:
            base_widget = (
                self.itemAtPosition(empty_block[0],
                                    empty_block[1] - 1).widget()
                if horizontal else
                self.itemAtPosition(empty_block[0] - 1,
                                    empty_block[1]).widget()
            )
            base_widget_pos = self.getItemPosition(self.indexOf(base_widget))
            is_aligned = (base_widget_pos[0] == empty_block[0]
                          if horizontal else
                          base_widget_pos[1] == empty_block[1])
            if is_aligned:
                increment = True
                start = (base_widget_pos[0]
                         if horizontal else
                         base_widget_pos[1])
                end = (base_widget_pos[0] + base_widget_pos[2] - 1
                       if horizontal else
                       base_widget_pos[1] + base_widget_pos[3] - 1)
            else:
                # This widget isn't aligned with the empty block, so we start
                # on the other end
                increment = False
                base_widget = (
                    self.itemAtPosition(
                        empty_block[0] + empty_block[2] - 1,
                        empty_block[1] - 1).widget()
                    if horizontal else
                    self.itemAtPosition(
                        empty_block[0] - 1,
                        empty_block[1] + empty_block[3] - 1).widget()
                )
                base_widget_pos = self.getItemPosition(
                    self.indexOf(base_widget)
                )
                start = (base_widget_pos[0] + base_widget_pos[2] - 1
                         if horizontal else
                         base_widget_pos[1] + base_widget_pos[3] - 1)
                end = (base_widget_pos[0]
                       if horizontal else
                       base_widget_pos[1])

            # Now to find out the size
            size = base_widget[3] if horizontal else base_widget_pos[2]
            next_item = (
                self.itemAtPosition(start, empty_block[1] - 1 - size)
                if horizontal else
                self.itemAtPosition(empty_block[0] - 1 - size, start)
            )
            while next_item and next_item.widget() not in excluded_widgets:
                pos = self.getItemPosition(self.indexOf(next_item.widget()))
                size += pos[3] if horizontal else pos[2]
                next_item = (
                    self.itemAtPosition(start, empty_block[1] - 1 - size)
                    if horizontal else
                    self.itemAtPosition(empty_block[0] - 1 - size, start)
                )

            # Finally, move along the axis (incrementing the index if
            # "increment" is True, decrementing it otherwise) and grow the
            # block until it's rectangular
            is_rectangular = False
            index_limit = (empty_block[1] if horizontal
                           else empty_block[0]) - 1 - size
            while not is_rectangular:
                index = (empty_block[1] if horizontal else empty_block[0]) - 1
                aligned = True
                prev_widget = None
                while aligned and index > index_limit:
                    pos = (end, index) if horizontal else (index, end)
                    widget = self.itemAtPosition(*pos).widget()

                    if widget is prev_widget:
                        continue
                    prev_widget - widget

                    widget_pos = self.getItemPosition(self.indexOf(widget))
                    if horizontal:
                        edge = (widget_pos[0] if increment
                                else widget_pos[0] + widget_pos[2] - 1)
                    else:
                        edge = (widget_pos[1] if increment
                                else widget_pos[1] + widget_pos[3] - 1)
                    aligned = end == edge
                    index -= widget_pos[3] if horizontal else widget_pos[2]

                if aligned:
                    is_rectangular = True
                elif increment:
                    pos = ((end + 1, empty_block[1] - 1) if horizontal
                           else (empty_block[0] - 1, end + 1))
                    next_neighbor = self.itemAtPosition(*pos).widget()
                    next_neighbor_pos = self.getItemPosition(
                        self.indexOf(next_neighbor))
                    end += next_neighbor_pos[2 if horizontal else 3]
                else:
                    pos = ((end - 1, empty_block[1] - 1) if horizontal
                           else (empty_block[0] - 1, end - 1))
                    next_neighbor_pos = self.getItemPosition(
                        self.indexOf(next_neighbor))
                    end -= next_neighbor_pos[2 if horizontal else 3]

            i, j, rowspan, colspan = (
                empty_block[1 if horizontal else 0] - size,
                min(start, end),
                size,
                abs(end - start) + 1
            )
        # self._grow_block((i, j, rowspan, colspan), empty_block[2])
        return i, j, rowspan, colspan





    def _adjust_sizes(self, horizontal):
        """Resizes all widgets that have available space to grow.

        Args:
            horizontal: The axis in which to resize widgets (always the
                        opposite of the splitting axis).
        """
        widget_to_grow = self._find_growable_widget(horizontal)
        if widget_to_grow:
            self._grow(widget_to_grow, horizontal)
            self._adjust_sizes(horizontal)

    def _find_growable_widget(self, horizontal):
        visited_widgets = []

        for outer in range(0, self.columnCount() if horizontal else
                self.rowCount()):
            for inner in range(0, self.rowCount() if horizontal else
                    self.columnCount()):
                pos = (inner, outer) if horizontal else (outer, inner)
                item = self.itemAtPosition(*pos)

                if not item or item.widget() in visited_widgets:
                    continue

                visited_widgets.append(item.widget())
                if self._grow_space(item.widget(), horizontal):
                    return item.widget()

        return None


    def _grow_space(self, widget, horizontal):
        """Returns the amount of space a widget has available to grow.

        Args:
            horizontal: The axis in which to find space (always the opposite
                        of the splitting axis).
        """
        pos = self.getItemPosition(self.indexOf(widget))
        pivot, start, end = ((pos[1] + pos[3], pos[0], pos[0] + pos[2])
                             if horizontal else
                             (pos[0] + pos[2], pos[1], pos[1] + pos[3]))
        limit = self.columnCount() if horizontal else self.rowCount()
        if pivot < limit:
            for index in range(start, end):
                curr_pos = (index, pivot) if horizontal else (pivot, index)
                item = self.itemAtPosition(*curr_pos)
                if not item:
                    space = 0
                    while not item and pivot < limit:
                        space += 1
                        pivot += 1
                        curr_pos = ((index, pivot) if horizontal
                                    else (pivot, index))
                        item = self.itemAtPosition(*curr_pos)
                    return space
        return 0

    def _grow(self, widget, horizontal):
        """Resizes a particular widget.

        Args:
            horizontal: The axis in which to resize (always the opposite of
                        the splitting axis).
        """
        # We need to ask again, because after one widget has grown it's
        # possible that another one that previously could, now can't anymore.
        space = self._grow_space(widget, horizontal)

        next_supporters = self._get_support_widgets(widget, horizontal, False)
        # TODO: resize the critical block,not only "widget"
        widgets_to_displace = [
            (widget, self.getItemPosition(self.indexOf(widget)))
            for widget in next_supporters
        ]
        for supporter in next_supporters:
            self.removeWidget(supporter)
        for supporter, pos in widgets_to_displace:
            new_pos = (pos[0] + (0 if horizontal else space),
                       pos[1] + (space if horizontal else 0),
                       pos[2],
                       pos[3])
            self.addWidget(supporter, *new_pos)
        curr_pos = self.getItemPosition(self.indexOf(widget))
        new_widget_pos = (curr_pos[0],
                          curr_pos[1],
                          curr_pos[2] + (0 if horizontal else space),
                          curr_pos[3] + (space if horizontal else 0))
        self.removeWidget(widget)
        self.addWidget(widget, *new_widget_pos)

    def _multiply_spans(self, horizontal, factor):
        item = self.itemAt(0)
        widgets = []
        while item:
            pos = self.getItemPosition(0)
            pos = (
                (pos[0] * factor, pos[1], pos[2] * factor, pos[3])
                if horizontal else
                (pos[0], pos[1] * factor, pos[2], pos[3] * factor)
            )
            widgets.append((item.widget(), pos))
            self.removeWidget(item.widget())
            item = self.itemAt(0)

        for widget, pos in widgets:
            self.layout().addWidget(widget, *pos)
