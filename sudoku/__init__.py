from sudoku.model import (
    DictSudoku,
    MatrixSudoku,
    Row,
    Sudoku,
)
from sudoku.solver import (
    BruteForceSolver,
    ConstraintBasedSolver,
    DLXSolver,
    SolutionAlgorithm,
    get_solver,
    solve,
)

input_string = """
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
"""

ds = DictSudoku.from_string(input_string)
ms = MatrixSudoku.from_string(input_string)
