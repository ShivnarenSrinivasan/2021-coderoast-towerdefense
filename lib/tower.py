from __future__ import annotations
import math
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
    monster,
)
from .protocols import GameObject
from .maps import Dimension
from .monster import IMonster
from .projectile import (
    IProjectile,
    AngledProjectile,
    PowerShot,
    TrackingBullet,
)


@runtime_checkable
class ITowerMap(GameObject, Protocol):
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


@runtime_checkable
class ITower(Protocol):
    targetList: int = 0
    stickyTarget: bool
    name: str
    upgradeCost: int | None

    def upgrade(self) -> None:
        ...


class Tower(ABC):
    def __init__(self, x: float, y: float, gridx: int, gridy: int):
        self.level: int = 1
        self._range: int
        self._x = x
        self._y = y
        self._gridx = gridx
        self.gridy = gridy
        self.image = load_img(self)
        self.targetList = 0
        self.stickyTarget = False
        self.name: str
        self.upgradeCost: int | None
        self._projectiles: list[IProjectile] = []

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
        point = grid.Point(self._gridx, self.gridy)
        tower_map.pop(point)

    def paintSelect(self, canvas: tk.Canvas) -> None:
        canvas.create_oval(
            self._x - self._range,
            self._y - self._range,
            self._x + self._range,
            self._y + self._range,
            fill='',
            outline="white",
        )

    def paint(self, canvas: tk.Canvas) -> None:
        canvas.create_image(self._x, self._y, image=self.image, anchor=tk.CENTER)
        for proj in self._projectiles:
            proj.paint(canvas)


class TargetingTower(Tower):
    def __init__(
        self,
        x: float,
        y: float,
        gridx: int,
        gridy: int,
        block_dim: Dimension,
        monsters: list[IMonster],
    ):
        super().__init__(x, y, gridx, gridy)
        self._bullets_per_second: int
        self._ticks = 0
        self._damage = 0
        self._block_dim = block_dim
        self._target = None
        self._monsters = monsters

    def update(self) -> None:
        self._prepareShot()
        for proj in self._projectiles:
            proj.update(self._monsters)
            if proj.should_remove:
                self._projectiles.remove(proj)

    def nextLevel(self) -> None:
        ...

    def _prepareShot(self):
        monster_list = monster.gen_list(self._monsters)[self.targetList]
        if self._ticks != 20 / self._bullets_per_second:
            self._ticks += 1

        if not self.stickyTarget:
            for monster_ in monster_list:
                if (self._range + self._block_dim / 2) ** 2 >= (
                    self._x - monster_.x
                ) ** 2 + (self._y - monster_.y) ** 2:
                    self._target = monster_

        if self._target:
            if (
                not monster.is_dead(self._target)
                and (self._range + self._block_dim / 2)
                >= ((self._x - self._target.x) ** 2 + (self._y - self._target.y) ** 2)
                ** 0.5
            ):
                if self._ticks >= 20 / self._bullets_per_second:
                    self._shoot()
                    self._ticks = 0
            else:
                self._target = None
        elif self.stickyTarget:
            for monster_ in monster_list:
                if (self._range + self._block_dim / 2) ** 2 >= (
                    self._x - monster_.x
                ) ** 2 + (self._y - monster_.y) ** 2:
                    self._target = monster_

    def _shoot(self) -> None:
        ...

    def _add(self, proj: IProjectile) -> None:
        self._projectiles.append(proj)

    def _remove(self, proj: IProjectile) -> None:
        self._projectiles.remove(proj)


