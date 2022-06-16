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

    def checkPress(self, point: grid.Point) -> bool:
        if is_within_bounds(self, point):
            self.press()
            return True
        return False

    @abstractmethod
    def press(self) -> None:
        """Implement press functionality."""

    def paint(self, canvas):
        canvas.create_rectangle(
            self.x, self.y, self.xTwo, self.yTwo, fill="red", outline="black"
        )


def is_within_bounds(btn: BaseButton, point: grid.Point) -> bool:
    return btn.x <= point.x <= btn.xTwo and btn.y <= point.y <= btn.yTwo
