from __future__ import annotations
import tkinter as tk
import functools
from abc import ABC, abstractmethod
from pathlib import Path
from typing import NoReturn, overload

from PIL import ImageTk

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
        self.image = load_img(self)

    @abstractmethod
    def update(self) -> None:
        ...

    @abstractmethod
    def nextLevel(self) -> None:
        ...

    def upgrade(self):
        self.level = self.level + 1
        self.image = load_img(self)
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


@functools.singledispatch
def _load_img(obj: object) -> NoReturn:
    raise ValueError(f"Unhandled type {type(obj)}")


@_load_img.register
def _(tower: Tower) -> ImageTk.PhotoImage:
    img_fp = Path(f'tower/{tower.__class__.__name__}/{tower.level}.png')
    return io.load_img(img_fp)


@_load_img.register
def _(tower: str) -> ImageTk.PhotoImage:
    img_fp = Path(f'tower/{towers[tower]}/1.png')
    return io.load_img(img_fp)


@overload
def load_img(tower: Tower) -> ImageTk.PhotoImage:
    ...


@overload
def load_img(tower: str) -> ImageTk.PhotoImage:
    ...


def load_img(*args, **kwargs):
    return _load_img(*args, **kwargs)


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


towers = {
    "Arrow Shooter": "ArrowShooterTower",
    "Bullet Shooter": "BulletShooterTower",
    "Tack Tower": "TackTower",
    "Power Tower": "PowerTower",
}


def cost(tower: str) -> int:
    _costs = {
        "Arrow Shooter": 150,
        "Bullet Shooter": 150,
        "Tack Tower": 150,
        "Power Tower": 200,
    }
    return _costs[tower]
