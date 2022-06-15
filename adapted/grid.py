from collections.abc import Generator
from dataclasses import dataclass


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
