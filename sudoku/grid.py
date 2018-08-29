import abc
import itertools
import re

from collections import defaultdict
from dataclasses import dataclass
from enum import Enum
from typing import (
    AnyStr,
    Dict,
    Iterable,
    List,
    Optional,
    Set,
    Tuple,
    Union,
)

from sudoku.utils.colorize import cyan


class Row(Enum):
    """Enumeration defining the valid rows in a sudoku grid."""
    A = 1
    B = 2
    C = 3
    D = 4
    E = 5
    F = 6
    G = 7
    H = 8
    I = 9

    def next(self, wrap: bool = True) -> 'Row':
        """Return the row after the current row."""
        if self == Row.I:
            if wrap:
                return Row.A
            raise ValueError(f'{str(self)} has no next row')
        return Row[chr(ord(self.name) + 1)]


@dataclass(unsafe_hash=True)
class Cell:
    """Class representing a single cell in a sudoku puzzle."""
    row: Row
    column: int
    value: Optional[int] = None

    @property
    def name(self) -> AnyStr:
        """Return the cell's name (e.g., 'C5')."""
        return f'{self.row.name}{self.column}'


def all_cells() -> Iterable[Cell]:
    """Generator that yields all cells (row/column pairs) in a sudoku grid."""
    for row in Row:
        for column in columns():
            yield Cell(row, column)


def columns() -> Iterable[int]:
    """Generator that yields all valid columns in a sudoku grid."""
    return range(1, 10)


class Sudoku(abc.ABC):
    """Abstract base class for a sudoku puzzle."""

    CELL_VALUES = {1, 2, 3, 4, 5, 6, 7, 8, 9}
    GRID_SIDE_LENGTH = 9
    GRID_SIZE = 81
    NON_DIGIT_REGEX = re.compile(r'[^.0-9]+')

    def __init__(self) -> None:
        """Initialize a Sudoku."""
        self.clue_cells = set()

    def __str__(self) -> AnyStr:
        """Return a string representation of the sudoku suitable for printing to the console."""
        return self.to_string()

    @classmethod
    def from_string(cls, string: AnyStr) -> 'Sudoku':
        """Create a Sudoku instance from a string (see http://norvig.com/sudoku.html)."""
        sudoku = cls()
        row = Row.A
        column = 1
        cell_count = 0
        for char in string:
            values = None
            if char in '123456789':
                values = (row, column, int(char))
                sudoku.clue_cells.add(Cell(*values))
            elif char in '0.':
                values = (row, column, None)
            if values is not None:
                sudoku.set_cell_value(*values)
                cell_count += 1
                if divmod(cell_count, cls.GRID_SIDE_LENGTH)[1] == 0:
                    row = row.next()
                    column = 1
                else:
                    column += 1

        if cell_count != cls.GRID_SIZE:
            raise ValueError('Invalid sudoku string')
        return sudoku

    def to_string(self, colorize: bool = True, show_initial_state: bool = False) -> AnyStr:
        """Return a string representation of the sudoku, optionally colorized and/or showing the initial state."""
        horizontal_line = '+-------+-------+-------+\n'
        text = horizontal_line
        for row in Row:
            row_str = '|'
            for column in columns():
                cell_value = self.get_cell_value(row, column) or '.'
                if any(cell.row == row and cell.column == column for cell in self.clue_cells):
                    if colorize:
                        cell_value = cyan(cell_value)
                elif show_initial_state and cell_value != '.':
                    cell_value = '.'
                row_str += f' {cell_value}'
                if column in {3, 6}:
                    row_str += ' |'
            row_str += ' |\n'
            text += row_str
            if row in {Row.C, Row.F}:
                text += horizontal_line
        text += horizontal_line
        return text

    def get_condensed_string(self) -> AnyStr:
        """Return a condensed string representation of the sudoku (cell values only, no formatting)."""
        return self.NON_DIGIT_REGEX.sub('', self.to_string(colorize=False))

    @abc.abstractmethod
    def get_cell_value(self, row: Row, column: int) -> Optional[int]:
        """Return the value of the sudoku grid at the given row and column."""
        raise NotImplemented

    @abc.abstractmethod
    def set_cell_value(self, row: Row, column: int, value: Optional[int]) -> bool:
        """Set the value of the sudoku grid at the given row and column to the given value."""
        raise NotImplemented

    @abc.abstractmethod
    def is_valid(self) -> bool:
        """Return True IFF the sudoku is valid (does not violate any rules)."""
        raise NotImplemented

    @abc.abstractmethod
    def is_solved(self) -> bool:
        """Return True IFF the sudoku is solved."""
        raise NotImplemented


