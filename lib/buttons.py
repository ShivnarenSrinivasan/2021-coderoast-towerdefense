import tkinter as tk
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Protocol

from . import (
    grid,
    tower,
)


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
    def press(self, tower_map: tower.ITowerMap) -> None:
        """Implement press functionality."""

    def paint(self, canvas: tk.Canvas) -> None:
        canvas.create_rectangle(*self.coord1, *self.coord2, fill="red", outline="black")


class NextWaveButton:
    def __init__(self):
        self.coord1 = grid.Point(450, 25)
        self.coord2 = grid.Point(550, 50)

    def paint(self, canvas: tk.Canvas, color: str) -> None:
        canvas.create_rectangle(
            *self.coord1, *self.coord2, fill=color, outline=color
        )  # draws a rectangle where the pointer is
        canvas.create_text(500, 37, text="Next Wave")


def is_within_bounds(btn: BaseButton, point: grid.Point) -> bool:
    return (
        btn.coord1.x <= point.x <= btn.coord2.x
        and btn.coord1.y <= point.y <= btn.coord2.y
    )


def make_coords(x1: int, y1: int, x2: int, y2: int) -> tuple[grid.Point, grid.Point]:
    return grid.Point(x1, y1), grid.Point(x2, y2)
