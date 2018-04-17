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
            assert self._is_point_inside_grid(row, col), 'Point outside grid'
            return self.addWidget(widget, row, col, rowspan, colspan)
        else:
            assert self._is_point_inside_grid(col, row), 'Point outside grid'
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
            assert self._is_point_inside_grid(row, col), 'Point outside grid'
            return self.itemAtPosition(row, col)
        else:
            assert self._is_point_inside_grid(col, row), 'Point outside grid'
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

            all_supporters = top_supporters.all_nodes().union(
                bottom_supporters.all_nodes(), {new_widget}
            )
            self._fix_unaligned_widgets(ib, all_supporters, transpose)

        else:
            raise NotImplementedError

    def _fix_unaligned_widgets(self, independent_block, supporters, transpose):
        domain = (0, independent_block[0], self._row_count(transpose),
                  independent_block[1])
        unaligned_block, up, free_space_height = self._find_unaligned_block(
            domain,
            supporters,
            transpose
        )
        while unaligned_block:
            empty_space_width = 0
            if (
                    (up and unaligned_block[0] > 0) or
                    (not up and unaligned_block[0] + unaligned_block[2] <
                     self._row_count(transpose))
            ):
                for j in range(unaligned_block[1],
                               unaligned_block[1] + unaligned_block[3]):
                    i = (unaligned_block[0] - 1 if up
                         else unaligned_block[0] + unaligned_block[2])
                    if not self._item_at_position(i, j, transpose):
                        empty_space_width += 1

            if empty_space_width == 0:
                # The block has no space to move at all, so shrink it
                self._displace_and_resize(*unaligned_block, 0 if up else free_space_height,
                                          -free_space_height, transpose)
                unaligned_block, up, free_space_height = self._find_unaligned_block(
                    domain,
                    supporters,
                    transpose
                )
            elif empty_space_width == unaligned_block[3]:
                # The block has space to move, so move it and resize it if
                # necessary
                space_to_fill = 0
                next_item = None
                while not next_item:
                    space_to_fill += 1
                    i = (unaligned_block[0] - space_to_fill - 1 if up
                         else unaligned_block[0] + unaligned_block[2] +
                         space_to_fill)
                    next_item = self._item_at_position(i, unaligned_block[1],
                                                       transpose)
                self._displace_and_resize(*unaligned_block,
                                          space_to_fill * (-1 if up else 1),
                                          space_to_fill + free_space_height - unaligned_block[2],
                                          transpose)
                unaligned_block, up, free_space_height = self._find_unaligned_block(
                    domain,
                    supporters,
                    transpose
                )
            else:
                # The block has space below or above it but not wide enough to
                # move, there must be another unaliged block below or above it
                new_domain = (
                    (domain[0] if up
                     else unaligned_block[0] + unaligned_block[2]),
                    domain[1],
                    (unaligned_block[0] + unaligned_block[2] if up
                     else domain[2] - unaligned_block[0] - unaligned_block[2]),
                    domain[3]
                )
                unaligned_block, up, free_space_height = self._find_unaligned_block(
                    new_domain,
                    supporters,
                    transpose
                )

    def _find_unaligned_block(self, domain, supporters, transpose):
        empty_space = None
        left = True
        for widget, pos in self._get_widgets_in_block(*domain, transpose):
            if widget in supporters:
                continue

            for i in range(pos[0], pos[0] + pos[2]):
                if pos[1] > domain[1]:
                    if not self._item_at_position(i, pos[1] - 1, transpose):
                        empty_space = (i, pos[1] - 1)
                        break
                if pos[1] + pos[3] < domain[1] + domain[3]:
                    if not self._item_at_position(i, pos[1] + pos[3],
                                                  transpose):
                        left = False
                        empty_space = (i, pos[1] + pos[3])
                        break

            if empty_space:
                # Now find out if it has a support widget on top or beneath it
                top_item = bottom_item = top_row = bottom_row =None
                offset = 1
                while not top_item or not bottom_item:
                    if not top_item:
                        top_row = empty_space[0] - offset
                        top_item = self._item_at_position(top_row,
                                                          empty_space[1],
                                                          transpose)
                    if not bottom_item:
                        bottom_row = empty_space[0] + offset
                        bottom_item = self._item_at_position(bottom_row,
                                                             empty_space[1],
                                                             transpose)
                    offset += 1

                if top_item.widget() in supporters:
                    critical_block = self._find_critical_block(
                        bottom_row,
                        empty_space[1] + (1 if left else 0),
                        True,
                        not left,
                        transpose
                    )
                    return critical_block, True, bottom_row - top_row - 1
                elif bottom_item.widget() in supporters:
                    critical_block = self._find_critical_block(
                        top_row + 1,
                        empty_space[1] + (1 if left else 0),
                        False,
                        not left,
                        transpose
                    )
                    return critical_block, False, bottom_row - top_row - 1
                # The empty space should've had a support widget either above
                # or below it. It seems we reached an invalid state.
                # TODO: somehow dump the state of the whole layout
                raise ValueError('Invalid unaligned block found')
        return None, None, None

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
            item = self._item_at_position(index - 1 if up else index,
                                          col, transpose)
            if item:
                pos = self._get_item_position(item.widget(), transpose)
                if pos[1] == col:
                    index = pos[0] if up else pos[0] + pos[2]
                    reached_end = index == 0 if up else index == rows
                else:
                    reached_end = True
            else:
                index += -1 if up else 1
                reached_end = index == 0 if up else index == rows

        return row - index if up else index - row

    def _get_supporters(self, block, before, transpose):
        """Returns a tree of "support" widgets for the specified block.

        A support widget is a widget that is (directly or indirectly) "pushed"
        by the specified block (or widget) when it grows.

        Args:
            block: The widget (or position) for which to find supporters.
            before: The direction in which to find supporters (True for up,
                    False for down).
            transpose: If True, will behave as if the grid was transposed.
        """
        supporters = []
        pos = self._get_item_position(block, transpose) \
              if isinstance(block, QWidget) else block
        pivot = pos[0] - 1 if before else pos[0] + pos[2]
        col = pos[1]
        upper_limit = self._row_count(transpose)
        within_limits = (pivot >= 0) if before else (pivot < upper_limit)
        if within_limits:
            while col < pos[1] + pos[3]:
                item = self._item_at_position(pivot, col, transpose)
                if item:
                    supporter = item.widget()
                    supporters.append(supporter)
                    supporter_pos = self._get_item_position(supporter,
                                                            transpose)
                    col = supporter_pos[1] + supporter_pos[3]
                else:
                    col += 1
        return TreeNode(block, [self._get_supporters(w, before, transpose)
                                for w in supporters])

    def _find_empty_block(self, transpose):
        """Finds a block made entirely of empty space.

        Returns a tuple in the form of (i, j, rowspan, colspan). the block is
        of the largest possible size.

        Args:
            transpose: If True, will behave as if the grid was transposed.
        """
        #TODO: find a way to avoid looping over every row
        i = -1
        found = False
        while not found and i < self._row_count(transpose) - 1:
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
        # But hang on, there could be empty space on the other side of this
        # border, so we're gonna check and shrink it if necessary
        item = self._item_at_position(
            i + (-first_border if up else first_border - 1),
            j - 1 if left else j,
            transpose
        )
        while not item:
            first_border -= 1
            item = self._item_at_position(
                i + (first_border - 1) * (-1 if up else 1),
                j - 1 if left else j,
                transpose
            )

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

    def _get_widgets_in_block(self, i, j, rowspan, colspan, transpose):
        #TODO: find a way to avoid looping over every row
        done = set()
        row = i
        while row < i + rowspan:
            col = 0
            while col < j + colspan:
                item = self._item_at_position(row, col, transpose)
                if item:
                    widget = item.widget()
                    pos = self._get_item_position(widget, transpose)
                    if widget not in done:
                        yield widget, pos
                        done.add(widget)
                    col += pos[3]
                else:
                    col += 1
            row += 1

    def _displace_and_resize(self, i, j, rowspan, colspan, displacement,
                             growth, transpose):
        heights = []
        virtual_block = self._virtualize_block(i, j, rowspan, colspan,
                                               transpose)
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
            marked_rows = []
            while growth:
                height, row = best(heights)

                if height == 1 and growth < 0:
                    raise SplitLimitException

                marked_rows.append(row)
                if growth < 0:
                    growth += 1
                    heights[heights.index((height, row))] = (height - 1, row)
                else:
                    growth -= 1
                    heights[heights.index((height, row))] = (height + 1, row)

            new_virtual_block = []
            for index, row in enumerate(virtual_block):
                if index in marked_rows:
                    if growth > 0:
                        new_virtual_block.append(row)
                        new_virtual_block.append(row)
                    else:
                        # Nothing, we skip this row
                        pass
                else:
                    new_virtual_block.append(row)
            virtual_block = new_virtual_block

        materialized = self._materialize_virtual_block(i + displacement, j,
                                                       virtual_block)
        for widget, pos in materialized:
            self.removeWidget(widget)
            self._add_widget(widget, *pos, transpose)

    def _virtualize_block(self, i, j, rowspan, colspan, transpose):
        return [
            [self._item_at_position(row, col, transpose).widget()
             for col in range(j, j + colspan)]
            for row in range(i, i + rowspan)
        ]

    def _materialize_virtual_block(self, i, j, virtual_block):
        block = {}
        for row in range(len(virtual_block)):
            for col in range(len(virtual_block[0])):
                widget = virtual_block[row][col]
                if widget in block:
                    pos = block[widget][:2]
                    block[widget] = (*pos,
                                     i + row - pos[0] + 1,
                                     j + col - pos[1] + 1)
                else:
                    block[widget] = (i + row, j + col, 1, 1)

        return block.items()


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

    def all_nodes(self):
        return {self.value}.union(*(child.all_nodes()
                                    for child in self.children))
