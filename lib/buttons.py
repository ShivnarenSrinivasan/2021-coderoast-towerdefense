from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Protocol

import grid


class BaseButton(Protocol):
    """Contains coords."""
    x: int
    y: int
    xTwo: int
    yTwo: int


@dataclass  # type: ignore
class Button(ABC):
    """Generic Button."""
    x: int
    y: int
    xTwo: int
    yTwo: int

    def can_press(self, point: grid.Point) -> bool:
        return is_within_bounds(self, point)

    @abstractmethod
    def press(self) -> None:
        """Implement press functionality."""

    def paint(self, canvas):
        canvas.create_rectangle(
            self.x, self.y, self.xTwo, self.yTwo, fill="red", outline="black"
        )


def is_within_bounds(btn: BaseButton, point: grid.Point) -> bool:
    return btn.x <= point.x <= btn.xTwo and btn.y <= point.y <= btn.yTwo
