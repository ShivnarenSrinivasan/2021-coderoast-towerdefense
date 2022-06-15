from __future__ import annotations
import tkinter as tk
from abc import ABC, abstractmethod

from PIL import Image, ImageTk

import grid


class Tower(ABC):
    def __init__(self, x: float, y: float, gridx: int, gridy: int):
        self.upgradeCost = None
        self.level: int = 1
        self.range: int = 0
        self.clicked: bool = False
        self.x = x
        self.y = y
        self.gridx = gridx
        self.gridy = gridy
        self.image = Image.open(
            "images/towerImages/" + self.__class__.__name__ + "/1.png"
        )
        self.image = ImageTk.PhotoImage(self.image)

    @abstractmethod
    def update(self) -> None:
        ...

    @abstractmethod
    def nextLevel(self) -> None:
        ...

    def upgrade(self):
        self.level = self.level + 1
        self.image = Image.open(
            "images/towerImages/"
            + self.__class__.__name__
            + "/"
            + str(self.level)
            + ".png"
        )
        self.image = ImageTk.PhotoImage(self.image)
        self.nextLevel()

    def sold(self, tower_map: dict[grid.Point, Tower]) -> None:
        point = grid.Point(self.gridx, self.gridy)
        tower_map.pop(point)

    def paintSelect(self, canvas: tk.Canvas) -> None:
        canvas.create_oval(
            self.x - self.range,
            self.y - self.range,
            self.x + self.range,
            self.y + self.range,
            fill=None,
            outline="white",
        )

    def paint(self, canvas: tk.Canvas) -> None:
        canvas.create_image(self.x, self.y, image=self.image, anchor=tk.CENTER)


class ShootingTower(Tower):
    def __init__(self, x, y, gridx, gridy):
        super(ShootingTower, self).__init__(x, y, gridx, gridy)
        self.bulletsPerSecond = None
        self.ticks = 0
        self.damage = 0
        self.speed = None

    def update(self) -> None:
        self.prepareShot()

    @abstractmethod
    def prepareShot(self) -> None:
        ...
