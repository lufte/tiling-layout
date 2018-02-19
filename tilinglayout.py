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
        max_span = max((
            (self.getItemPosition(self.indexOf(w))[2]
             if horizontal else
             self.getItemPosition(self.indexOf(w))[3])
            for w in prev_supporters.union(next_supporters)
        )) if prev_supporters or next_supporters else 0

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
            self._adjust_sizes(not horizontal)

    def _get_critical_block(self, horizontal, i, j):
        pass

    def _get_support_widgets(self, widget, horizontal, before):
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
        return supporters.union(
            *(self._get_support_widgets(w, horizontal, before)
              for w in supporters)
        )

    def _adjust_sizes(self, horizontal):
        """Resizes all widgets that have available space to grow.

        Args:
            horizontal: The axis in which to resize widgets (always the
                        opposite of the splitting axis).
        """
        growable_widgets = []
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
                    growable_widgets.append(item.widget())

        for widget in growable_widgets:
            self._grow(widget, horizontal)

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
