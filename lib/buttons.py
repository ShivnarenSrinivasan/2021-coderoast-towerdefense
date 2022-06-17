from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Protocol

from . import grid


class BaseButton(Protocol):
    """Contains coords."""

    coord1: grid.Point
    coord2: grid.Point


@dataclass  # type: ignore
class Button(ABC):
    """Generic Button."""

    coord1: grid.Point
    coord2: grid.Point

    def can_press(self, point: grid.Point) -> bool:
        return is_within_bounds(self, point)

    @abstractmethod
    def press(self) -> None:
        """Implement press functionality."""

    def paint(self, canvas):
        canvas.create_rectangle(*self.coord1, *self.coord2, fill="red", outline="black")


def is_within_bounds(btn: BaseButton, point: grid.Point) -> bool:
    return (
        btn.coord1.x <= point.x <= btn.coord2.x
        and btn.coord1.y <= point.y <= btn.coord2.y
    )


def make_coords(x1: int, y1: int, x2: int, y2: int) -> tuple[grid.Point, grid.Point]:
    return grid.Point(x1, y1), grid.Point(x2, y2)
