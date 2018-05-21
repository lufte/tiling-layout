from PyQt5.QtWidgets import QGridLayout, QWidget
from functools import reduce
from math import gcd as gcd_
import itertools
import pdb


class SplitLimitException(Exception):
    pass


class PointOutsideGridException(Exception):
    pass


class QTilingLayout(QGridLayout):

    def __init__(self, widget, *args, max_span=60, **kwargs):
        super().__init__(*args, **kwargs)
        self.max_span = max_span
        self._add_widget(widget, 0, 0, self.max_span, self.max_span, False)

    def _is_point_inside_grid(self, row, col):
        # return 0 <= row < self.max_span and 0 <= col < self.max_span
        # TODO: fix tests to use the previous line
        return 0 <= row < self.rowCount() and 0 <= col < self.columnCount()

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
            if not self._is_point_inside_grid(row, col):
                raise PointOutsideGridException
            return self.addWidget(widget, row, col, rowspan, colspan)
        else:
            if not self._is_point_inside_grid(col, row):
                raise PointOutsideGridException
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
            if not self._is_point_inside_grid(row, col):
                raise PointOutsideGridException
            return self.itemAtPosition(row, col)
        else:
            if not self._is_point_inside_grid(col, row):
                raise PointOutsideGridException
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
        rows = self._row_count(transpose)
        old_widget_pos = self._get_item_position(old_widget, transpose)
        ib = self._get_independent_block(old_widget, transpose)
        offsets = [0] * self._column_count(transpose)
        widgets = list(ib.get_widgets())
        if put_before:
            widgets.insert(widgets.index((old_widget, old_widget_pos)),
                           (new_widget, old_widget_pos))
        else:
            widgets.insert(widgets.index((old_widget, old_widget_pos)) + 1,
                           (new_widget, old_widget_pos))

        for widget, old_pos in widgets:
            self.removeWidget(widget)
            row = max(offsets[old_pos[1]:old_pos[1] + old_pos[3]])

            if row >= rows:
                raise SplitLimitException

            self._add_widget(widget, row, old_pos[1], 1, old_pos[3], transpose)
            for col in range(old_pos[1], old_pos[1] + old_pos[3]):
                offsets[col] = row + 1

        block_height = max(offsets)
        block_to_grow= RecBlock(self, transpose, ib.i, ib.j, block_height,
                                ib.colspan)
        block_to_grow.displace_and_resize(0, rows - block_height)
        self._fill_easy_spaces(ib, transpose)
        # self._fill_hard_spaces(ib, transpose)

    def _fill_easy_spaces(self, domain, transpose):
        eb = EmptyBlock.find_in_block(self, transpose, domain)

        if not eb:
            return

        # Find a CriticalBlock on top of it with the same width
        try:
            cb = CriticalBlock.build_from_point(self, transpose, eb.i,
                                                eb.j, eb.colspan, True)
        except (EmptySpaceInCriticalBlockException,
                ImpossibleToBuildBlockException):
            # No suitable CriticalBlock, try another EmptyBlock
            new_domain = RecBlock(self, transpose, eb.i + eb.rowspan, domain.j,
                                  domain.i + domain.rowspan - eb.i
                                  - eb.rowspan, domain.colspan)
            self._fill_easy_spaces(new_domain, transpose)
        else:
            cb.displace_and_resize(0, eb.rowspan)
            self._fill_easy_spaces(domain, transpose)

    def _fill_hard_spaces(self, domain, transpose):
        raise NotImplementedError

    def _get_independent_block(self, widget, transpose):
        pos = self._get_item_position(widget, transpose)
        rows = self._row_count(transpose)

        left = pos[1]
        found_left_limit = False
        while not found_left_limit:
            height = 0
            reached_end = False
            while not reached_end:
                tmp_widget = self._item_at_position(height, left,
                                                    transpose).widget()
                tmp_pos = self._get_item_position(tmp_widget, transpose)
                if tmp_pos[1] == left:
                    height += tmp_pos[2]
                reached_end = tmp_pos[1] != left or height == rows
            if height == rows:
                found_left_limit = True
            else:
                tmp_left_widget = self._item_at_position(tmp_pos[0], left - 1,
                                                         transpose).widget()
                left = self._get_item_position(tmp_left_widget, transpose)[1]

        right = pos[1] + pos[3]
        found_right_limit = False
        while not found_right_limit:
            height = 0
            reached_end = False
            while not reached_end:
                tmp_widget = self._item_at_position(height, right - 1,
                                                    transpose).widget()
                tmp_pos = self._get_item_position(tmp_widget, transpose)
                if tmp_pos[1] + tmp_pos[3] == right:
                    height += tmp_pos[2]
                reached_end = (tmp_pos[1] + tmp_pos[3] != right
                               or height == rows)
            if height == rows:
                found_right_limit = True
            else:
                tmp_right_widget = self._item_at_position(tmp_pos[0], right,
                                                          transpose).widget()
                tmp_right_widget_pos = self._get_item_position(
                    tmp_right_widget,
                    transpose
                )
                right = tmp_right_widget_pos[1] + tmp_right_widget_pos[3]

        return CriticalBlock(self, transpose, 0, left, rows, right - left)


