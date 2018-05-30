from PyQt5.QtWidgets import QGridLayout, QWidget


class SplitLimitException(Exception):
    pass


class PointOutsideGridException(Exception):
    pass


class SplitException(Exception):
    """Generic unexpected exception with useful debug information"""

    def __init__(self, positions, pos_index, operation):
        """Creates a new SplitException

        Args:
            positions: List of positions of all the widgets in the layout
                       before the failed operation was executed.
            pos_index: Index of the position of the affected widget in the
                       previous list.
            operation: 'vsplit', 'hsplit' or 'delete'
        """
        valid_operations = ('vsplit', 'hsplit', 'delete')
        if operation not in valid_operations:
            raise ValueError('"operation" must be one of '
                             '{}'.format(valid_operations))
        super().__init__('Exception raised when performing a "{}" operation '
                         'of the widget positioned at {}.\nPositions:\n'
                         '{}'.format(operation, positions[pos_index],
                                     '\n'.join(str(p) for p in positions)))
        self.positions = positions
        self.pos_index = pos_index
        self.operation = operation


class QTilingLayout(QGridLayout):

    def __init__(self, widget, *args, max_span=12, **kwargs):
        super().__init__(*args, **kwargs)
        self._max_span = max_span
        self._add_widget(widget, 0, 0, self._max_span, self._max_span, False)

    def _is_point_inside_grid(self, row, col):
        """Determines if the point is inside the layout."""
        return 0 <= row < self._max_span and 0 <= col < self._max_span

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

    def _get_state(self):
        """Returns every widget in the layout along with its position"""

        return [(self.itemAt(i).widget(), self.getItemPosition(i))
                for i in range(self.count())]

    def _restore_state(self, prev_state):
        item = self.itemAt(0)
        while item:
            widget = item.widget()
            self.removeWidget(widget)
            widget.hide()
            item = self.itemAt(0)
        for widget, pos in prev_state:
            widget.show()
            self.addWidget(widget, *pos)

    def delete_widget(self, widget):
        """Removes a widget from the layout and fills the remaining space"""

        raise NotImplentedError

    def hsplit(self, old_widget, new_widget, put_before=False):
        """Splits the specified widget horizontally.

        Args:
            old_widget: The widget to split.
            new_widget: The widget to insert in the new space.
            put_before: If True, the new widget will be inserted on top of the
                        old widget.
        """

        self._split(old_widget, new_widget, put_before, False)

    def vsplit(self, old_widget, new_widget, put_before=False):
        """Splits the specified widget vertically.

        Args:
            old_widget: The widget to split.
            new_widget: The widget to insert in the new space.
            put_before: If True, the new widget will be inserted to the left of
                        the old widget.
        """
        self._split(old_widget, new_widget, put_before, True)

    def _split(self, old_widget, new_widget, put_before, transpose):
        """Splits the specified widget.

        Args:
            old_widget: The widget to split.
            new_widget: The widget to insert in the new space.
            put_before: If True, the new widget will be inserted on top the
                        old widget.
            transpose: If True, will behave as if the grid was transposed.
        """
        original_state = self._get_state()
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

        try:
            for widget, old_pos in widgets:
                self.removeWidget(widget)
                row = max(offsets[old_pos[1]:old_pos[1] + old_pos[3]])

                if row >= rows:
                    raise SplitLimitException

                self._add_widget(widget, row, old_pos[1], 1, old_pos[3],
                                 transpose)
                for col in range(old_pos[1], old_pos[1] + old_pos[3]):
                    offsets[col] = row + 1

            self._drop_hanging_widgets(ib, transpose)
            block_height = 1 + max(self._get_item_position(w, transpose)[0]
                                   for w, _ in widgets)
            block_to_grow= RecBlock(self, transpose, ib.i, ib.j, block_height,
                                    ib.colspan)
            block_to_grow.displace_and_resize(0, rows - block_height)
            self._fill_spaces(ib, transpose)
        except SplitLimitException:
            self._restore_state(original_state)
            raise
        except Exception as e:
            original_positions = [t[1] for t in original_state]
            raise SplitException(
                original_positions,
                original_positions.index(old_widget_pos),
                'vsplit' if transpose else 'hsplit'
            ) from e


    def _get_independent_block(self, widget, transpose):
        """Returns the independent block for the specified widget.

        An indenpendent block is a CriticalBlock that doesn't share widgets to
        the CriticalBlock to its right nor the CriticalBlock to its left.

        Args:
            widget: Find the independent block that contains this widget.
            transpose: If True, will behave as if the grid was transposed.
        """
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

    def _drop_hanging_widgets(self, domain, transpose):
        """Moves widgets with lateral space down until that space is filled.

        A hanging widget is a widget with lateral space (to their left or
        their right) which, if moved down, can fill that space with another
        widget.

        Args:
            domain: A Block in which hanging widgets will be searched.
            transpose: If True, will behave as if the grid was transposed.
        """
        for widget, pos in domain.get_widgets():
            left_space = (pos[1] > domain.j and not
                          self._item_at_position(pos[0], pos[1] - 1,
                                                 transpose))
            right_space = (pos[1] + pos[3] < domain.j + domain.colspan and not
                           self._item_at_position(pos[0], pos[1] + pos[3],
                                                  transpose))
            left_height = 1
            left_fits = False
            if left_space:
                for row in range(pos[0] + 1, domain.i + domain.rowspan):
                    item = self._item_at_position(row, pos[1] - 1, transpose)
                    if item:
                        tmp_pos = self._get_item_position(item.widget(),
                                                          transpose)
                        left_fits = tmp_pos[1] + tmp_pos[3] == pos[1]
                        break
                    else:
                        left_height += 1

            right_height = 1
            right_fits = False
            if right_space:
                for row in range(pos[0] + 1, domain.i + domain.rowspan):
                    item = self._item_at_position(row, pos[1] + pos[3],
                                                  transpose)
                    if item:
                        tmp_pos = self._get_item_position(item.widget(),
                                                          transpose)
                        right_fits = tmp_pos[1] == pos[1] + pos[3]
                        break
                    else:
                        right_height += 1

            displacement = (
                min(left_height, right_height) if left_fits and right_fits else
                left_height if left_fits else
                right_height if right_fits else
                0
            )

            if displacement:
                widgets = [(widget, pos)]
                max_row = pos[0]
                for supporter in self._get_supporters(widget, transpose):
                    supporter_pos = self._get_item_position(supporter,
                                                            transpose)
                    widgets.append((supporter, supporter_pos))
                    max_row = max(max_row, supporter_pos[0])

                if max_row + displacement < self._row_count(transpose):
                    for supporter, old_pos in widgets:
                        self.removeWidget(supporter)
                        # We are adding a widget before removing its
                        # supporters. This could cause overlap between widgets
                        # until the whole loop it's over.
                        self._add_widget(supporter, old_pos[0] + displacement,
                                         *old_pos[1:], transpose)
                    self._drop_hanging_widgets(domain, transpose)
                    return

    def _get_supporters(self, widget, transpose):
        """Returns a set of "support" widgets for the specified widget.

        A support widget is a widget that is (directly or indirectly) "pushed"
        by the specified widget when it grows.

        Args:
            widget: The widget for which to find supporters.
            transpose: If True, will behave as if the grid was transposed.
        """
        supporters = set()
        pos = self._get_item_position(widget, transpose)
        pivot = pos[0] + pos[2]
        start = pos[1]
        end = pos[1] + pos[3]
        upper_limit = self._row_count(transpose)
        within_limits = (pivot < upper_limit)
        if within_limits:
            for index in range(start, end):
                item = self._item_at_position(pivot, index, transpose)
                if item:  # this function can be called in the resizing process
                    supporters.add(item.widget())
        return supporters.union(*(self._get_supporters(w, transpose)
                                  for w in supporters))

    def _fill_spaces(self, domain, transpose):
        """Searches EmptyBlocks inside domain and fills them.

        Args:
            domain: A Block in which empty spaces will be searched.
            transpose: If True, will behave as if the grid was transposed.
        """
        eb = EmptyBlock.find_in_block(self, transpose, domain)

        if not eb:
            return

        # Find a CriticalBlock that can fill the EmptyBlock
        cb = CriticalBlock.build_from_point(self, transpose, eb.i, eb.j,
                                            eb.colspan, True)
        cb.displace_and_resize(0, eb.rowspan)
        self._fill_spaces(domain, transpose)


