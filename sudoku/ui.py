import threading
import time
import tkinter as tk

from typing import Optional

from sudoku import (
    DictSudoku,
    MatrixSudoku,
    Row,
    SolutionAlgorithm,
    Sudoku,
    ds,
    get_solver,
    ms,
)


class SudokuApp(tk.Frame):

    DEFAULT_STEP_DELAY_MILLIS = 10
    DEFAULT_TICK_DELAY_MILLIS = 100

    def __init__(self, master: Optional[tk.Tk] = None, sudoku: Optional[Sudoku] = None,
                 algorithm: Optional[SolutionAlgorithm] = None, delay_millis: int = DEFAULT_STEP_DELAY_MILLIS):
        if master is None:
            master = tk.Tk()
            master.title('Sudoku Solver')

        super().__init__(master)

        if sudoku is not None:
            if algorithm is None:
                for alg in SolutionAlgorithm:
                    if isinstance(sudoku, alg.value.sudoku_type):
                        algorithm = alg
                        break
            if algorithm not in {SolutionAlgorithm.BRUTE_FORCE, SolutionAlgorithm.CONSTRAINT_BASED}:
                raise ValueError('Algorithm must be either BRUTE_FORCE or CONSTRAINT_BASED for Sudoku UI')

        self.algorithm = algorithm
        self.sudoku = sudoku
        self.delay_millis = delay_millis
        self.solver = None
        self.solve_thread = None
        self.cells = []
        self.pack()
        self.create_grid()
        self.stats = self.create_stats_display()
        self.start_time = None
        self.end_time = None

    def create_grid(self) -> None:
        self.create_horizontal_line()
        for row_enum in Row:
            cells = []
            row = tk.Frame()
            self.create_vertical_line(row)
            for column in range(1, 10):
                if self.sudoku is not None:
                    value = str(self.sudoku.get_cell_value(row_enum, column) or '')
                else:
                    value = ''
                var = tk.StringVar(value=value)
                cell = tk.Label(
                    row,
                    height=3,
                    width=4,
                    justify=tk.CENTER,
                    padx=6,
                    borderwidth=1,
                    relief=tk.RAISED,
                    textvariable=var,
                    font=('Arial', 18),
                    fg='blue' if value else 'black'
                )
                cell.pack(side='left')
                cells.append(var)
                if column in {3, 6}:
                    self.create_vertical_line(row)
            row.pack(side='top')
            self.cells.append(cells)
            if row_enum.value in {3, 6}:
                self.create_horizontal_line()
            self.create_vertical_line(row)
        self.create_horizontal_line()

    @staticmethod
    def create_horizontal_line() -> None:
        horizontal_line = tk.Label(width=544, height=1, bg='black', font=('Arial', 1))
        horizontal_line.pack(side='top')

    @staticmethod
    def create_vertical_line(row: tk.Frame) -> None:
        vertical_line = tk.Label(row, width=1, height=31, bg='black', font=('Arial', 2))
        vertical_line.pack(side='left')

    @staticmethod
    def create_stats_display() -> tk.Label:
        stats = tk.Label(pady=5)
        stats.pack(side='top')
        return stats

    def update_grid(self, sudoku: Sudoku) -> None:
        try:
            for row in Row:
                for column in range(1, 10):
                    value = str(sudoku.get_cell_value(row, column) or '')
                    cell = self.cells[row.value - 1][column - 1]
                    if cell.get() != value:
                        cell.set(value)
            time.sleep(self.delay_millis / 1000)
        except:
            pass

    @property
    def elapsed_time(self) -> float:
        if self.start_time is not None:
            end_time = self.end_time or time.time()
            return end_time - self.start_time
        return 0

    def tick(self) -> None:
        if self.solve_thread is not None and not self.solve_thread.is_alive():
            self.end_time = time.time()
            self.solve_thread = None
        self.stats['text'] = (f'Possibilities Tried: {self.solver.possibilities_tried}          '
                              f'Backtracks: {self.solver.backtracks}          '
                              f'Elapsed Time: {self.elapsed_time:0.2f} sec')
        self.update()
        self.after(self.DEFAULT_TICK_DELAY_MILLIS, self.tick)

    def run(self) -> None:
        if self.sudoku is not None:
            self.solver = get_solver(self.sudoku, self.algorithm)
            self.solver.event_listener = self.update_grid
            self.solve_thread = threading.Thread(target=self.solver.solve, daemon=True)
            self.solve_thread.start()
            self.start_time = time.time()
            self.tick()

        super().mainloop()

        if self.solve_thread is not None:
            self.solve_thread.join(timeout=1)


if __name__ == '__main__':
    s = """
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
    """
    ms2 = MatrixSudoku.from_string(s)  # TODO - does this produce an invalid solution??
    ds2 = DictSudoku.from_string(s)
    app = SudokuApp(sudoku=ds, delay_millis=1000)
    app.run()
