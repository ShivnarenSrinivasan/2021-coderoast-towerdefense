from __future__ import annotations
from abc import ABC, abstractmethod
import math
import tkinter as tk
from math import degrees
from pathlib import Path
from typing import Protocol
from PIL import ImageTk

from . import (
    io,
    monster,
)
from .maps import Dimension
from .monster import IMonster


class IProjectile(Protocol):
    should_remove: bool

    def update(self, monsters: list[IMonster]):
        ...

    def paint(self, canvas: tk.Canvas) -> None:
        ...


class Projectile(ABC):
    def __init__(self, x, y, damage, speed, block_dim: Dimension):
        self.hit = False
        self._x = x
        self._y = y
        self._speed = block_dim / 2
        self._block_dim = block_dim
        self._damage = damage
        self._speed = speed
        self._target: IMonster | None
        self._image: ImageTk.PhotoImage
        self.should_remove: bool = False

    def update(self, monsters: list[IMonster]) -> None:
        if self._target and monster.is_dead(self._target):
            self.should_remove = True
            return
        if self.hit:
            self._hit_monster()
            self.should_remove = True
        self._move()
        self._check_hit(monsters)

    def _hit_monster(self):
        assert self._target is not None
        self._target.health -= self._damage

    def paint(self, canvas: tk.Canvas) -> None:
        canvas.create_image(self._x, self._y, image=self._image)

    @abstractmethod
    def _move(self) -> None:
        ...

    @abstractmethod
    def _check_hit(self, monsters: list[IMonster]) -> None:
        ...


class TrackingBullet(Projectile):
    def __init__(self, x, y, damage, speed, target, block_dim: Dimension):
        super().__init__(x, y, damage, speed, block_dim)
        self._target = target
        self._image = load_img('bullet')

    def _move(self):
        assert self._target
        length = (
            (self._x - (self._target.x)) ** 2 + (self._y - (self._target.y)) ** 2
        ) ** 0.5
        if length <= 0:
            return
        self._x += self._speed * ((self._target.x) - self._x) / length
        self._y += self._speed * ((self._target.y) - self._y) / length

    def _check_hit(self, _: list[IMonster]):
        assert self._target
        if (
            self._speed**2
            > (self._x - (self._target.x)) ** 2 + (self._y - (self._target.y)) ** 2
        ):
            self.hit = True


class PowerShot(TrackingBullet):
    def __init__(self, x, y, damage, speed, target, slow, block_dim: Dimension):
        super().__init__(x, y, damage, speed, target, block_dim)
        self._slow = slow
        self._image = load_img('powerShot')

    def _hit_monster(self):
        assert self._target
        self._target.health -= self._damage
        if self._target.movement > (self._target.speed) / self._slow:
            self._target.movement = (self._target.speed) / self._slow
        self.should_remove = True


class AngledProjectile(Projectile):
    def __init__(self, x, y, damage, speed, angle, givenRange, block_dim: Dimension):
        super().__init__(x, y, damage, speed, block_dim)
        self._x_change = speed * math.cos(angle)
        self._y_change = speed * math.sin(-angle)
        self._range = givenRange
        self._image = load_arrow_img(angle)
        self._target = None
        self._speed = speed
        self._distance = 0

    def _check_hit(self, monsters: list[IMonster]):
        for monster_ in monsters:
            if (monster_.x - self._x) ** 2 + (monster_.y - self._y) ** 2 <= (
                self._block_dim
            ) ** 2:
                self.hit = True
                self._target = monster_
                return

    def _hit_monster(self):
        assert self._target
        self._target.health -= self._damage
        self._target.tick = 0
        self._target.maxTick = 5
        self.should_remove = True

    def _move(self):
        self._x += self._x_change
        self._y += self._y_change
        self._distance += self._speed
        if self._distance >= self._range:
            self.should_remove = True


def load_img(projectile: str) -> ImageTk.PhotoImage:
    return io.load_img_tk(_img_path(projectile))


def load_arrow_img(angle: float) -> ImageTk.PhotoImage:
    img = io.load_img(_img_path('arrow'))
    return ImageTk.PhotoImage(img.rotate(degrees(angle)))


def _img_path(p: str) -> Path:
    return Path(f'projectileImages/{p}.png')
