from collections.abc import Generator, Sequence
from dataclasses import dataclass
from typing import TypeVar


@dataclass(frozen=True)
class Point:
    """(x, y) coord pair of grid."""

    x: int | float
    y: int | float


def point_iter(grid_size: int) -> Generator[Point, None, None]:
    """Return Point for each grid cell.

    Expects square grid dimension."""
    for y in range(grid_size):
        for x in range(grid_size):
            yield Point(x, y)


T = TypeVar('T')


def grid_iter(grid: Sequence[Sequence[T]]) -> Generator[T, None, None]:
    """Return iterator over elems of 2-D array."""
    for row in grid:
        for item in row:
            yield item