class ArrowShooterTower(TargetingTower):
    def __init__(
        self, x, y, gridx, gridy, block_dim: Dimension, monsters: list[IMonster]
    ):
        super().__init__(x, y, gridx, gridy, block_dim, monsters)
        self.name = "Arrow Shooter"
        self.infotext = "ArrowShooterTower at [" + str(gridx) + "," + str(gridy) + "]."
        self._range = block_dim * 10
        self._bullets_per_second = 1
        self._damage = 10
        self._speed = block_dim
        self.upgradeCost = 50
        self._projectile_type = AngledProjectile

    @property
    def _angle(self) -> float:
        assert self._target is not None
        return math.atan2(self._y - self._target.y, self._target.x - self._x)

    def nextLevel(self):
        if self.level == 2:
            self.upgradeCost = 100
            self._range = self._block_dim * 11
            self._damage = 12
        elif self.level == 3:
            self.upgradeCost = None
            self._bullets_per_second = 2

    def _shoot(self):
        self._add(
            self._projectile_type(
                self._x,
                self._y,
                self._damage,
                self._speed,
                self._angle,
                self._range + self._block_dim / 2,
                self._block_dim,
            )
        )


class BulletShooterTower(TargetingTower):
    def __init__(
        self, x, y, gridx, gridy, block_dim: Dimension, monsters: list[IMonster]
    ):
        super().__init__(x, y, gridx, gridy, block_dim, monsters)
        self.name = "Bullet Shooter"
        self.infotext = "BulletShooterTower at [" + str(gridx) + "," + str(gridy) + "]."
        self._range = block_dim * 6
        self._bullets_per_second = 4
        self._damage = 5
        self._speed = block_dim / 2
        self._projectile_type = TrackingBullet

    def _shoot(self):
        self._add(
            self._projectile_type(
                self._x,
                self._y,
                self._damage,
                self._speed,
                self._target,
                self._block_dim,
            )
        )

    def nextLevel(self) -> None:
        ...


class PowerTower(TargetingTower):
    def __init__(
        self, x, y, gridx, gridy, block_dim: Dimension, monsters: list[IMonster]
    ):
        super().__init__(x, y, gridx, gridy, block_dim, monsters)
        self.name = "Power Tower"
        self.infotext = "PowerTower at [" + str(gridx) + "," + str(gridy) + "]."
        self._range = block_dim * 8
        self._bullets_per_second = 10
        self._damage = 1
        self._speed = block_dim
        self._slow = 3
        self._projectile_type = PowerShot

    def _shoot(self):
        self._add(
            self._projectile_type(
                self._x,
                self._y,
                self._damage,
                self._speed,
                self._target,
                self._slow,
                self._block_dim,
            )
        )

    def nextLevel(self) -> None:
        ...


class TackTower(TargetingTower):
    def __init__(
        self, x, y, gridx, gridy, block_dim: Dimension, monsters: list[IMonster]
    ):
        super().__init__(x, y, gridx, gridy, block_dim, monsters)
        self.name = "Tack Tower"
        self.infotext = "TackTower at [" + str(gridx) + "," + str(gridy) + "]."
        self._range = block_dim * 5
        self._bullets_per_second = 1
        self._damage = 10
        self._speed = block_dim
        self.angle: float
        self._projectile_type = AngledProjectile

    def _shoot(self):
        for i in range(8):
            self.angle = math.radians(i * 45)
            self._add(
                self._projectile_type(
                    self._x,
                    self._y,
                    self._damage,
                    self._speed,
                    self.angle,
                    self._range,
                    self._block_dim,
                )
            )

    def nextLevel(self) -> None:
        ...


def tower_factory(
    tower_: str,
    loc: grid.Loc,
    grid_: grid.Point,
    block_dim: Dimension,
    monsters: list[IMonster],
) -> Tower:
    towers_ = {
        "Arrow Shooter": ArrowShooterTower,
        "Bullet Shooter": BulletShooterTower,
        "Tack Tower": TackTower,
        "Power Tower": PowerTower,
    }
    tower_type = towers_[tower_]
    return tower_type(loc.x, loc.y, grid_.x, grid_.y, block_dim, monsters)


def load_img(tower: ITower | Tower | str) -> ImageTk.PhotoImage:
    match tower:
        case Tower():
            img_fp = Path(f'tower/{tower.__class__.__name__}/{tower.level}.png')
        case str():
            img_fp = Path(f'tower/{_towers[tower]}/1.png')
        case _:
            raise ValueError(f"Unhandled type {type(tower)}")

    return io.load_img_tk(img_fp)


_towers = {
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
