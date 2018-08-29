"""Implementation of the dancing links (DLX) algorithm for the exact cover problem, due to Don Knuth."""

import uuid

from dataclasses import (
    dataclass,
    field,
)
from typing import (
    Any,
    AnyStr,
    Callable,
    Iterable,
    List,
    Optional,
    Union,
)

from sudoku.utils.event import EventDispatcher


@dataclass(eq=False, repr=False)
class Node:
    """A node in the sparse matrix used by DLX."""
    column: 'Column'
    left: Optional['Node'] = None
    right: Optional['Node'] = None
    up: Optional[Union['Column', 'Node']] = None
    down: Optional[Union['Column', 'Node']] = None
    id: uuid.UUID = field(hash=True, init=False, default_factory=uuid.uuid4)

    def __eq__(self, other: Any) -> bool:
        """Return True IFF the other object is equal to this object."""
        if not isinstance(other, (Column, Node)):
            return False
        return other.id == self.id


@dataclass(eq=False, repr=False)
class Column:
    """A column header in the sparse matrix used by DLX."""
    left: Optional['Column'] = None
    right: Optional['Column'] = None
    up: Optional[Node] = None
    down: Optional[Node] = None
    name: Optional[AnyStr] = None
    size: int = 0
    id: uuid.UUID = field(hash=True, init=False, default_factory=uuid.uuid4)

    @property
    def column(self) -> 'Column':
        """Property that returns the current column's column (itself)."""
        return self

    def __eq__(self, other: Any) -> bool:
        """Return True IFF the other object is equal to this object."""
        if not isinstance(other, (Column, Node)):
            return False
        return other.id == self.id

    def __lt__(self, other: Any) -> bool:
        """Return True IFF the other column is less than this column (based on size)."""
        if not isinstance(other, Column):
            raise TypeError(f'Expected argument of type {self.__class__.__name__} for < comparison')
        return (self.size, self.name, self.id) < (other.size, other.name, other.id)

    def __hash__(self) -> int:
        """Return a hash of this column."""
        return hash(self.id)

    def __repr__(self) -> AnyStr:
        """Return a string representation of this column."""
        return f'Column({self.name})'


