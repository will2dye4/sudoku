import abc
import logging

from typing import (
    Callable,
    Optional,
)

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
            if sudoku.is_valid():
                solved = self.solve(sudoku)
                if solved:
                    return solved
        sudoku[cell] = None
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
            if new_sudoku.set_cell_value(Row[cell[0]], int(cell[1]), value):
                self.on_grid_changed(new_sudoku)
                solved = self.solve(new_sudoku)
                if solved:
                    return solved
        return None


def get_solver(sudoku: Sudoku) -> SudokuSolver:
    if isinstance(sudoku, MatrixSudoku):
        return BruteForceSolver()
    if isinstance(sudoku, DictSudoku):
        return ConstraintBasedSolver()
    raise TypeError('Expected instance of DictSudoku or MatrixSudoku')


def solve(sudoku: Sudoku) -> Optional[Sudoku]:
    return get_solver(sudoku).solve(sudoku)
