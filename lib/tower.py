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


class Tower(ABC):
    def __init__(self, x: float, y: float, gridx: int, gridy: int):
        self.level: int = 1
        self.range: int
        self.x = x
        self.y = y
        self.gridx = gridx
        self.gridy = gridy
        self.image = load_img(self)
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
        for proj in self._projectiles:
            proj.paint(canvas)


def load_img(tower: ITower | Tower | str) -> ImageTk.PhotoImage:
    match tower:
        case Tower():
            img_fp = Path(f'tower/{tower.__class__.__name__}/{tower.level}.png')
        case str():
            img_fp = Path(f'tower/{towers[tower]}/1.png')
        case _:
            raise ValueError(f"Unhandled type {type(tower)}")

    return io.load_img_tk(img_fp)


@runtime_checkable
class ITower(Protocol):
    targetList: int = 0
    stickyTarget: bool
    name: str
    upgradeCost: int

    def upgrade(self) -> None:
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
        self.bulletsPerSecond: int
        self.ticks = 0
        self.damage = 0
        self.block_dim = block_dim
        self.target = None
        self.targetList = 0
        self.stickyTarget = False
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
        if self.ticks != 20 / self.bulletsPerSecond:
            self.ticks += 1

        if not self.stickyTarget:
            for monster_ in monster_list:
                if (self.range + self.block_dim / 2) ** 2 >= (
                    self.x - monster_.x
                ) ** 2 + (self.y - monster_.y) ** 2:
                    self.target = monster_

        if self.target:
            if (
                not monster.is_dead(self.target)
                and (self.range + self.block_dim / 2)
                >= ((self.x - self.target.x) ** 2 + (self.y - self.target.y) ** 2)
                ** 0.5
            ):
                if self.ticks >= 20 / self.bulletsPerSecond:
                    self.shoot()
                    self.ticks = 0
            else:
                self.target = None
        elif self.stickyTarget:
            for monster_ in monster_list:
                if (self.range + self.block_dim / 2) ** 2 >= (
                    self.x - monster_.x
                ) ** 2 + (self.y - monster_.y) ** 2:
                    self.target = monster_

    def shoot(self) -> None:
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
        self.range = block_dim * 10
        self.bulletsPerSecond = 1
        self.damage = 10
        self.speed = block_dim
        self.upgradeCost = 50
        self.angle: float
        self._projectile_type = AngledProjectile

    def nextLevel(self):
        if self.level == 2:
            self.upgradeCost = 100
            self.range = self.block_dim * 11
            self.damage = 12
        elif self.level == 3:
            self.upgradeCost = None
            self.bulletsPerSecond = 2

    def shoot(self):
        assert self.target is not None
        self.angle = math.atan2(self.y - self.target.y, self.target.x - self.x)
        self._add(
            self._projectile_type(
                self.x,
                self.y,
                self.damage,
                self.speed,
                self.angle,
                self.range + self.block_dim / 2,
                self.block_dim,
            )
        )


class BulletShooterTower(TargetingTower):
    def __init__(
        self, x, y, gridx, gridy, block_dim: Dimension, monsters: list[IMonster]
    ):
        super().__init__(x, y, gridx, gridy, block_dim, monsters)
        self.name = "Bullet Shooter"
        self.infotext = "BulletShooterTower at [" + str(gridx) + "," + str(gridy) + "]."
        self.range = block_dim * 6
        self.bulletsPerSecond = 4
        self.damage = 5
        self.speed = block_dim / 2
        self._projectile_type = TrackingBullet

    def shoot(self):
        self._add(
            self._projectile_type(
                self.x, self.y, self.damage, self.speed, self.target, self.block_dim
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
        self.range = block_dim * 8
        self.bulletsPerSecond = 10
        self.damage = 1
        self.speed = block_dim
        self.slow = 3
        self._projectile_type = PowerShot

    def shoot(self):
        self._add(
            self._projectile_type(
                self.x,
                self.y,
                self.damage,
                self.speed,
                self.target,
                self.slow,
                self.block_dim,
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
        self.range = block_dim * 5
        self.bulletsPerSecond = 1
        self.damage = 10
        self.speed = block_dim
        self.angle: float
        self._projectile_type = AngledProjectile

    def shoot(self):
        for i in range(8):
            self.angle = math.radians(i * 45)
            self._add(
                self._projectile_type(
                    self.x,
                    self.y,
                    self.damage,
                    self.speed,
                    self.angle,
                    self.range,
                    self.block_dim,
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
