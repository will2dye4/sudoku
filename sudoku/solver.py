import abc
import logging

from typing import (
    AnyStr,
    Callable,
    Iterable,
    Optional,
)

from sudoku.dlx import DLX
from sudoku.model import (
    CELLS,
    DictSudoku,
    MatrixSudoku,
    Row,
    Sudoku,
)


logger = logging.getLogger(__name__)


class SudokuSolver(abc.ABC):
    """Abstract base class for a sudoku solver."""

    def __init__(self, event_listener: Optional[Callable[[Sudoku], None]] = None):
        self.event_listener = event_listener
        self.possibilities_tried = 0
        self.backtracks = 0

    def on_grid_changed(self, sudoku: Sudoku) -> None:
        if self.event_listener is not None:
            try:
                self.event_listener(sudoku)
            except Exception:
                logger.exception('caught exception while running event listener')

    @abc.abstractmethod
    def solve(self, sudoku: Sudoku) -> Optional[Sudoku]:
        raise NotImplemented


class BruteForceSolver(SudokuSolver):

    def solve(self, sudoku: MatrixSudoku) -> Optional[Sudoku]:
        if sudoku.is_solved():
            return sudoku
        cell = sudoku.get_next_empty_cell()
        if cell is None:
            return None
        for value in range(1, 10):
            logger.debug(f'Trying {value} for {cell.name}')
            logger.debug(str(sudoku))
            self.on_grid_changed(sudoku)
            sudoku[cell] = value
            self.possibilities_tried += 1
            if sudoku.is_valid():
                solved = self.solve(sudoku)
                if solved:
                    return solved
        sudoku[cell] = None
        self.backtracks += 1
        return None


class ConstraintBasedSolver(SudokuSolver):

    def solve(self, sudoku: DictSudoku) -> Optional[Sudoku]:
        if sudoku.is_solved():
            return sudoku
        _, cell = min((len(sudoku.values[c]), c) for c in CELLS if len(sudoku.values[c]) > 1)
        for value in sudoku.values[cell]:
            logger.debug(f'Trying {value} for {cell}')
            logger.debug(str(sudoku))
            new_sudoku = DictSudoku(sudoku.values.copy())
            self.possibilities_tried += 1
            if new_sudoku.set_cell_value(Row[cell[0]], int(cell[1]), value):
                self.on_grid_changed(new_sudoku)
                solved = self.solve(new_sudoku)
                if solved:
                    return solved
        self.backtracks += 1
        return None


ROW_COLUMN_CONSTRAINTS = [f'R{r}C{c}' for r in range(1, 10) for c in range(1, 10)]
ROW_NUMBER_CONSTRAINTS = [f'R{r}#{n}' for r in range(1, 10) for n in range(1, 10)]
COLUMN_NUMBER_CONSTRAINTS = [f'C{c}#{n}' for c in range(1, 10) for n in range(1, 10)]
BOX_NUMBER_CONSTRAINTS = [f'B{b}#{n}' for b in range(1, 10) for n in range(1, 10)]
ALL_CONSTRAINTS = ROW_COLUMN_CONSTRAINTS + ROW_NUMBER_CONSTRAINTS + COLUMN_NUMBER_CONSTRAINTS + BOX_NUMBER_CONSTRAINTS


class DLXSolver(SudokuSolver):

    def __init__(self, event_listener: Optional[Callable[[Sudoku], None]] = None, minimize_branching: bool = False):
        self.minimize_branching = minimize_branching
        super().__init__(event_listener)

    @staticmethod
    def get_constraint_index(constraint: AnyStr) -> int:
        first_part, first_value, second_part, second_value = constraint
        if first_part == 'R' and second_part == 'C':
            offset = 0
        elif first_part == 'R' and second_part == '#':
            offset = len(ROW_COLUMN_CONSTRAINTS)
        elif first_part == 'C' and second_part == '#':
            offset = len(ROW_COLUMN_CONSTRAINTS) + len(ROW_NUMBER_CONSTRAINTS)
        else:
            offset = len(ROW_COLUMN_CONSTRAINTS) + len(ROW_NUMBER_CONSTRAINTS) + len(COLUMN_NUMBER_CONSTRAINTS)
        index = ((int(first_value) - 1) * 9) + int(second_value) - 1
        return offset + index

    def get_matching_constraint_indices(self, row: Row, column: int, value: int) -> Iterable[int]:
        row_col_index = self.get_constraint_index(f'R{row.value}C{column}')
        row_num_index = self.get_constraint_index(f'R{row.value}#{value}')
        col_num_index = self.get_constraint_index(f'C{column}#{value}')
        row_offset = (row.value - 1) // 3
        column_offset = ((column - 1) // 3) + 1
        box = (row_offset * 3) + column_offset
        box_num_index = self.get_constraint_index(f'B{box}#{value}')
        return row_col_index, row_num_index, col_num_index, box_num_index

    def solve(self, sudoku: Sudoku) -> Optional[Sudoku]:
        matrix = []
        for row in Row:
            for column in range(1, 10):
                cell_value = sudoku.get_cell_value(row, column)
                if cell_value is None:
                    candidates = {1, 2, 3, 4, 5, 6, 7, 8, 9}
                else:
                    candidates = {cell_value}
                for matrix_candidate in {1, 2, 3, 4, 5, 6, 7, 8, 9}:
                    matrix_row = [0] * len(ALL_CONSTRAINTS)
                    if matrix_candidate in candidates:
                        for index in self.get_matching_constraint_indices(row, column, matrix_candidate):
                            matrix_row[index] = 1
                    matrix.append(matrix_row)

        dlx = DLX(matrix, column_names=ALL_CONSTRAINTS, minimize_branching=self.minimize_branching)
        solution = dlx.search()
        if solution is None:
            print('no workie')
            return None
        print(solution)
        # TODO return sudoku


def get_solver(sudoku: Sudoku) -> SudokuSolver:
    if isinstance(sudoku, MatrixSudoku):
        return BruteForceSolver()
    if isinstance(sudoku, DictSudoku):
        return ConstraintBasedSolver()
    raise TypeError('Expected instance of DictSudoku or MatrixSudoku')


def solve(sudoku: Sudoku) -> Optional[Sudoku]:
    return get_solver(sudoku).solve(sudoku)


if __name__ == '__main__':
    solver = DLXSolver(minimize_branching=True)
    sudoku = MatrixSudoku.from_string("""
        +-------+-------+-------+
        | 4 . . | . . . | 8 . 5 |
        | . 3 . | . . . | . . . |
        | . . . | 7 . . | . . . |
        +-------+-------+-------+
        | . 2 . | . . . | . 6 . |
        | . . . | . 8 . | 4 . . |
        | . . . | . 1 . | . . . |
        +-------+-------+-------+
        | . . . | 6 . 3 | . 7 . |
        | 5 . . | 2 . . | . . . |
        | 1 . 4 | . . . | . . . |
        +-------+-------+-------+
    """)
    solver.solve(sudoku)
