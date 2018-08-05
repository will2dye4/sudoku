import itertools

from dataclasses import dataclass
from enum import Enum
from typing import (
    AnyStr,
    List,
    Optional,
    Tuple,
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


@dataclass
class Cell:
    """Class representing a single cell in a sudoku puzzle."""
    row: int
    column: Column
    value: Optional[int] = None


@dataclass
class Sudoku:
    """Class representing a sudoku puzzle."""
    cells: List[List[Cell]]

    @classmethod
    def from_string(cls, string: AnyStr) -> 'Sudoku':
        # See http://norvig.com/sudoku.html
        cells = []
        row = []
        row_num = 1
        column = Column.A
        for char in string:
            cell = None
            if char in '123456789':
                cell = Cell(row_num, column, int(char))
            elif char in '0.':
                cell = Cell(row_num, column)
            if cell is not None:
                row.append(cell)
                column = Column.A if column == Column.I else Column[chr(ord(column.name) + 1)]
            if len(row) == 9:
                cells.append(row)
                row = []
                row_num += 1
                column = Column.A
        if len(cells) != 9 or not all(len(row) == 9 for row in cells):
            raise ValueError('Invalid sudoku string')
        return cls(cells)

    def __getitem__(self, item: Tuple[Column, int]) -> Cell:
        column, row = item
        return self.cells[row - 1][column.value - 1]

    def __iter__(self) -> List[Cell]:
        return list(itertools.chain(*self.cells))

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
