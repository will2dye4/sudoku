import argparse
import os
import sys
import time

from typing import (
    AnyStr,
    List,
)

from sudoku import (
    SolutionAlgorithm,
    get_solver,
)
from sudoku.ui import SudokuApp


ALGORITHM_CHOICES = {
    'brute-force': SolutionAlgorithm.BRUTE_FORCE,
    'constraint': SolutionAlgorithm.CONSTRAINT_BASED,
    'dlx': SolutionAlgorithm.DANCING_LINKS,
}


class WiderHelpFormatter(argparse.HelpFormatter):

    def __init__(self, prog):
        super().__init__(prog, width=120)


def parse_args(args: List[AnyStr]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description='Solve sudoku puzzles.', formatter_class=WiderHelpFormatter)
    parser.add_argument('-s', '--sudoku', '--string', '--sudoku-string',
                        required=True, help='A string representing a sudoku puzzle to solve')
    parser.add_argument('-a', '--algorithm',
                        choices=sorted(ALGORITHM_CHOICES.keys()), default='constraint',
                        help='The algorithm to use to solve the puzzle')
    parser.add_argument('-g', '--gui', '--ui', action='store_true',
                        help='Display a GUI showing the puzzle being solved (not available for DLX mode)')
    parser.add_argument('-d', '--delay', '--delay-millis', type=int, default=SudokuApp.DEFAULT_STEP_DELAY_MILLIS,
                        help='How long to delay between steps in solving the puzzle (only applies in GUI mode)')
    parser.add_argument('-q', '--quiet', action='count', default=0,
                        help='Reduce output verbosity (may be used multiple times)')
    return parser.parse_args(args)


def main() -> None:
    args = parse_args(sys.argv[1:])
    algorithm = ALGORITHM_CHOICES[args.algorithm]

    if args.gui and algorithm == SolutionAlgorithm.DANCING_LINKS:
        print('GUI mode is not available for DLX algorithm. Defaulting to non-GUI mode...')
        args.gui = False

    sudoku = algorithm.value.sudoku_type.from_string(args.sudoku)
    if args.gui:
        if args.delay <= 0 or args.delay > 3_600_000:
            print(f'Delay must be between 1 and 3,600,000. Defaulting to {SudokuApp.DEFAULT_STEP_DELAY_MILLIS} ms...')
            args.delay = SudokuApp.DEFAULT_STEP_DELAY_MILLIS
        app = SudokuApp(sudoku=sudoku, algorithm=algorithm, delay_millis=args.delay)
        app.run()
    else:
        if args.quiet < 1:
            print(str(sudoku))
        if args.quiet < 2:
            print('Solving...')
        solver = get_solver(sudoku=sudoku, algorithm=algorithm)
        start_time = time.time()
        solved = solver.solve()
        end_time = time.time()
        if solved is None:
            if args.quiet < 2:
                print('Failed to solve sudoku!')
            sys.exit(1)
        else:
            total_time = end_time - start_time
            if args.quiet < 2:
                print(f'Done! Evaluated {solver.possibilities_tried} possibilities in {total_time:0.2f} seconds.\n')
            if args.quiet < 1:
                print(str(solved))
            print(solved.get_condensed_string())


def ku() -> None:
    if os.geteuid() != 0:
        print('ERROR! You are not root! Try running "sudo ku"')
        sys.exit(1)
    main()


if __name__ == '__main__':
    main()
