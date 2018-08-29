import time

from collections import namedtuple
from typing import Iterable

from sudoku import (
    SolutionAlgorithm,
    get_puzzle_by_name,
)


Trial = namedtuple('Trial', ['name', 'empty_cells', 'possibilities_tried', 'backtracks', 'total_time'])


def test_time_vs_number_of_empty_cells(algorithm: SolutionAlgorithm) -> Iterable[Trial]:
    results = []

    for i in range(1, 65):
        puzzle_string = get_puzzle_by_name(f'empty-{i}')
        sudoku_type, solver_type = algorithm.value
        sudoku = sudoku_type.from_string(puzzle_string)
        solver = solver_type(sudoku)

        print(f'Running {algorithm.name} algorithm with {i} empty cells')
        start = time.time()
        solved = solver.solve()
        end = time.time()

        if not solved:
            raise RuntimeError(f'Failed to solve puzzle with {i} empty cells using {algorithm.name} algorithm')

        alg_name = 'brute' if algorithm == SolutionAlgorithm.BRUTE_FORCE else \
            'constraint' if algorithm == SolutionAlgorithm.CONSTRAINT_BASED else 'dlx'
        results.append(Trial(f'{alg_name}-{i}-empty', i, solver.possibilities_tried, solver.backtracks, end - start))

    return results


if __name__ == '__main__':
    for algorithm in SolutionAlgorithm:
        test_time_vs_number_of_empty_cells(algorithm)
