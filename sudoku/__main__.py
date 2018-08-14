import argparse
import itertools
import os
import sys

from typing import (
    AnyStr,
    List,
)

from sudoku import (
    SolutionAlgorithm,
    solve,
)
from sudoku.ui import SudokuApp


ALGORITHM_CHOICES = {
    ('brute', 'brute-force'): SolutionAlgorithm.BRUTE_FORCE,
    ('constraint', 'constraint-based'): SolutionAlgorithm.CONSTRAINT_BASED,
    ('dancing-links', 'dlx', 'exact-cover', 'hitting-set'): SolutionAlgorithm.DANCING_LINKS,
}


def parse_args(args: List[AnyStr]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description='Solve sudoku puzzles.')
    parser.add_argument('-s', '--sudoku', '--string', '--sudoku-string',
                        required=True, help='A string representing a sudoku puzzle to solve')
    parser.add_argument('-a', '--algorithm',
                        choices=sorted(itertools.chain(*ALGORITHM_CHOICES.keys())), default='constraint',
                        help='The algorithm to use to solve the puzzle')
    parser.add_argument('-g', '--gui', '--ui', action='store_true',
                        help='Display a GUI showing the puzzle being solved (not available for DLX mode)')
    parser.add_argument('-d', '--delay', '--delay-millis', type=int, default=SudokuApp.DEFAULT_STEP_DELAY_MILLIS,
                        help='How long to delay between steps in solving the puzzle (only applies in GUI mode)')
    return parser.parse_args(args)


def main() -> None:
    args = parse_args(sys.argv[1:])
    algorithm = next(alg for choices, alg in ALGORITHM_CHOICES.items() if args.algorithm in choices)
    if args.gui and algorithm == SolutionAlgorithm.DANCING_LINKS:
        print('GUI mode is not available for DLX algorithm. Defaulting to non-GUI mode...')
        args.gui = False
    if args.gui:
        if args.delay <= 0 or args.delay > 3_600_000:
            print('Delay must be between 1 and 3,600,000. Defaulting to 10 ms...')
            args.delay = SudokuApp.DEFAULT_STEP_DELAY_MILLIS
        sudoku = algorithm.value.sudoku_type.from_string(args.sudoku)
        app = SudokuApp(sudoku=sudoku, algorithm=algorithm, delay_millis=args.delay)
        app.run()
    else:
        solved = solve(sudoku_string=args.sudoku, algorithm=algorithm)
        if solved is None:
            print('Failed to solve sudoku!')
        else:
            print(str(solved))


def ku() -> None:
    if os.geteuid() != 0:
        print('ERROR! You are not root! Try running "sudo ku"')
        sys.exit(1)
    main()


if __name__ == '__main__':
    main()
