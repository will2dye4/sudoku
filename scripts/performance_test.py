#!/usr/bin/env python3.7

import multiprocessing
import pprint
import threading
import time

from concurrent.futures import ProcessPoolExecutor as Pool
from dataclasses import dataclass
from typing import (
    AnyStr,
    List,
    Optional,
)

from sudoku import (
    SolutionAlgorithm,
    Sudoku,
    SudokuSolver,
)
from sudoku.sample_puzzles import (
    empty_cell_count_puzzles,
    hard_puzzles,
)


@dataclass
class Trial:
    name: AnyStr
    empty_cells: int
    possibilities_tried: int
    backtracks: int
    total_time: float


class Task:

    def __init__(self, puzzle_string: AnyStr, algorithm: SolutionAlgorithm,
                 trial_name: AnyStr, timeout_minutes: Optional[int] = None) -> None:
        self.puzzle_string = puzzle_string
        self.algorithm = algorithm
        self.timeout_seconds = timeout_minutes * 60 if timeout_minutes is not None else None
        self.name = trial_name
        self.solve_time = None
        self.solved_sudoku = None

    def solve(self, solver: SudokuSolver) -> None:
        start_time = time.time()
        self.solved_sudoku = solver.solve()
        self.solve_time = time.time() - start_time

    def run(self) -> Optional[Trial]:
        sudoku = self.algorithm.value.sudoku_type.from_string(self.puzzle_string)
        empty_cells = Sudoku.GRID_SIZE - len(sudoku.clue_cells)
        solver = self.algorithm.value.solver_type(sudoku)
        solve_thread = threading.Thread(target=self.solve, args=(solver,), daemon=True)
        solve_thread.run()

        start_time = time.time()
        if self.timeout_seconds is None:
            should_loop = lambda: solve_thread.is_alive()
        else:
            should_loop = lambda: time.time() - start_time < self.timeout_seconds

        while should_loop():
            if not solve_thread.is_alive():
                break
            time.sleep(10)

        if solve_thread.is_alive():
            solve_thread.join(timeout=1)

        if self.solved_sudoku is None:
            return None

        return Trial(
            self.name,
            empty_cells,
            solver.possibilities_tried,
            solver.backtracks,
            self.solve_time
        )


def test_brute_force_solve_time() -> List[Trial]:
    return test_solve_time(hard_puzzles, SolutionAlgorithm.BRUTE_FORCE, timeout_minutes=30)


def test_constraint_based_solve_time() -> List[Trial]:
    return test_solve_time(hard_puzzles, SolutionAlgorithm.CONSTRAINT_BASED)


def test_dlx_solve_time() -> List[Trial]:
    return test_solve_time(hard_puzzles, SolutionAlgorithm.DANCING_LINKS, timeout_minutes=60)


def test_empty_cells_vs_solve_time(algorithm: SolutionAlgorithm) -> List[Trial]:
    return test_solve_time(empty_cell_count_puzzles, algorithm, 'empty')


def test_solve_time(puzzle_strings: List[AnyStr], algorithm: SolutionAlgorithm,
                    trial_tag: Optional[AnyStr] = None, timeout_minutes: Optional[int] = None) -> List[Trial]:
    results = []
    count_fmt = f'0{len(str(len(puzzle_strings)))}d'    # ex: '02d' if len(puzzle_strings) is 2 digits

    def future_done(future):
        trial = future.result()
        if trial is None:
            print(f'Trial {trial.name} timed out')
        else:
            total_time = trial.total_time
            print(f'Trial {trial.name} completed in {total_time:0.2f} seconds')
            results.append(trial)

    with Pool(max_workers=multiprocessing.cpu_count()) as pool:
        for i, puzzle_string in enumerate(puzzle_strings):
            alg_name = 'brute' if algorithm == SolutionAlgorithm.BRUTE_FORCE else \
                'constraint' if algorithm == SolutionAlgorithm.CONSTRAINT_BASED else 'dlx'
            trial_name = f'{alg_name}-{i+1:{count_fmt}}'
            if trial_tag:
                trial_name += f'-{trial_tag}'
            task = Task(puzzle_string, algorithm, trial_name, timeout_minutes)
            future = pool.submit(task.run)
            future.add_done_callback(future_done)

    return sorted(results, key=lambda trial: trial.name)


if __name__ == '__main__':
    pprint.pprint(test_brute_force_solve_time())
