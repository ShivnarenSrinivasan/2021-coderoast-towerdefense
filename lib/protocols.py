import tkinter as tk
from typing import Protocol


class Movable(Protocol):
    x: float
    y: float
    distance_travelled: float
    speed: float
    movement: float


class GameObject(Protocol):
    def update(self) -> None:
        """Updates the game."""

    def paint(self, canvas: tk.Canvas) -> None:
        """Paints the game."""