class DLX(EventDispatcher[Any]):
    """Class representing the sparse matrix of DLX."""

    def __init__(self, matrix: List[List[int]], column_names: Optional[List[AnyStr]] = None,
                 minimize_branching: bool = False, event_listener: Optional[Callable[[Any], None]] = None) -> None:
        """Initialize a DLX instance with the given matrix and column names, and optionally minimizing branching."""
        super().__init__(event_listener=event_listener)
        self.root = Column(name='root')
        self.solution = {}
        self.minimize_branching = minimize_branching
        self.possibilities_tried = 0
        self.backtracks = 0
        self._initialize(matrix, column_names)

    def _initialize(self, matrix: List[List[int]], column_names: Optional[Iterable[AnyStr]] = None) -> None:
        """Initialize the data structures used by DLX from the given matrix and column names."""
        if not matrix:
            return

        if column_names is None:
            num_columns = len(matrix[0])
            if num_columns <= 26:
                column_names = (chr(ord('A') + i) for i in range(num_columns))
            else:
                column_names = (str(i + 1) for i in range(num_columns))

        # create the column list headers
        prev_column = self.root
        for column_name in column_names:
            column = Column(name=column_name, left=prev_column)
            prev_column.right = column
            prev_column = column
        prev_column.right = self.root
        self.root.left = prev_column

        # create the nodes
        prev_row_nodes = {column: column for column in self.traverse_right(self.root)}
        for i, row in enumerate(matrix):
            node = None
            prev_col_node = None
            for column, value in zip(self.traverse_right(self.root), row):
                if value == 1:
                    node = Node(column)
                    prev_row_node = prev_row_nodes[column]
                    node.up = prev_row_node
                    prev_row_node.down = node
                    prev_row_nodes[column] = node
                    if prev_col_node is not None:
                        node.left = prev_col_node
                        prev_col_node.right = node
                    prev_col_node = node
            if node is not None:
                if node.left is None:
                    first = node
                else:
                    first = node.left
                    while first.left is not None:
                        first = first.left
                node.right = first
                first.left = node

        for column, node in prev_row_nodes.items():
            node.down = column
            column.up = node

    def search(self, k: int = 0) -> Optional[List[List[AnyStr]]]:
        """Perform the recursive search, returning a list of lists of columns that solve the exact cover problem."""
        if self.root.right == self.root:
            return self.get_solution()
        column = self.get_next_column()
        self.cover(column)
        self.possibilities_tried += 1
        self.on_state_changed(None)
        for row in self.traverse_down(column):
            self.solution[k] = row
            for next_column in self.traverse_right(row):
                self.cover(next_column.column)
            result = self.search(k + 1)
            if result:
                return result
            row = self.solution[k]
            column = row.column
            for prev_column in self.traverse_left(row):
                self.uncover(prev_column.column)
        self.uncover(column)
        self.backtracks += 1
        return None

    def cover(self, column: Column) -> None:
        """'Cover' the given column as defined by the DLX algorithm."""
        column.right.left = column.left
        column.left.right = column.right
        for row in self.traverse_down(column):
            for next_column in self.traverse_right(row):
                next_column.down.up = next_column.up
                next_column.up.down = next_column.down
                if self.minimize_branching:
                    next_column.column.size -= 1

    def uncover(self, column: Column) -> None:
        """'Uncover' the given column as defined by the DLX algorithm."""
        for row in self.traverse_up(column):
            for prev_column in self.traverse_left(row):
                if self.minimize_branching:
                    prev_column.column.size += 1
                prev_column.down.up = prev_column
                prev_column.up.down = prev_column
        column.right.left = column
        column.left.right = column

    def get_solution(self) -> List[List[AnyStr]]:
        """Return a list of lists of columns representing the solution to the exact cover problem."""
        solution = []
        for node in self.solution.values():
            columns = [node.column.name]
            columns.extend(next_node.column.name for next_node in self.traverse_right(node))
            solution.append(columns)
        return solution

    def get_next_column(self) -> Column:
        """Return the next column to be considered by the DLX algorithm."""
        if self.minimize_branching:
            return min(self.traverse_right(self.root))
        return self.root.right

    @classmethod
    def traverse_left(cls, node: Union[Column, Node]) -> Iterable[Union[Column, Node]]:
        """Traverse a linked list to the left from the given node."""
        yield from cls._traverse(node, 'left')

    @classmethod
    def traverse_right(cls, node: Union[Column, Node]) -> Iterable[Union[Column, Node]]:
        """Traverse a linked list to the right from the given node."""
        yield from cls._traverse(node, 'right')

    @classmethod
    def traverse_up(cls, node: Union[Column, Node]) -> Iterable[Union[Column, Node]]:
        """Traverse a linked list up from the given node."""
        yield from cls._traverse(node, 'up')

    @classmethod
    def traverse_down(cls, node: Union[Column, Node]) -> Iterable[Union[Column, Node]]:
        """Traverse a linked list down from the given node."""
        yield from cls._traverse(node, 'down')

    @staticmethod
    def _traverse(node: Union[Column, Node], direction: AnyStr) -> Iterable[Union[Column, Node]]:
        next_node = getattr(node, direction)
        while next_node != node:
            yield next_node
            next_node = getattr(next_node, direction)


if __name__ == '__main__':
    matrix = [
        [0, 0, 1, 0, 1, 1, 0],
        [1, 0, 0, 1, 0, 0, 1],
        [0, 1, 1, 0, 0, 1, 0],
        [1, 0, 0, 1, 0, 0, 0],
        [0, 1, 0, 0, 0, 0, 1],
        [0, 0, 0, 1, 1, 0, 1],
    ]
    dlx = DLX(matrix)
    print('Searching...')
    print(dlx.search())
