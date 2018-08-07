import logging

from typing import Optional

from sudoku.model import (
    CELLS,
    DictSudoku,
    MatrixSudoku,
    Row,
    Sudoku,
)


logger = logging.getLogger(__name__)


def solve(sudoku: Sudoku) -> Optional[Sudoku]:
    if isinstance(sudoku, MatrixSudoku):
        result = brute_force_solve(sudoku)
    elif isinstance(sudoku, DictSudoku):
        result = constraint_solve(sudoku)
    else:
        raise TypeError('Expected instance of DictSudoku or MatrixSudoku')

    return result


def brute_force_solve(sudoku: MatrixSudoku) -> Optional[Sudoku]:
    if sudoku.is_solved():
        return sudoku
    cell = sudoku.get_next_empty_cell()
    if cell is None:
        return None
    for value in range(1, 10):
        logger.debug(f'Trying {value} for {cell.name}')
        logger.debug(str(sudoku))
        sudoku[cell] = value
        if sudoku.is_valid():
            solved = brute_force_solve(sudoku)
            if solved:
                return solved
    sudoku[cell] = None
    return None


def constraint_solve(sudoku: DictSudoku) -> Optional[Sudoku]:
    if sudoku.is_solved():
        return sudoku
    _, cell = min((len(sudoku.values[c]), c) for c in CELLS if len(sudoku.values[c]) > 1)
    for value in sudoku.values[cell]:
        logger.debug(f'Trying {value} for {cell}')
        logger.debug(str(sudoku))
        new_sudoku = DictSudoku(sudoku.values.copy())
        if new_sudoku.set_cell_value(Row[cell[0]], int(cell[1]), value):
            solved = constraint_solve(new_sudoku)
            if solved:
                return solved
    return None
