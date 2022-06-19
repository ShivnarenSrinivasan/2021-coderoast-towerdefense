import tkinter as tk
from collections.abc import Iterable
from dataclasses import dataclass
from enum import Enum, auto
from typing import Optional
from .protocols import GameObject


class GameState(Enum):
    IDLE = auto()
    WAIT_FOR_SPAWN = auto()
    SPAWNING = auto()


@dataclass
class Stats:
    money: int
    health: int


class Game:
    def __init__(self, title: str, width: int, height: int, timestep: int = 50):
        self.root = tk.Tk()
        self.root.title(title)
        self._running = False
        self.root.protocol("WM_DELETE_WINDOW", self._end)
        self._timer_id: Optional[str] = None
        self._timestep = timestep
        self.frame = tk.Frame(master=self.root)
        self.frame.grid(row=0, column=0)

        self.canvas = tk.Canvas(
            master=self.frame,
            width=width,
            height=height,
            bg="white",
            highlightthickness=0,
        )  # actually creates a window and puts our frame on it
        self.canvas.grid(
            row=0, column=0, rowspan=2, columnspan=1
        )  # makes the window called "canvas" complete

        self.objects: list[GameObject] = []

    def _add_objects(self, objs: Iterable[GameObject]) -> None:
        self.objects.extend(objs)

    def _remove_object(self, obj: GameObject) -> None:
        self.objects.remove(obj)

    def run(self) -> None:
        self._running = True
        self._run()
        self.root.mainloop()

    def _run(self) -> None:
        self._update()
        self._paint()

        if self._running:
            self._timer_id = self.root.after(self._timestep, self._run)

    def _end(self) -> None:
        self._running = False
        if self._timer_id is not None:
            self.root.after_cancel(self._timer_id)
        self.root.destroy()

    def _update(self) -> None:
        """Updates the game."""
        for obj in self.objects:
            obj.update()

    def _paint(self) -> None:
        """Paints the game."""
        self.canvas.delete(tk.ALL)  # clear the screen
        for obj in self.objects:
            obj.paint(self.canvas)
