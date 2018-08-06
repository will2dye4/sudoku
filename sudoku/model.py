import abc
import itertools

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


class Column(Enum):
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
        for row in range(1, 10):
            row_str = '|'
            for column in Column:
                row_str += f' {self.get_cell_value(column, row) or "."}'
                if column in {Column.C, Column.F}:
                    row_str += ' |'
            row_str += ' |\n'
            text += row_str
            if row in {3, 6}:
                text += horizontal_line
        text += horizontal_line
        return text

    @classmethod
    def from_string(cls, string: AnyStr) -> 'Sudoku':
        # See http://norvig.com/sudoku.html
        sudoku = cls()
        row = 1
        column = Column.A
        cell_count = 0
        for char in string:
            values = None
            if char in '123456789':
                values = (column, row, int(char))
            elif char in '0.':
                values = (column, row, None)
            if values is not None:
                sudoku.add_cell(*values)
                cell_count += 1
                if divmod(cell_count, 9)[1] == 0:
                    row += 1
                    column = Column.A
                else:
                    column = Column[chr(ord(column.name) + 1)]

        if cell_count != 81:
            raise ValueError('Invalid sudoku string')
        return sudoku

    @abc.abstractmethod
    def add_cell(self, column: Column, row: int, value: Optional[int]) -> None:
        raise NotImplemented

    @abc.abstractmethod
    def get_cell_value(self, column: Column, row: int) -> Optional[int]:
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
    row: int
    column: Column
    value: Optional[int] = None


@dataclass
class MatrixSudoku(Sudoku):
    """Class representing a sudoku puzzle."""
    cells: List[List[Cell]]

    def __init__(self, cells: List[List[Cell]] = None):
        if cells is None:
            cells = [
                [
                    Cell(row, column)
                    for column in Column
                ]
                for row in range(1, 10)
            ]
        self.cells = cells

    def add_cell(self, column: Column, row: int, value: Optional[int]) -> None:
        self[column, row] = value

    def __getitem__(self, item: Union[Cell, Tuple[Column, int]]) -> Optional[int]:
        if isinstance(item, tuple):
            column, row = item
        else:
            column, row = item.column, item.row
        return self.cells[row - 1][column.value - 1].value

    def __setitem__(self, item: Union[Cell, Tuple[Column, int]], value: Optional[int]) -> None:
        if isinstance(item, tuple):
            column, row = item
        else:
            column, row = item.column, item.row
        self.cells[row - 1][column.value - 1].value = value

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

    def get_row(self, row: int) -> List[Cell]:
        return self.cells[row - 1]

    def get_column(self, column: Column) -> List[Cell]:
        return self.columns[column.value - 1]

    def get_box(self, box_num: int) -> List[Cell]:
        return self.boxes[box_num - 1]

    def get_next_empty_cell(self) -> Optional[Cell]:
        return next((cell for cell in self if cell.value is None), None)

    def get_cell_value(self, column: Column, row: int) -> Optional[int]:
        return self[column, row]

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
