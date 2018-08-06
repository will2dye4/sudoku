import abc
import itertools

from collections import defaultdict
from dataclasses import dataclass
from enum import Enum
from typing import (
    AnyStr,
    Iterable,
    List,
    Optional,
    Tuple,
    Union,
)


class Row(Enum):
    A = 1
    B = 2
    C = 3
    D = 4
    E = 5
    F = 6
    G = 7
    H = 8
    I = 9


class Sudoku(abc.ABC):
    """Abstract base class for a sudoku puzzle."""

    def __str__(self) -> AnyStr:
        horizontal_line = '+-------+-------+-------+\n'
        text = horizontal_line
        for row in Row:
            row_str = '|'
            for column in range(1, 10):
                row_str += f' {self.get_cell_value(row, column) or "."}'
                if column in {3, 6}:
                    row_str += ' |'
            row_str += ' |\n'
            text += row_str
            if row in {Row.C, Row.F}:
                text += horizontal_line
        text += horizontal_line
        return text

    @classmethod
    def from_string(cls, string: AnyStr) -> 'Sudoku':
        # See http://norvig.com/sudoku.html
        sudoku = cls()
        row = Row.A
        column = 1
        cell_count = 0
        for char in string:
            values = None
            if char in '123456789':
                values = (row, column, int(char))
            elif char in '0.':
                values = (row, column, None)
            if values is not None:
                sudoku.set_cell_value(*values)
                cell_count += 1
                if divmod(cell_count, 9)[1] == 0:
                    if row != Row.I:
                        row = Row[chr(ord(row.name) + 1)]
                    column = 1
                else:
                    column += 1

        if cell_count != 81:
            raise ValueError('Invalid sudoku string')
        return sudoku

    @abc.abstractmethod
    def get_cell_value(self, row: Row, column: int) -> Optional[int]:
        raise NotImplemented

    @abc.abstractmethod
    def set_cell_value(self, row: Row, column: int, value: Optional[int]) -> None:
        raise NotImplemented

    @abc.abstractmethod
    def is_valid(self) -> bool:
        raise NotImplemented

    @abc.abstractmethod
    def is_solved(self) -> bool:
        raise NotImplemented


@dataclass
class Cell:
    """Class representing a single cell in a sudoku puzzle."""
    row: Row
    column: int
    value: Optional[int] = None

    @property
    def name(self) -> AnyStr:
        return f'{self.row.name}{self.column}'


@dataclass
class MatrixSudoku(Sudoku):
    """Class representing a sudoku puzzle."""
    cells: List[List[Cell]]

    def __init__(self, cells: List[List[Cell]] = None):
        if cells is None:
            cells = [
                [
                    Cell(row, column)
                    for column in range(1, 10)
                ]
                for row in Row
            ]
        self.cells = cells

    def __getitem__(self, item: Union[Cell, Tuple[Row, int]]) -> Optional[int]:
        if isinstance(item, tuple):
            row, column = item
        else:
            row, column = item.row, item.column
        return self.cells[row.value - 1][column - 1].value

    def __setitem__(self, item: Union[Cell, Tuple[Row, int]], value: Optional[int]) -> None:
        if isinstance(item, tuple):
            row, column = item
        else:
            row, column = item.row, item.column
        self.cells[row.value - 1][column - 1].value = value

    def __iter__(self) -> Iterable[Cell]:
        return itertools.chain(*self.cells)

    @property
    def rows(self) -> List[List[Cell]]:
        return self.cells

    @property
    def columns(self) -> List[List[Cell]]:
        return list(list(col) for col in zip(*self.cells))

    @property
    def boxes(self) -> List[List[Cell]]:
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
        return self.cells[row.value - 1]

    def get_column(self, column: int) -> List[Cell]:
        return self.columns[column - 1]

    def get_box(self, box_num: int) -> List[Cell]:
        return self.boxes[box_num - 1]

    def get_next_empty_cell(self) -> Optional[Cell]:
        return next((cell for cell in self if cell.value is None), None)

    def get_cell_value(self, row: Row, column: int) -> Optional[int]:
        return self[row, column]

    def set_cell_value(self, row: Row, column: int, value: Optional[int]) -> None:
        self[row, column] = value

    def is_valid(self) -> bool:
        if not all(cell.value is None or cell.value in {1, 2, 3, 4, 5, 6, 7, 8, 9} for cell in self):
            return False
        for units in (self.rows, self.columns, self.boxes):
            for unit in units:
                unit_values = [cell.value for cell in unit if cell.value is not None]
                if len(set(unit_values)) != len(unit_values):
                    return False
        return True

    def is_solved(self) -> bool:
        return self.is_valid() and all(cell.value is not None for cell in self)


def cross(a, b):
    return [x + y for x in a for y in b]


ROWS = [r.name for r in Row]
COLUMNS = [str(c) for c in range(1, 10)]
SQUARES = cross(ROWS, COLUMNS)
ALL_UNITS = (
        [cross(ROWS, c) for c in COLUMNS] +
        [cross(r, COLUMNS) for r in ROWS] +
        [cross(rs, cs) for rs in ('ABC', 'DEF', 'GHI') for cs in ('123', '456', '789')]
)
UNITS = {
    s: [u for u in ALL_UNITS if s in u]
    for s in SQUARES
}
PEERS = {
    s: set(itertools.chain(*UNITS[s])) - {s}
    for s in SQUARES
}


class DictSudoku(Sudoku):

    def __init__(self):
        self.values = defaultdict(lambda: {1, 2, 3, 4, 5, 6, 7, 8, 9})

    @staticmethod
    def key(row: Row, column: int) -> AnyStr:
        return f'{row.name}{column}'

    def get_cell_value(self, row: Row, column: int) -> Optional[int]:
        value = self.values[self.key(row, column)]
        if len(value) == 1:
            return list(value)[0]
        return None

    def set_cell_value(self, row: Row, column: int, value: Optional[int]) -> None:
        if value is not None:
            other_values = self.values[self.key(row, column)] - {value}
            if not all(self.eliminate(row, column, val) for val in other_values):
                raise ValueError('Contradiction detected')

    def eliminate(self, row: Row, column: int, value: int) -> bool:
        key = self.key(row, column)
        if value not in self.values[key]:
            return True
        self.values[key] = self.values[key] - {value}
        if len(self.values[key]) == 0:
            return False
        if len(self.values[key]) == 1:
            other_value = list(self.values[key])[0]
            if not all(self.eliminate(Row[s[0]], int(s[1]), other_value) for s in PEERS[key]):
                return False
        for unit in UNITS[key]:
            places = [s for s in unit if value in self.values[s]]
            if len(places) == 0:
                return False
            if len(places) == 1:
                place = places[0]
                self.set_cell_value(Row[place[0]], int(place[1]), value)
        return True

    def is_valid(self) -> bool:
        pass

    def is_solved(self) -> bool:
        return all(len(self.values[s]) == 1 for s in SQUARES)
