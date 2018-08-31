#!/usr/bin/env python3.7

import multiprocessing
import pprint
import queue
import time

from dataclasses import dataclass
from typing import (
    AnyStr,
    Callable,
    List,
    Optional,
)

from sudoku import (
    SolutionAlgorithm,
    Sudoku,
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


class SudokuProcess(multiprocessing.Process):

    def __init__(self, puzzle_string: AnyStr, algorithm: SolutionAlgorithm,
                 trial_name: AnyStr, results_queue: multiprocessing.Queue) -> None:
        super().__init__(name=trial_name)
        self.puzzle_string = puzzle_string
        self.algorithm = algorithm
        self.results_queue = results_queue

    def run(self) -> None:
        sudoku = self.algorithm.value.sudoku_type.from_string(self.puzzle_string)
        empty_cells = Sudoku.GRID_SIZE - len(sudoku.clue_cells)
        solver = self.algorithm.value.solver_type(sudoku)

        start_time = time.time()
        solved = solver.solve()
        end_time = time.time()

        if solved is not None:
            total_time = end_time - start_time
            print(f'Trial {self.name} completed in {total_time:0.2f} seconds')
            self.results_queue.put(
                Trial(self.name, empty_cells, solver.possibilities_tried, solver.backtracks, total_time)
            )


class PerformanceTestRunner:

    MAX_WORKERS = multiprocessing.cpu_count()

    def __init__(self, puzzle_strings: List[AnyStr], algorithm: SolutionAlgorithm,
                 trial_tag: Optional[AnyStr] = None, timeout_minutes: Optional[int] = None) -> None:
        self.puzzle_strings = puzzle_strings
        self.algorithm = algorithm
        self.trial_tag = trial_tag
        self.timeout_seconds = timeout_minutes * 60 if timeout_minutes is not None else None
        self.count_format = f'0{len(str(len(puzzle_strings)))}d'  # ex: '02d' if len(puzzle_strings) is 2 digits
        self.processes = {}
        self.process_queue = queue.Queue()
        self.results_queue = multiprocessing.Queue()

    def await_next_process_completion_or_timeout(self) -> None:
        self.block_while(lambda: len(self.processes) == self.MAX_WORKERS)

    def await_all(self) -> None:
        self.block_while(lambda: len(self.processes) > 0)

    def block_while(self, condition: Callable[[], bool]) -> None:
        while condition():
            removed = None
            for pid in self.processes.keys():
                process, start_time = self.processes[pid]
                if not process.is_alive():
                    # found a finished process - remove it
                    removed = pid
                elif self.timeout_seconds is not None and time.time() - start_time > self.timeout_seconds:
                    # process timed out - kill it
                    print(f'Trial {process.name} timed out')
                    process.terminate()
                    process.join()
                    removed = pid

                if removed is not None:
                    del self.processes[pid]
                    break

            if removed is None:
                time.sleep(1)

    def run(self) -> None:
        while not self.process_queue.empty():
            self.await_next_process_completion_or_timeout()
            process = self.process_queue.get()
            print(f'Running trial {process.name}')
            process.start()
            self.processes[process.pid] = (process, time.time())
        self.await_all()

    def submit(self, puzzle_string: AnyStr, trial_name: AnyStr) -> None:
        self.process_queue.put(SudokuProcess(puzzle_string, self.algorithm, trial_name, self.results_queue))

    def get_results(self) -> List[Trial]:
        results = []
        while not self.results_queue.empty():
            results.append(self.results_queue.get())
        return sorted(results, key=lambda trial: trial.name)

    def run_tests(self) -> List[Trial]:
        for i, puzzle_string in enumerate(self.puzzle_strings):
            alg_name = 'brute' if self.algorithm == SolutionAlgorithm.BRUTE_FORCE else \
                'constraint' if self.algorithm == SolutionAlgorithm.CONSTRAINT_BASED else 'dlx'
            trial_name = f'{alg_name}-{i+1:{self.count_format}}'
            if self.trial_tag:
                trial_name += f'-{self.trial_tag}'
            self.submit(puzzle_string, trial_name)

        self.run()
        return self.get_results()


def test_brute_force_solve_time(timeout_minutes: int = 30) -> List[Trial]:
    return test_solve_time(hard_puzzles, SolutionAlgorithm.BRUTE_FORCE, timeout_minutes=timeout_minutes)


def test_constraint_based_solve_time() -> List[Trial]:
    return test_solve_time(hard_puzzles, SolutionAlgorithm.CONSTRAINT_BASED)


def test_dlx_solve_time(timeout_minutes: int = 60) -> List[Trial]:
    return test_solve_time(hard_puzzles, SolutionAlgorithm.DANCING_LINKS, timeout_minutes=timeout_minutes)


def test_empty_cells_vs_solve_time(algorithm: SolutionAlgorithm) -> List[Trial]:
    return test_solve_time(empty_cell_count_puzzles, algorithm, 'empty')


def test_solve_time(puzzle_strings: List[AnyStr], algorithm: SolutionAlgorithm,
                    trial_tag: Optional[AnyStr] = None, timeout_minutes: Optional[int] = None) -> List[Trial]:
    return PerformanceTestRunner(puzzle_strings, algorithm, trial_tag, timeout_minutes).run_tests()


if __name__ == '__main__':
    pprint.pprint(test_brute_force_solve_time())
