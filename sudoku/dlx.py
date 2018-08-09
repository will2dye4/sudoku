import uuid

from dataclasses import (
    dataclass,
    field,
)
from typing import (
    AnyStr,
    Iterable,
    List,
    Optional,
    Union,
)


@dataclass(eq=False, repr=False)
class Node:
    """A node in the sparse matrix used by DLX."""
    column: 'Column'
    left: Optional['Node'] = None
    right: Optional['Node'] = None
    up: Optional[Union['Column', 'Node']] = None
    down: Optional[Union['Column', 'Node']] = None
    id: uuid.UUID = field(hash=True, init=False, default_factory=uuid.uuid4)

    def __eq__(self, other):
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
        return self

    def __eq__(self, other):
        if not isinstance(other, (Column, Node)):
            return False
        return other.id == self.id

    def __repr__(self) -> AnyStr:
        return f'Column({self.name})'


class DLX:
    """Class representing the sparse matrix of DLX."""

    def __init__(self, matrix: List[List[int]]):
        self.root = Column(name='root')
        self.solution = {}
        self._initialize(matrix)

    def _initialize(self, matrix: List[List[int]]) -> None:
        if not matrix:
            return

        # create the column list headers
        prev_column = self.root
        for i in range(len(matrix[0])):
            column_name = chr(ord('A') + i)     # TODO this won't work if the matrix is large
            column = Column(name=column_name, left=prev_column)
            prev_column.right = column
            prev_column = column
        prev_column.right = self.root
        self.root.left = prev_column

        # create the nodes
        pass

    def search(self, k: int = 0) -> None:
        if self.root.right == self.root:
            return  # DONE! print solution or return it here
        column = self.root.right    # NOTE: could optimize using column sizes
        self.cover(column)
        for row in self.traverse_down(column):
            self.solution[k] = row
            for next_column in self.traverse_right(row):
                self.cover(next_column)
            self.search(k + 1)
            row = self.solution[k]
            column = row.column
            for prev_column in self.traverse_left(row):
                self.uncover(prev_column)
        self.uncover(column)

    def cover(self, column: Column) -> None:
        column.right.left = column.left
        column.left.right = column.right
        for row in self.traverse_down(column):
            for next_column in self.traverse_right(row):
                next_column.down.up = next_column.up
                next_column.up.down = next_column.down
                if next_column.column.size:
                    next_column.column.size -= 1

    def uncover(self, column: Column) -> None:
        for row in self.traverse_up(column):
            for prev_column in self.traverse_left(row):
                if prev_column.column.size:
                    prev_column.column.size += 1
                prev_column.down.up = prev_column
                prev_column.up.down = prev_column
        column.right.left = column
        column.left.right = column

    @classmethod
    def traverse_left(cls, node: Union[Column, Node]) -> Iterable[Union[Column, Node]]:
        yield from cls._traverse(node, 'left')

    @classmethod
    def traverse_right(cls, node: Union[Column, Node]) -> Iterable[Union[Column, Node]]:
        yield from cls._traverse(node, 'right')

    @classmethod
    def traverse_up(cls, node: Union[Column, Node]) -> Iterable[Union[Column, Node]]:
        yield from cls._traverse(node, 'up')

    @classmethod
    def traverse_down(cls, node: Union[Column, Node]) -> Iterable[Union[Column, Node]]:
        yield from cls._traverse(node, 'down')

    @staticmethod
    def _traverse(node: Union[Column, Node], direction: AnyStr) -> Iterable[Union[Column, Node]]:
        next_node = getattr(node, direction)
        while next_node != node:
            yield next_node
            next_node = getattr(next_node, direction)
