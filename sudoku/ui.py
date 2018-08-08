import threading
import time
import tkinter as tk

from sudoku import Sudoku, ds, ms
from sudoku.model import Row
from sudoku.solver import get_solver


class SudokuApp(tk.Frame):

    DEFAULT_TICK_DELAY_MILLIS = 100

    def __init__(self, master: tk.Tk = None, sudoku: Sudoku = None, delay_millis: int = 0):
        super().__init__(master)
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

    def tick(self) -> None:
        if self.solve_thread is not None:
            if self.solve_thread.is_alive():
                # still running
                elapsed = time.time() - self.start_time
            else:
                # finished
                self.end_time = time.time()
                elapsed = self.end_time - self.start_time
                self.solve_thread = None
        elif self.start_time is not None and self.end_time is not None:
            elapsed = self.end_time - self.start_time
        else:
            elapsed = 0
        self.stats['text'] = (f'Possibilities Tried: {self.solver.possibilities_tried}          '
                              f'Backtracks: {self.solver.backtracks}          '
                              f'Elapsed Time: {elapsed:0.2f} sec')
        self.update()
        self.after(self.DEFAULT_TICK_DELAY_MILLIS, self.tick)

    def mainloop(self, n: int = 0) -> None:
        if self.sudoku is not None:
            self.solver = get_solver(self.sudoku)
            self.solver.event_listener = self.update_grid
            self.solve_thread = threading.Thread(target=self.solver.solve, args=(self.sudoku,), daemon=True)
            self.solve_thread.start()
            self.start_time = time.time()
            self.tick()

        super().mainloop(n)

        if self.solve_thread is not None:
            self.solve_thread.join(timeout=1)


if __name__ == '__main__':
    root = tk.Tk()
    root.title('Sudoku Solver')
    app = SudokuApp(master=root, sudoku=ds, delay_millis=1000)
    app.mainloop()
