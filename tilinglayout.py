from PyQt5.QtWidgets import QGridLayout
import itertools

class QTilingLayout(QGridLayout):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._unity = 1

    def hsplit(self, old_widget, new_widget, put_before=False):
        self._split(old_widget, new_widget, True, put_before=put_before)

    def vsplit(self, old_widget, new_widget, put_before=False):
        self._split(old_widget, new_widget, False, put_before=put_before)

    def _get_independent_blocks(self, horizontal):
        """
        Finds groups of rows (if horizontal is True, else columns) that are
        considered independent in the sense that they don't share widgets
        spanning multiple rows (if horizontal is True, else columns) between
        them.

        returns: list of starting indexes for each group
        """
        blocks = []
        curr_items = []
        for outer in range(0, self.rowCount() if horizontal else
                self.columnCount()):
            prev_item = None
            prev_items = curr_items
            curr_items = []
            depends_on_prev = False

            for inner in range(0, self.columnCount() if horizontal else
                    self.rowCount()):
                pos = (outer, inner) if horizontal else (inner, outer)
                item = self.itemAtPosition(*pos)

                if item is prev_item:
                    continue

                prev_item = item
                curr_items.append(item)
                if item in prev_items:
                    depends_on_prev = True

            if not depends_on_prev:
                blocks.append(outer)

        return blocks

    def _split(self, old_widget, new_widget, horizontal, put_before=False):
        blocks = get_independent_blocks(horizontal)
        curr_pos = self.getItemPosition(self.indexOf(old_widget))
        span = curr_pos[2] if horiztonal else curr_pos[3]
        if span == self._unity:
            # we need to insert a new row/column
            pass
        else:
            # we need to shrink other widgets to make room for the new one
            end = self.rowCount() if horizontal else self.columnCount()
            prev_item = None
            for index in range(0, end):
                item = self.itemAtPosition(*(
                    (index, curr_pos[1])
                    if horizontal else
                    (curr_pos[0], index)
                ))
                if item is prev_item:
                    continue
                else:
                    prev_item = item
                item_pos = self.getItemPosition(self.indexOf(item.widget()))


        offset = (curr_pos[0] if horizontal else curr_pos[1]) + 1
        panes_to_displace = []

        for index in range(offset, end):

            if not item:
                # should not be needed once I figure rowspans and colspans
                continue
            item_pos = (item.widget())
            if item_pos not in panes_to_displace:
                panes_to_displace.append(item_pos)

        for pane, old_pos in reversed(panes_to_displace):
            self.removeWidget(pane)
            self.addWidget(pane,
                        old_pos[0] + (1 if horizontal else 0),
                        old_pos[1] + (1 if not horizontal else 0),
                        old_pos[2], old_pos[3])

        self.layout().addWidget(new_widget,
                                curr_pos[0] + (1 if horizontal else 0),
                                curr_pos[1] + (1 if not horizontal else 0),
                                1, 1)

    def _intersect(self, area1, area2):
        return (
            (
                (area2[0] < area1[0] < area2[0] + area2[2])
                or
                (area1[0] < area2[0] < area1[0] + area1[2])
            )
            and
            (
                (area2[1] < area1[1] < area2[1] + area2[3])
                or
                (area1[1] < area2[1] < area1[1] + area1[3])
            )
        )

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

