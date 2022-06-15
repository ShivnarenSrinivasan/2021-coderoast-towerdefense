import tkinter as tk


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
