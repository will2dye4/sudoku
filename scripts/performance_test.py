#!/usr/bin/env python3.7

import time

from collections import namedtuple
from typing import (
    AnyStr,
    Iterable,
    List,
)

from sudoku import (
    SolutionAlgorithm,
    Sudoku,
)
from sudoku.sample_puzzles import (
    empty_cell_count_puzzles,
    hard_puzzles,
)


Trial = namedtuple('Trial', ['name', 'empty_cells', 'possibilities_tried', 'backtracks', 'total_time'])


def test_brute_force_solve_time() -> Iterable[Trial]:
    return test_solve_time(hard_puzzles, SolutionAlgorithm.BRUTE_FORCE)


def test_constraint_based_solve_time() -> Iterable[Trial]:
    return test_solve_time(hard_puzzles, SolutionAlgorithm.CONSTRAINT_BASED)


def test_dlx_solve_time() -> Iterable[Trial]:
    return test_solve_time(hard_puzzles, SolutionAlgorithm.DANCING_LINKS)


def test_empty_cells_vs_solve_time(algorithm: SolutionAlgorithm) -> Iterable[Trial]:
    return test_solve_time(empty_cell_count_puzzles, algorithm, 'empty')


def test_solve_time(puzzle_strings: List[AnyStr], algorithm: SolutionAlgorithm, trial_tag: AnyStr = '') -> Iterable[Trial]:
    results = []
    sudoku_type, solver_type = algorithm.value

    for i, puzzle_string in enumerate(puzzle_strings):
        sudoku = sudoku_type.from_string(puzzle_string)
        empty_cells = Sudoku.GRID_SIZE - len(sudoku.clue_cells)
        solver = solver_type(sudoku)

        print(f'Running {algorithm.name} algorithm trial #{i+1} of {len(puzzle_strings)}')
        start = time.time()
        solved = solver.solve()
        end = time.time()

        if not solved:
            raise RuntimeError(f'Failed to solve trial puzzle #{i+1} using the {algorithm.name} algorithm')

        alg_name = 'brute' if algorithm == SolutionAlgorithm.BRUTE_FORCE else \
            'constraint' if algorithm == SolutionAlgorithm.CONSTRAINT_BASED else 'dlx'
        trial_name = f'{alg_name}-{i+1}'
        if trial_tag:
            trial_name += f'-{trial_tag}'
        results.append(Trial(trial_name, empty_cells, solver.possibilities_tried, solver.backtracks, end - start))

    return results


if __name__ == '__main__':
    for algorithm in SolutionAlgorithm:
        test_empty_cells_vs_solve_time(algorithm)
