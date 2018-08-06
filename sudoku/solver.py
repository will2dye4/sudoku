import logging

from sudoku.model import (
    DictSudoku,
    MatrixSudoku,
    Sudoku,
)


logger = logging.getLogger(__name__)


def solve(sudoku: Sudoku) -> None:
    if isinstance(sudoku, MatrixSudoku):
        result = brute_force_solve(sudoku)
    elif isinstance(sudoku, DictSudoku):
        result = constraint_solve(sudoku)
    else:
        raise TypeError('Expected instance of DictSudoku or MatrixSudoku')

    if not result:
        raise ValueError('Failed to solve sudoku')


def brute_force_solve(sudoku: MatrixSudoku) -> bool:
    if sudoku.is_solved():
        return True
    cell = sudoku.get_next_empty_cell()
    if cell is None:
        return False
    for value in range(1, 10):
        logger.debug(f'Trying {value} for {cell.name}')
        logger.debug(str(sudoku))
        sudoku[cell] = value
        if sudoku.is_valid() and brute_force_solve(sudoku):
            return True
    sudoku[cell] = None
    return False


def constraint_solve(sudoku: DictSudoku) -> bool:
    if sudoku.is_solved():
        return True
    # TODO
