import abc
import logging

from collections import namedtuple
from enum import Enum
from typing import (
    AnyStr,
    Callable,
    Dict,
    Generic,
    Iterable,
    List,
    Optional,
    TypeVar,
)

from sudoku.dlx import DLX
from sudoku.model import (
    CELLS,
    Cell,
    DictSudoku,
    MatrixSudoku,
    Row,
    Sudoku,
)


logger = logging.getLogger(__name__)


T = TypeVar('T')


class SudokuSolver(abc.ABC, Generic[T]):
    """Abstract base class for a sudoku solver."""

    def __init__(self, sudoku: T, event_listener: Optional[Callable[[Sudoku], None]] = None):
        self.sudoku = sudoku
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
    def solve(self) -> Optional[Sudoku]:
        raise NotImplemented


class BruteForceSolver(SudokuSolver[MatrixSudoku]):

    def solve(self) -> Optional[Sudoku]:
        if self.sudoku.is_solved():
            return self.sudoku
        cell = self.sudoku.get_next_empty_cell()
        if cell is None:
            return None
        for value in range(1, 10):
            logger.debug(f'Trying {value} for {cell.name}')
            logger.debug(str(self.sudoku))
            self.on_grid_changed(self.sudoku)
            self.sudoku[cell] = value
            self.possibilities_tried += 1
            if self.sudoku.is_valid():
                solved = self.solve()
                if solved:
                    return solved
        self.sudoku[cell] = None
        self.backtracks += 1
        return None


class ConstraintBasedSolver(SudokuSolver[DictSudoku]):

    def solve(self, sudoku: DictSudoku = None) -> Optional[Sudoku]:
        if sudoku is None:
            sudoku = self.sudoku
        if sudoku.is_solved():
            return sudoku
        _, cell = min((len(sudoku.values[c]), c) for c in CELLS if len(sudoku.values[c]) > 1)
        for value in sudoku.values[cell]:
            logger.debug(f'Trying {value} for {cell}')
            logger.debug(str(sudoku))
            new_sudoku = sudoku.clone()
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


class DLXSolver(SudokuSolver[MatrixSudoku]):

    def __init__(self, sudoku: MatrixSudoku, event_listener: Optional[Callable[[Sudoku], None]] = None,
                 minimize_branching: bool = False):
        self.minimize_branching = minimize_branching
        self.dlx = None
        super().__init__(sudoku, event_listener)

    @property
    def possibilities_tried(self) -> int:
        if self.dlx is None:
            return 0
        return self.dlx.possibilities_tried

    @possibilities_tried.setter
    def possibilities_tried(self, value: int) -> None:
        pass

    @property
    def backtracks(self) -> int:
        if self.dlx is None:
            return 0
        return self.dlx.backtracks

    @backtracks.setter
    def backtracks(self, value: int) -> None:
        pass

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

    def get_matrix(self) -> List[List[int]]:
        matrix = []
        for row in Row:
            for column in range(1, 10):
                cell_value = self.sudoku.get_cell_value(row, column)
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
        return matrix

    @staticmethod
    def get_cell_dict_for_solution(solution: List[List[AnyStr]]) -> Dict[AnyStr, int]:
        cell_dict = {}
        for matched_constraints in solution:
            row = None
            column = None
            value = None
            for constraint in matched_constraints:
                first_part, first_value, second_part, second_value = constraint
                if first_part == 'R' and second_part == 'C':
                    row = chr(ord('A') + int(first_value) - 1)
                    column = second_value
                elif second_part == '#':
                    value = int(second_value)
            cell_dict[f'{row}{column}'] = value
        return cell_dict

    def get_solved_sudoku(self, solution: List[List[AnyStr]]) -> MatrixSudoku:
        cell_dict = self.get_cell_dict_for_solution(solution)
        cells = []
        for row in Row:
            matrix_row = []
            for column in range(1, 10):
                matrix_row.append(Cell(row, column, cell_dict[f'{row.name}{column}']))
            cells.append(matrix_row)
        return MatrixSudoku(cells)

    def solve(self) -> Optional[Sudoku]:
        matrix = self.get_matrix()
        self.dlx = DLX(matrix, column_names=ALL_CONSTRAINTS, minimize_branching=self.minimize_branching)
        solution = self.dlx.search()
        if solution is None:
            return None
        if len(solution) != 81 or not all(len(constraints) == 4 for constraints in solution):
            raise ValueError(f'DLX search produced an invalid solution: {solution}')
        return self.get_solved_sudoku(solution)


AlgorithmConfig = namedtuple('AlgorithmConfig', ['sudoku_type', 'solver_type'])


class SolutionAlgorithm(Enum):
    BRUTE_FORCE = AlgorithmConfig(sudoku_type=MatrixSudoku, solver_type=BruteForceSolver)
    CONSTRAINT_BASED = AlgorithmConfig(sudoku_type=DictSudoku, solver_type=ConstraintBasedSolver)
    DANCING_LINKS = AlgorithmConfig(sudoku_type=MatrixSudoku, solver_type=DLXSolver)


def solve(sudoku: Optional[Sudoku] = None, sudoku_string: Optional[AnyStr] = None,
          algorithm: SolutionAlgorithm = SolutionAlgorithm.CONSTRAINT_BASED,
          event_listener: Optional[Callable[[Sudoku], None]] = None) -> Optional[Sudoku]:
    if sudoku is None and sudoku_string is None:
        raise ValueError('Must provide a Sudoku instance or a sudoku string')

    sudoku_type, solver_type = algorithm.value

    if sudoku is None:
        sudoku = sudoku_type.from_string(sudoku_string)
    elif not isinstance(sudoku, sudoku_type):
        raise ValueError(f'Algorithm {algorithm.name} requires an instance of {sudoku_type}')

    solver = solver_type(sudoku, event_listener=event_listener)
    return solver.solve()


def get_solver(sudoku: Sudoku, algorithm: SolutionAlgorithm) -> SudokuSolver:
    sudoku_type, solver_type = algorithm.value
    if not isinstance(sudoku, sudoku_type):
        raise ValueError(f'Algorithm {algorithm.name} requires an instance of {sudoku_type}')
    return solver_type(sudoku)


if __name__ == '__main__':
    # sudoku = MatrixSudoku.from_string("""
    #     +-------+-------+-------+
    #     | 4 . . | . . . | 8 . 5 |
    #     | . 3 . | . . . | . . . |
    #     | . . . | 7 . . | . . . |
    #     +-------+-------+-------+
    #     | . 2 . | . . . | . 6 . |
    #     | . . . | . 8 . | 4 . . |
    #     | . . . | . 1 . | . . . |
    #     +-------+-------+-------+
    #     | . . . | 6 . 3 | . 7 . |
    #     | 5 . . | 2 . . | . . . |
    #     | 1 . 4 | . . . | . . . |
    #     +-------+-------+-------+
    # """)
    sudoku = MatrixSudoku.from_string("""
        6 . 2 |4 8 . |9 3 7 
        8 3 4 |6 . 9 |1 5 2 
        9 7 1 |. 2 5 |8 6 4 
        ------+------+------
        . 6 7 |8 1 2 |5 . 3 
        3 1 5 |7 9 . |6 2 8 
        2 9 . |5 6 3 |. 7 1 
        ------+------+------
        . 8 . |. 3 . |2 . 5 
        5 . 3 |1 . 6 |. 8 . 
        7 . 9 |. 5 8 |3 1 6
    """)
    solver = DLXSolver(sudoku, minimize_branching=True)
    solved = solver.solve()
    if solved:
        print(str(solved))
    else:
        print('Failed to solve sudoku')
