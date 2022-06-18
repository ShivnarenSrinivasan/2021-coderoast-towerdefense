import tkinter as tk
from typing import Protocol


class Movable(Protocol):
    distanceTravelled: float


class GameObject(Protocol):
    def update(self) -> None:
        """Updates the game."""

    def paint(self, canvas: tk.Canvas) -> None:
        """Paints the game."""