class InvalidBlockException(Exception):
    pass


class Block:

    def __init__(self, layout, transpose, i, j, rowspan, colspan):
        if not (
                i >= 0 and j >= 0 and rowspan > 0 and colspan > 0
                and 0 <= i < layout._row_count(transpose)
                and 0 <= j < layout._column_count(transpose)
                and 0 < i + rowspan <= layout._row_count(transpose)
                and 0 < j + colspan <= layout._column_count(transpose)
        ):
            raise InvalidBlockException
        self.layout = layout
        self.transpose = transpose
        self.i = i
        self.j = j
        self.rowspan = rowspan
        self.colspan = colspan

    def get_widgets(self):
        #TODO: find a way to avoid looping over every row
        done = set()
        row = self.i
        while row < self.i + self.rowspan:
            col = self.j
            while col < self.j + self.colspan:
                item = self.layout._item_at_position(row, col, self.transpose)
                if item:
                    widget = item.widget()
                    pos = self.layout._get_item_position(widget,
                                                         self.transpose)
                    if widget not in done:
                        yield widget, pos
                        done.add(widget)
                    col += pos[3]
                else:
                    col += 1
            row += 1

    def __repr__(self):
        return '{}: {}, {}, {}, {}'.format(type(self).__name__, self.i,
                                           self.j, self.rowspan, self.colspan)

    def __eq__(self, other):
        return (self.layout is other.layout
                and self.transpose == other.transpose
                and self.i == other.i
                and self.j == other.j
                and self.rowspan == other.rowspan
                and self.colspan == other.colspan)


class NonRectangularRecBlockException(Exception):
    pass


class RecBlock(Block):

    def __init__(self, layout, transpose, i, j, rowspan, colspan):
        super().__init__(layout, transpose, i, j, rowspan, colspan)
        index = self.i
        while index < self.i + self.rowspan:
            item = self.layout._item_at_position(index, self.j, self.transpose)
            if item:
                item_pos = self.layout._get_item_position(item.widget(),
                                                          self.transpose)
                if item_pos[1] != self.j:
                    raise NonRectangularRecBlockException
                index += item_pos[2]
            else:
                index += 1

        index = self.i
        while index < self.i + self.rowspan:
            item = self.layout._item_at_position(index,
                                                 self.j + self.colspan - 1,
                                                 self.transpose)
            if item:
                item_pos = self.layout._get_item_position(item.widget(),
                                                          self.transpose)
                if item_pos[1] + item_pos[3] != self.j + self.colspan:
                    raise NonRectangularRecBlockException
                index += item_pos[2]
            else:
                index += 1

        index = self.j
        while index < self.j + self.colspan:
            item = self.layout._item_at_position(self.i, index, self.transpose)
            if item:
                item_pos = self.layout._get_item_position(item.widget(),
                                                          self.transpose)
                if item_pos[0] != self.i:
                    raise NonRectangularRecBlockException
                index += item_pos[3]
            else:
                index += 1

        index = self.j
        while index < self.j + self.colspan:
            item = self.layout._item_at_position(self.i + self.rowspan - 1,
                                                 index, self.transpose)
            if item:
                item_pos = self.layout._get_item_position(item.widget(),
                                                          self.transpose)
                if item_pos[0] + item_pos[2] != self.i + self.rowspan:
                    raise NonRectangularRecBlockException
                index += item_pos[3]
            else:
                index += 1

    def _virtualize(self):
        return [
            tuple(self.layout._item_at_position(row, col,
                                                self.transpose).widget()
                  if self.layout._item_at_position(row, col, self.transpose)
                  else None
                  for col in range(self.j, self.j + self.colspan))
            for row in range(self.i, self.i + self.rowspan)
        ]

    @staticmethod
    def materialize_virtual_block(i, j, virtual_block):
        block = {}
        for row in range(len(virtual_block)):
            for col in range(len(virtual_block[0])):
                widget = virtual_block[row][col]

                if not widget:
                    continue

                if widget in block:
                    pos = block[widget][:2]
                    block[widget] = (*pos,
                                     i + row - pos[0] + 1,
                                     j + col - pos[1] + 1)
                else:
                    block[widget] = (i + row, j + col, 1, 1)

        return block.items()

    def displace_and_resize(self, displacement, growth):
        heights = []
        virtual_block = self._virtualize()
        if growth:
            prev_row = None
            common_height = 0
            for row in range(len(virtual_block)):
                curr_row = virtual_block[row]
                if not prev_row or curr_row == prev_row:
                    common_height += 1
                else:
                    heights.append((common_height, row - common_height))
                    common_height = 1
                prev_row = curr_row
            # Append the last one since the loop finishes before
            heights.append((common_height, row + 1 - common_height))

            best = max if growth < 0 else min
            marked_rows = {}
            keep_growing = growth
            while keep_growing:
                height, row_index = best(heights)

                if height == 1 and growth < 0:
                    raise SplitLimitException

                row = virtual_block[row_index]
                marked_rows[row] = marked_rows.setdefault(row, 0) + 1
                if growth < 0:
                    keep_growing += 1
                    heights[heights.index((height, row_index))] = (height - 1,
                                                                   row_index)
                else:
                    keep_growing -= 1
                    heights[heights.index((height, row_index))] = (height + 1,
                                                                   row_index)

            new_virtual_block = []
            for index, row in enumerate(virtual_block):
                if row in marked_rows:
                    if growth > 0:
                        for _ in range(marked_rows[row] + 1):
                            new_virtual_block.append(row)
                        del marked_rows[row]
                    elif marked_rows[row] > 0:
                        marked_rows[row] -= 1
                        if marked_rows[row] == 0:
                            del marked_rows[row]
                else:
                    new_virtual_block.append(row)

            virtual_block = new_virtual_block

        materialized = self.materialize_virtual_block(self.i + displacement,
                                                      self.j, virtual_block)
        for widget, pos in materialized:
            self.layout.removeWidget(widget)
            self.layout._add_widget(widget, *pos, self.transpose)
        self.i += displacement
        self.rowspan += growth


