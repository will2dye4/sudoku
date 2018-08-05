from sudoku.model import (
    Cell,
    Column,
    Sudoku,
)


def is_valid(sudoku: Sudoku) -> bool:
    if not all(cell.value is None or cell.value in {1, 2, 3, 4, 5, 6, 7, 8, 9} for cell in sudoku):
        return False
    for units in (sudoku.rows, sudoku.columns, sudoku.boxes):
        for unit in units:
            unit_values = [cell.value for cell in unit if cell.value is not None]
            if len(set(unit_values)) != len(unit_values):
                return False
    return True


def is_solved(sudoku: Sudoku) -> bool:
    return is_valid(sudoku) and all(cell.value is not None for cell in sudoku)


def get_next_empty_cell(sudoku: Sudoku) -> Cell:
    return next((cell for cell in sudoku if cell.value is None), None)


def solve(sudoku: Sudoku) -> None:
    if not _solve(sudoku):
        raise ValueError('failed to solve sudoku')


def _solve(sudoku: Sudoku) -> bool:
    if is_solved(sudoku):
        return True
    cell = get_next_empty_cell(sudoku)
    if cell is None:
        return False
    for value in range(1, 10):
        print(f'trying {value} for {cell.column.name}{cell.row}')
        pprint(sudoku)
        sudoku[cell.column, cell.row] = value
        if is_valid(sudoku) and _solve(sudoku):
            return True
    sudoku[cell.column, cell.row] = None
    return False


def pprint(sudoku: Sudoku) -> None:
    horizontal_line = '+-------+-------+-------+'
    print(horizontal_line)
    for i, row in enumerate(sudoku.rows):
        row_str = '|'
        for cell in row:
            row_str += f' {cell.value or "."}'
            if cell.column in {Column.C, Column.F, Column.I}:
                row_str += ' |'
        print(row_str)
        if i + 1 in {3, 6}:
            print(horizontal_line)
    print(horizontal_line)
