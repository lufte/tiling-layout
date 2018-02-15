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

    def _split(self, old_widget, new_widget, horizontal, put_before=False):
        curr_pos = self.getItemPosition(self.indexOf(old_widget))
        offset = (curr_pos[0] if horizontal else curr_pos[1]) + 1
        end = self.rowCount() if horizontal else self.columnCount()
        panes_to_displace = []

        for index in range(offset, end):
            item = self.itemAtPosition(*(
                (index, curr_pos[1])
                if horizontal else
                (curr_pos[0], index)
            ))

            if not item:
                # should not be needed once I figure rowspans and colspans
                continue
            item_pos = (item.widget(),
                        self.getItemPosition(self.indexOf(item.widget())))
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

