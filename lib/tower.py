from __future__ import annotations
import tkinter as tk
from abc import ABC, abstractmethod
from pathlib import Path


from . import (
    grid,
    io,
)


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
        self.image = io.load_img(self._img_fp)

    @abstractmethod
    def update(self) -> None:
        ...

    @abstractmethod
    def nextLevel(self) -> None:
        ...

    @property
    def _img_fp(self) -> Path:
        return Path(f'tower/{self.__class__.__name__}/{self.level}.png')

    def upgrade(self):
        self.level = self.level + 1
        self.image = io.load_img(self._img_fp)
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
            fill='',
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


def cost(tower: str) -> int:
    _costs = {
        "Arrow Shooter": 150,
        "Bullet Shooter": 150,
        "Tack Tower": 150,
        "Power Tower": 200,
    }
    return _costs[tower]
