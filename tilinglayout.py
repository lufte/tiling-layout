from PyQt5.QtWidgets import QGridLayout
from bisect import bisect
import itertools

class QTilingLayout(QGridLayout):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._unity = 1

    def hsplit(self, old_widget, new_widget, put_before=False):
        self._split(old_widget, new_widget, True, put_before=put_before)

    def vsplit(self, old_widget, new_widget, put_before=False):
        self._split(old_widget, new_widget, False, put_before=put_before)

    def _get_critical_block(self, horizontal, i, j):
        pass

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

    def _get_min_span(start, end, horizontal):
        min_span = None
        for outer in range(start, end):
            for inner in range(0, self.rowCount() if horizontal else
                    self.columnCount()):
                pos = (inner, outer) if horizontal else (outer, inner)
                item = self.itemAtPosition(*pos)
                item_pos = self.getItemPosition(self.indexOf(item.widget()))
                span = item_pos[2] if horizontal else item_pos[3]
                if not min_span or span < min_span:
                    min_span = span
        return min_span

    def _get_support_widgets(self, widget, horizontal, before):
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
                supporters.add(item.widget())
        return supporters.union(
            *(self._get_support_widgets(w, horizontal, before)
              for w in supporters)
        )

    def _split(self, old_widget, new_widget, horizontal, put_before=False):
        ind_blocks = self._get_independent_blocks(horizontal)
        support_widgets = self._get_support_widgets(old_widget)
        curr_pos = self.getItemPosition(self.indexOf(old_widget))
        span = curr_pos[2] if horiztonal else curr_pos[3]
        curr_block_index = bisect(blocks,
                                  curr_pos[1] if horizontal else curr_pos[0])
        curr_block_pos = (blocks[curr_block_index - 1],
                          blocks[curr_block_index])
        min_span = _get_min_span(*curr_block_pos, horizontal)

        # Dentro del bloque independiente afectado, busco la columna (o fila)
        # de soporte, es decir, todos los widgets sobre los cuales el widget
        # actual está apoyado, y todos los que están apoyados sobre él. De esos
        # widgets, solo aquellos que no tengan el tamaño mínimo podrán
        # achicarse, y si el widget actual ya tiene el tamaño mínimo se busca
        # un nuevo tamaño mínimo.
        # Si el widget actual tiene el doble o más espacio que el span mínimo,
        # entonces solo él se achica









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

