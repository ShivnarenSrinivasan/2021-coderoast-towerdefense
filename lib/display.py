import tkinter as tk
from typing import (
    NamedTuple,
    TypedDict,
)


from . import buttons
from ._type_aliases import _Anchor


class Displayboard:
    def __init__(self, frame: tk.Frame, health: int, money: int):
        self.canvas = tk.Canvas(
            master=frame, width=600, height=80, bg="gray", highlightthickness=0
        )
        self.canvas.grid(row=2, column=0)
        self.healthbar = Healthbar(health)
        self.moneybar = Moneybar(money)
        self.nextWaveButton = buttons.NextWaveButton()

    def update(self, health: int, money: int) -> None:
        self.healthbar.update(health)
        self.moneybar.update(money)

    def paint(self, color: str) -> None:
        self.canvas.delete(tk.ALL)  # clear the screen
        self.healthbar.paint(self.canvas)
        self.moneybar.paint(self.canvas)
        self.nextWaveButton.paint(self.canvas, color)


class Healthbar:
    def __init__(self, health: int):
        self.text = str(health)

    def update(self, health: int) -> None:
        self.text = str(health)

    def paint(self, canvas: tk.Canvas) -> None:
        canvas.create_text(40, 40, text=f"Health: {self.text}", fill="black")


class Moneybar:
    def __init__(self, money: int):
        self.text = str(money)

    def update(self, money: int) -> None:
        self.text = str(money)

    def paint(self, canvas: tk.Canvas) -> None:
        canvas.create_text(240, 40, text=f"Money: {self.text}", fill="black")


class Value(NamedTuple):
    coord: tuple[float, float]
    text: str


class Text(TypedDict):
    text: str
    font: tuple[str, int]
    fill: str
    anchor: _Anchor