@dataclass
class MatrixSudoku(Sudoku):
    """Sudoku subclass representing a sudoku puzzle as a 2D matrix of cells."""
    cells: List[List[Cell]]

    def __init__(self, cells: List[List[Cell]] = None) -> None:
        """Initialize a MatrixSudoku, optionally with a matrix of cells."""
        super().__init__()
        if cells is None:
            cells = [
                [
                    Cell(row, column)
                    for column in columns()
                ]
                for row in Row
            ]
        else:
            self.clue_cells |= {cell for cell in all_cells()
                                if cells[cell.row.value - 1][cell.column - 1].value is not None}
        self.cells = cells

    def __getitem__(self, item: Union[Cell, Tuple[Row, int]]) -> Optional[int]:
        """Allow accessing the value of a given cell with `sudoku[row, column]` or `sudoku[cell]`."""
        if isinstance(item, tuple):
            row, column = item
        else:
            row, column = item.row, item.column
        return self.cells[row.value - 1][column - 1].value

    def __setitem__(self, item: Union[Cell, Tuple[Row, int]], value: Optional[int]) -> None:
        """Allow setting the value of a given cell with `sudoku[row, column] = value` or `sudoku[cell] = value`."""
        if isinstance(item, tuple):
            row, column = item
        else:
            row, column = item.row, item.column
        self.cells[row.value - 1][column - 1].value = value

    def __iter__(self) -> Iterable[Cell]:
        """Return an iterator that iterates over all cells in the sudoku grid."""
        return itertools.chain(*self.cells)

    @property
    def rows(self) -> List[List[Cell]]:
        """Property for accessing the rows in the sudoku grid."""
        return self.cells

    @property
    def columns(self) -> List[List[Cell]]:
        """Property for accessing the columns in the sudoku grid."""
        return list(list(col) for col in zip(*self.cells))

    @property
    def boxes(self) -> List[List[Cell]]:
        """Property for accessing the 3x3 boxes in the sudoku grid."""
        return [
            [
                self.cells[row + i][col + j]
                for i in range(3)
                for j in range(3)
            ]
            for col in range(0, 9, 3)
            for row in range(0, 9, 3)
        ]

    def get_row(self, row: Row) -> List[Cell]:
        """Return a list of cells representing the given row."""
        return self.cells[row.value - 1]

    def get_column(self, column: int) -> List[Cell]:
        """Return a list of cells representing the given column."""
        return self.columns[column - 1]

    def get_box(self, box_num: int) -> List[Cell]:
        """Return a list of cells representing the given box."""
        return self.boxes[box_num - 1]

    def get_next_empty_cell(self) -> Optional[Cell]:
        """Return the next cell that does not yet have a value (if any)."""
        return next((cell for cell in self if cell.value is None), None)

    def get_cell_value(self, row: Row, column: int) -> Optional[int]:
        """Return the value of the sudoku grid at the given row and column."""
        return self[row, column]

    def set_cell_value(self, row: Row, column: int, value: Optional[int]) -> bool:
        """Set the value of the sudoku grid at the given row and column to the given value."""
        self[row, column] = value
        return True

    def is_valid(self) -> bool:
        """Return True IFF the sudoku is valid (does not violate any rules)."""
        if not all(cell.value is None or cell.value in self.CELL_VALUES for cell in self):
            return False
        for units in (self.rows, self.columns, self.boxes):
            for unit in units:
                unit_values = [cell.value for cell in unit if cell.value is not None]
                if len(set(unit_values)) != len(unit_values):
                    return False
        return True

    def is_solved(self) -> bool:
        """Return True IFF the sudoku is solved."""
        return self.is_valid() and all(cell.value is not None for cell in self)