class InvalidBlockException(Exception):
    """Raised if a Block has no area or doesn't fit in the layout."""
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

    def contains_point(self, layout, transpose, i, j):
        return (self.i <= i < self.i + self.rowspan and
                self.j <= j < self.j + self.colspan)

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
        row = i - (1 if up else 0)
        reached_left_end = row < 0 if up else row == rows
        while not reached_left_end:
            item = layout._item_at_position(row, j, transpose)
            if item:
                pos = layout._get_item_position(item.widget(), transpose)
                if pos[1] == j:
                    left_rows.add(pos[0] + (0 if up else pos[2]))
                    row = pos[0] + (-1 if up else pos[2])
                    reached_left_end = row < 0 if up else row == rows
                else:
                    reached_left_end = True
            else:
                reached_left_end = True

        right_rows = set()
        row = i - (1 if up else 0)
        reached_right_end = row < 0 if up else row == rows
        while not reached_right_end:
            item = layout._item_at_position(row, j + colspan - 1, transpose)
            if item:
                pos = layout._get_item_position(item.widget(), transpose)
                if pos[1] + pos[3] == j + colspan:
                    right_rows.add(pos[0] + (0 if up else pos[2]))
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

    def __init__(self, widget_pos, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.widget_pos = widget_pos


class EmptyBlock(Block):

    def __init__(self, layout, transpose, i, j, rowspan, colspan):
        super().__init__(layout, transpose, i, j, rowspan, colspan)
        for col in range(self.j, self.j + self.colspan):
            for row in range(self.i, self.i + self.rowspan):
                if self.layout._item_at_position(row, col, self.transpose):
                    raise WidgetInEmptyBlockException((row, col))

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
            return cls.build_from_point(layout, transpose, domain,
                                        *empty_point)
        else:
            # No empty blocks
            return None

    @classmethod
    def build_from_point(cls, layout, transpose, domain, i, j):
        rowspan = colspan = 0

        for rowspan in range(0, domain.i + domain.rowspan - i):
            if layout._item_at_position(i + rowspan, j, transpose):
                break
            rowspan += 1

        for colspan in range(0, domain.j + domain.colspan - j):
            if layout._item_at_position(i, j + colspan, transpose):
                break
            colspan += 1

        try:
            return cls(layout, transpose, i, j, rowspan, colspan)
        except WidgetInEmptyBlockException as e:
            # We reached an irregular shaped empty space. Try to build the
            # block using the information from the exception
            colspan = e.widget_pos[1] - j
            return cls(layout, transpose, i, j, rowspan, colspan)
