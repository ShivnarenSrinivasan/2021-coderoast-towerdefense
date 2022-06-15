from collections.abc import Generator, Sequence
from typing import TypeVar

T = TypeVar('T')


def grid_iter(grid: Sequence[Sequence[T]]) -> Generator[T, None, None]:
    """Return iterator over elems of 2-D array."""
    for row in grid:
        for item in row:
            yield item
