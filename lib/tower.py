from __future__ import annotations
import tkinter as tk
from abc import ABC, abstractmethod
from collections.abc import Iterable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Protocol, runtime_checkable

from PIL import ImageTk

from . import (
    grid,
    io,
)
from .protocols import GameObject


class ITowerMap(Protocol):
    displayed: ITower | None

    def __iter__(self) -> Iterable[grid.Point]:
        ...

    def __getitem__(self, p: grid.Point) -> ITower:
        ...

    def __contains__(self, p: grid.Point) -> bool:
        ...

    def __len__(self) -> int:
        ...

    def __setitem__(self, p: grid.Point, tower: ITower) -> None:
        ...

    def select(self, p: grid.Point) -> None:
        ...

    def remove(self, tower: ITower) -> None:
        ...


@dataclass(order=False)
class TowerMap(GameObject):
    _towers: dict[grid.Point, Tower] = field(default_factory=dict)
    displayed: Tower | None = None

    def __iter__(self) -> Iterable[grid.Point]:
        yield from self._towers

    def __getitem__(self, p: grid.Point) -> Tower:
        return self._towers[p]

    def __contains__(self, p: grid.Point) -> bool:
        return p in self._towers

    def __len__(self) -> int:
        return len(self._towers)

    def __setitem__(self, p: grid.Point, tower: Tower) -> None:
        if p in self._towers:
            raise KeyError(f'Point {p} already taken!')
        self._towers[p] = tower

    def select(self, p: grid.Point) -> None:
        tower = self[p]
        tower.clicked = True
        self.displayed = tower

    def update(self) -> None:
        for tower in self._towers.values():
            tower.update()

    def paint(self, canvas: tk.Canvas) -> None:
        for tower in self._towers.values():
            tower.paint(canvas)

        if self.displayed is not None:
            self.displayed.paintSelect(canvas)

    def remove(self, tower: Tower) -> None:
        for point, _tower in self._towers.items():
            if _tower == tower:
                self._towers.pop(point)
                return None
        raise KeyError(f'No such tower {tower} found.')


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

    def upgrade(self) -> None:
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


def load_img(tower: Tower | str) -> ImageTk.PhotoImage:
    match tower:
        case Tower():
            img_fp = Path(f'tower/{tower.__class__.__name__}/{tower.level}.png')
        case str():
            img_fp = Path(f'tower/{towers[tower]}/1.png')
        case _:
            raise ValueError(f"Unhandled type {type(tower)}")

    return io.load_img_tk(img_fp)


class ShootingTower(Tower):
    def __init__(self, x: float, y: float, gridx: int, gridy: int):
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


@runtime_checkable
class ITower(Protocol):
    targetList: int = 0
    stickyTarget: bool
    name: str
    upgradeCost: int


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
