import tkinter as tk
from typing import Protocol

from .grid import Loc


class Movable(Protocol):
    distanceTravelled: float
    speed: float
    movement: float

    def move(self) -> None:
        ...

    def positionFormula(self) -> Loc:
        ...


class GameObject(Protocol):
    def update(self) -> None:
        """Updates the game."""

    def paint(self, canvas: tk.Canvas) -> None:
        """Paints the game."""