class EmptySpaceInCriticalBlockException(Exception):
    pass


class ImpossibleToBuildBlockException(Exception):
    pass


class CriticalBlock(RecBlock):

    def __init__(self, layout, transpose, i, j, rowspan, colspan):
        super().__init__(layout, transpose, i, j, rowspan, colspan)
        #TODO: find a way to avoid looping over every row
        row = self.i
        while row < self.i + self.rowspan:
            col = self.j
            while col < self.j + self.colspan:
                item = self.layout._item_at_position(row, col, self.transpose)
                if not item:
                    raise EmptySpaceInCriticalBlockException
                else:
                    item_pos = self.layout._get_item_position(item.widget(),
                                                              self.transpose)
                    col += item_pos[3]
            row += 1

    @classmethod
    def build_from_point(cls, layout, transpose, i, j, colspan, up):
        rows = layout._row_count(transpose)

        left_rows = set()
        reached_left_end = False
        row = i - (1 if up else 0)
        while not reached_left_end:
            item = layout._item_at_position(row, j, transpose)
            if item:
                pos = layout._get_item_position(item.widget(), transpose)
                if pos[1] == j:
                    left_rows.add(pos[0])
                    row = pos[0] + (-1 if up else pos[2])
                    reached_left_end = row < 0 if up else row == rows
                else:
                    reached_left_end = True
            else:
                reached_left_end = True

        right_rows = set()
        reached_right_end = False
        row = i - (1 if up else 0)
        while not reached_right_end:
            item = layout._item_at_position(row, j + colspan - 1, transpose)
            if item:
                pos = layout._get_item_position(item.widget(), transpose)
                if pos[1] + pos[3] == j + colspan:
                    right_rows.add(pos[0])
                    row = pos[0] + (-1 if up else pos[2])
                    reached_right_end = row < 0 if up else row == rows
                else:
                    reached_right_end = True
            else:
                reached_right_end = True

        common_rows = sorted(left_rows & right_rows, reverse=not up)

        for row in common_rows:
            try:
                return cls(layout, transpose, row if up else i, j,
                           abs(i - row), colspan)
            except (NonRectangularRecBlockException,
                    EmptySpaceInCriticalBlockException):
                continue

        raise ImpossibleToBuildBlockException


class WidgetInEmptyBlockException(Exception):
    pass


class EmptyBlock(Block):

    def __init__(self, layout, transpose, i, j, rowspan, colspan):
        super().__init__(layout, transpose, i, j, rowspan, colspan)
        for row in range(self.i, self.i + self.rowspan):
            for col in range(self.j, self.j + self.colspan):
                if self.layout._item_at_position(row, col, self.transpose):
                    raise WidgetInEmptyBlockException

    @classmethod
    def find_in_block(cls, layout, transpose, domain):
        positions = (
            (row, col)
            for row in range(domain.i, domain.i + domain.rowspan)
            for col in range(domain.j, domain.j + domain.colspan)
        )

        empty_point = None
        for pos in positions:
            item = layout._item_at_position(*pos, transpose)
            if item is None:
                empty_point = pos
                break

        if empty_point:
            # We know where it starts, now find its dimensions
            rowspan = colspan = 1
            for i in range(empty_point[0] + 1, domain.i + domain.rowspan):
                if not layout._item_at_position(i, empty_point[1], transpose):
                    rowspan += 1
                else:
                    break
            for j in range(empty_point[1] + 1, domain.j + domain.colspan):
                if not layout._item_at_position(empty_point[0], j, transpose):
                    colspan += 1
                else:
                    break
            return cls(layout, transpose, *empty_point, rowspan, colspan)
        else:
            # No empty blocks
            return None
