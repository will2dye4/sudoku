import argparse
import functools
import os
import sys
import time

from enum import Enum
from typing import (
    AnyStr,
    List,
)

from sudoku import (
    InvalidPuzzleError,
    Row,
    SolutionAlgorithm,
    Sudoku,
    SudokuSolver,
    get_puzzle_by_name,
    get_solver,
)
from sudoku.ui import SudokuApp


class Color(Enum):
    BOLD = '1'
    GREEN = '0;32'
    RED = '0;31'
    YELLOW = '0;33'


class WiderHelpFormatter(argparse.HelpFormatter):

    def __init__(self, prog: AnyStr):
        super().__init__(prog, width=120)


class SudokuMain:

    ALGORITHM_CHOICES = {
        'brute-force': SolutionAlgorithm.BRUTE_FORCE,
        'constraint': SolutionAlgorithm.CONSTRAINT_BASED,
        'dlx': SolutionAlgorithm.DANCING_LINKS,
    }

    DEFAULT_DELAY_MILLIS = SudokuApp.DEFAULT_STEP_DELAY_MILLIS

    def __init__(self, args: List[AnyStr] = None):
        if args is None:
            args = sys.argv[1:]
        parsed_args = self.parse_args(args)
        self.sudoku = parsed_args.sudoku
        self.name = parsed_args.name
        self.algorithm = self.ALGORITHM_CHOICES[parsed_args.algorithm]
        self.gui = parsed_args.gui
        self.delay = parsed_args.delay
        self.quietude = parsed_args.quiet

    @classmethod
    def parse_args(cls, args: List[AnyStr]) -> argparse.Namespace:
        parser = argparse.ArgumentParser(description='Solve sudoku puzzles.', formatter_class=WiderHelpFormatter)
        parser.add_argument('-s', '--sudoku', '--string', '--sudoku-string',
                            help='A string representing a sudoku puzzle to solve')
        parser.add_argument('-n', '--name',
                            help='The name of a sample puzzle to solve (for demo purposes)')
        parser.add_argument('-a', '--algorithm',
                            choices=sorted(cls.ALGORITHM_CHOICES.keys()), default='constraint',
                            help='The algorithm to use to solve the puzzle')
        parser.add_argument('-g', '--gui', '--ui', action='store_true',
                            help='Display a GUI showing the puzzle being solved (not available for DLX mode)')
        parser.add_argument('-d', '--delay', '--delay-millis', type=int, default=cls.DEFAULT_DELAY_MILLIS,
                            help='How long to delay between steps in solving the puzzle (only applies in GUI mode)')
        parser.add_argument('-q', '--quiet', action='count', default=0,
                            help='Reduce output verbosity (may be used multiple times)')
        return parser.parse_args(args)

    @classmethod
    def bold(cls, text: AnyStr) -> AnyStr:
        return cls.colorize(text, Color.BOLD)

    @classmethod
    def green(cls, text: AnyStr) -> AnyStr:
        return cls.colorize(text, Color.GREEN)

    @classmethod
    def red(cls, text: AnyStr) -> AnyStr:
        return cls.colorize(text, Color.RED)

    @classmethod
    def yellow(cls, text: AnyStr) -> AnyStr:
        return cls.colorize(text, Color.YELLOW)

    @staticmethod
    def colorize(text: AnyStr, color: Color) -> AnyStr:
        return f'\033[{color.value}m{text}\033[0m'

    def print(self, level: int, message: AnyStr, **kwargs) -> None:
        if self.quietude < level:
            print(message, **kwargs)

    def trace(self, message: AnyStr, **kwargs) -> None:
        self.print(1, message, **kwargs)

    def debug(self, message: AnyStr, **kwargs) -> None:
        self.print(2, message, **kwargs)

    def info(self, message: AnyStr, **kwargs) -> None:
        self.print(3, message, **kwargs)

    def warn(self, message: AnyStr, **kwargs) -> None:
        self.print(4, message, **kwargs)

    def die(self, message: AnyStr, level: int = 4, exit_code: int = 1, red: bool = True) -> None:
        if red:
            message = self.red(message)
        self.print(level, message, file=sys.stderr)
        sys.exit(exit_code)

    def get_sudoku(self) -> Sudoku:
        if not self.sudoku and not self.name:
            self.die('You must provide either a sudoku string (-s) or the name of a sample puzzle (-n) to solve!')

        if self.sudoku and self.name:
            self.die('You must provide either a sudoku string (-s) or a sample puzzle name (-n), but not both!')

        if self.name:
            try:
                self.sudoku = get_puzzle_by_name(self.name)
            except InvalidPuzzleError as error:
                self.die(str(error))

        return self.algorithm.value.sudoku_type.from_string(self.sudoku)

    def run_gui(self, sudoku: Sudoku) -> None:
        if self.algorithm == SolutionAlgorithm.DANCING_LINKS:
            self.warn(self.yellow('GUI mode is not available for DLX algorithm. Defaulting to non-GUI mode...'),
                      file=sys.stderr)
            self.gui = False
            self.name = None
            self.run()
            return
        if self.delay <= 0 or self.delay > 3_600_000:
            self.warn(self.yellow(f'Delay must be between 1 and 3,600,000. '
                                  f'Defaulting to {self.DEFAULT_DELAY_MILLIS} ms...'),
                      file=sys.stderr)
            self.delay = self.DEFAULT_DELAY_MILLIS
        app = SudokuApp(sudoku=sudoku, algorithm=self.algorithm, delay_millis=self.delay)
        app.run()

    def cli_event_listener(self, solver: SudokuSolver, _: Sudoku) -> None:
        _, remainder = divmod(solver.possibilities_tried, 1000)
        if remainder == 0:
            self.info('.', end='', flush=True)

    def run_cli(self, sudoku: Sudoku) -> None:
        self.trace('Starting puzzle:')
        self.trace(str(sudoku))

        num_empty_cells = sum(1 for row in Row for column in range(1, 10)
                              if sudoku.get_cell_value(row, column) is None)
        algorithm_name = self.algorithm.name.lower().replace('_', ' ')
        self.info(f'Solving for {self.bold(num_empty_cells)} unknown cells '
                  f'using the {self.bold(algorithm_name)} algorithm...', end='', flush=True)

        solver = get_solver(sudoku=sudoku, algorithm=self.algorithm)
        solver.event_listener = functools.partial(self.cli_event_listener, solver)
        start_time = time.time()
        solved = solver.solve()
        end_time = time.time()
        self.info('')   # force a newline after the dots

        if solved is None:
            self.die('Failed to solve sudoku!', level=3, exit_code=2)
        else:
            possibilities_tried = f'{solver.possibilities_tried:,}'
            total_time = f'{(end_time - start_time):0.2f}'
            self.info(f'{self.green("Done!")} Evaluated {self.bold(possibilities_tried)} possibilities '
                      f'in {self.bold(total_time)} seconds.\n')
            self.debug(str(solved))
            self.warn(solved.get_condensed_string())

    def run(self) -> None:
        sudoku = self.get_sudoku()
        if self.gui:
            self.run_gui(sudoku)
        else:
            try:
                self.run_cli(sudoku)
            except KeyboardInterrupt:
                self.die('\nGoodbye!', red=False)


def main() -> None:
    SudokuMain().run()


def ku() -> None:
    if os.geteuid() != 0:
        print('ERROR! You are not root! Try running "sudo ku"')
        sys.exit(1)
    main()


if __name__ == '__main__':
    main()
