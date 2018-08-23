# sudoku - Python sudoku solver

This package contains utilities for solving [sudoku](https://en.wikipedia.org/wiki/Sudoku) puzzles
using a variety of different algorithms.

## Installation

The package is not currently available on PyPI or any other Python package repository. The easiest
way to install it is to clone the GitHub repository and install it from source.

### Prerequisites

* [Python 3.7](https://www.python.org/downloads/release/python-370/)
* [Git](https://git-scm.com)
* [Make](https://www.gnu.org/software/make/)
* [virtualenvwrapper](https://virtualenvwrapper.readthedocs.io/en/latest/)

### Installation Instructions

Run the following commands in a shell (a UNIX-like environment is assumed):

```
$ git clone git@github.com:will2dye4/sudoku.git
$ cd sudoku
$ mkvirtualenv -p`which python3.7` sudoku
(sudoku) $ make install
```

It is not strictly necessary to create a virtual environment for the sudoku package. However, the
package makes use of Python 3.7 features, so if you choose not to use a virtual environment, you
assume responsibility for installing the package in an appropriate Python 3.7 environment.

When successfully installed, a program called `sudoku` will be placed on your `PATH`. See the Usage
section below for details about how to use this program.

## Usage

At any time, you can use the `-h` or `--help` flags to see a summary of options that the program accepts.

```
$ sudoku -h
usage: sudoku [-h] [-s SUDOKU] [-n NAME] [-a {brute-force,constraint,dlx}] [-g] [-d DELAY] [-q]

Solve sudoku puzzles.

optional arguments:
  -h, --help            show this help message and exit
  -s SUDOKU, --sudoku SUDOKU, --string SUDOKU, --sudoku-string SUDOKU
                        A string representing a sudoku puzzle to solve
  -n NAME, --name NAME  The name of a sample puzzle to solve (for demo purposes)
  -a {brute-force,constraint,dlx}, --algorithm {brute-force,constraint,dlx}
                        The algorithm to use to solve the puzzle
  -g, --gui, --ui       Display a GUI showing the puzzle being solved (not available for DLX mode)
  -d DELAY, --delay DELAY, --delay-millis DELAY
                        How long to delay between steps in solving the puzzle (only applies in GUI mode)
  -q, --quiet           Reduce output verbosity (may be used multiple times)
```

The most basic usage is `sudoku -s <string>`, where `<string>` is a string representing a sudoku
puzzle to solve. The string should contain the value for each cell in the puzzle as a digit, or
a `0` or `.` for cells that are empty. Any other characters in the string will be ignored. For
example, the following three strings all represent the same puzzle to the program:

```
4.....8.5.3..........7......2.....6.....8.4......1.......6.3.7.5..2.....1.4......
```

```
400000805
030000000
000700000
020000060
000080400
000010000
000603070
500200000
104000000
```

```
4 . . |. . . |8 . 5 
. 3 . |. . . |. . . 
. . . |7 . . |. . . 
------+------+------
. 2 . |. . . |. 6 . 
. . . |. 8 . |4 . . 
. . . |. 1 . |. . . 
------+------+------
. . . |6 . 3 |. 7 . 
5 . . |2 . . |. . . 
1 . 4 |. . . |. . . 
```

### Algorithms

By default, `sudoku` will use its fastest algorithm to solve the puzzle. This is a 
**constraint-based** algorithm which uses the rules of sudoku to quickly deduce the solution
to any input puzzle (assuming the puzzle has enough clues to be solved). The constraint-based
algorithm typically solves a sudoku in less than 0.1 seconds (tested on a mid-2015 MacBook Pro).
The implementation of the constraint-based solution algorithm is based heavily on the [prior work 
of Peter Norvig](http://norvig.com/sudoku.html).

To specify a different algorithm, use the `-a` or `--algorithm` flags to `sudoku`. The other
available algorithms are `brute-force` and `dlx`. A description of each of these algorithms follows.

The **brute-force** algorithm tries all possible values for all empty cells in the puzzle, and 
therefore its running time is exponential in the number of empty cells, i.e., *O(9^n)* where
*n* is the number of empty cells. As such, **this algorithm is NOT practical** for solving most 
sudoku puzzles. In other words, in the worst case, this algorithm will take longer than the lifetime
of the universe to solve a typical sudoku puzzle. Usage of the brute-force algorithm should be limited 
to input puzzles that are already mostly solved.

The **DLX** algorithm uses the ["dancing links" algorithm](https://arxiv.org/pdf/cs/0011047.pdf) (due to 
Don Knuth) to solve a sudoku puzzle  by mapping it onto an equivalent [exact cover](https://en.wikipedia.org/wiki/Exact_cover)
problem and using a Python implementation of dancing links to solve the exact cover problem. This 
algorithm is much faster than the brute-force algorithm but much slower than the constraint-based 
algorithm, and its running time is on the order of 10 hours for a typical input puzzle.

### Sample Puzzles

TODO

### Output

TODO

### GUI Mode

TODO