def cross(a, b) -> List[AnyStr]:
    """Return a list of all combinations of values from a and values from b."""
    return [x + y for x in a for y in b]


ROWS = [r.name for r in Row]
COLUMNS = [str(c) for c in columns()]
CELLS = cross(ROWS, COLUMNS)
ALL_UNITS = (
        [cross(ROWS, c) for c in COLUMNS] +
        [cross(r, COLUMNS) for r in ROWS] +
        [cross(rs, cs) for rs in ('ABC', 'DEF', 'GHI') for cs in ('123', '456', '789')]
)
UNITS = {
    c: [u for u in ALL_UNITS if c in u]
    for c in CELLS
}
PEERS = {
    c: set(itertools.chain(*UNITS[c])) - {c}
    for c in CELLS
}


class DictSudoku(Sudoku):
    """Sudoku subclass representing a sudoku puzzle as a dict."""

    def __init__(self, values: Dict[AnyStr, Set[int]] = None) -> None:
        """Initialize a DictSudoku, optionally with a dict of initial values."""
        super().__init__()
        if values is None:
            values = defaultdict(lambda: Sudoku.CELL_VALUES.copy())
        else:
            self.clue_cells |= {cell for cell in all_cells() if len(values.get(cell.name, set())) == 1}
        self.values = values

    @staticmethod
    def key(row: Row, column: int) -> AnyStr:
        """Return the dict key for the given row and column."""
        return f'{row.name}{column}'

    def get_cell_value(self, row: Row, column: int) -> Optional[int]:
        """Return the value of the sudoku grid at the given row and column."""
        value = self.values[self.key(row, column)]
        if len(value) == 1:
            return list(value)[0]
        return None

    def set_cell_value(self, row: Row, column: int, value: Optional[int]) -> bool:
        """Set the value of the sudoku grid at the given row and column to the given value."""
        if value is not None:
            other_values = self.values[self.key(row, column)] - {value}
            if not all(self.eliminate(row, column, val) for val in other_values):
                return False
        return True

    def eliminate(self, row: Row, column: int, value: int) -> bool:
        """Given a row, column, and value, eliminate possibilities from other cells that are no longer valid."""
        key = self.key(row, column)
        if value not in self.values[key]:
            return True
        self.values[key] = self.values[key] - {value}
        if len(self.values[key]) == 0:
            return False
        if len(self.values[key]) == 1:
            other_value = list(self.values[key])[0]
            if not all(self.eliminate(Row[c[0]], int(c[1]), other_value) for c in PEERS[key]):
                return False
        for unit in UNITS[key]:
            places = [c for c in unit if value in self.values[c]]
            if len(places) == 0:
                return False
            if len(places) == 1:
                place = places[0]
                if not self.set_cell_value(Row[place[0]], int(place[1]), value):
                    return False
        return True

    def is_valid(self) -> bool:
        """Fake is_valid implementation (does nothing)."""
        pass

    def is_solved(self) -> bool:
        """Return True IFF the sudoku is solved."""
        return all(len(self.values[c]) == 1 for c in CELLS)

    def clone(self) -> 'DictSudoku':
        """Return a new DictSudoku with the same values and clue cells as this instance."""
        new_sudoku = self.__class__(self.values.copy())
        new_sudoku.clue_cells = self.clue_cells
        return new_sudoku
