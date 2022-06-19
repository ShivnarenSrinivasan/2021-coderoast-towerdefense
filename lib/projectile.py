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
        self.x = x
        self.y = y
        self.speed = block_dim / 2
        self.block_dim = block_dim
        self.damage = damage
        self.speed = speed
        self.target: IMonster | None
        self.image: ImageTk.PhotoImage
        self.should_remove: bool = False

    def update(self, monsters: list[IMonster]) -> None:
        if self.target and monster.is_dead(self.target):
            self.should_remove = True
            return
        if self.hit:
            self.gotMonster()
            self.should_remove = True
        self.move()
        self.checkHit(monsters)

    def gotMonster(self):
        assert self.target is not None
        self.target.health -= self.damage

    def paint(self, canvas: tk.Canvas) -> None:
        canvas.create_image(self.x, self.y, image=self.image)

    @abstractmethod
    def move(self) -> None:
        ...

    @abstractmethod
    def checkHit(self, monsters: list[IMonster]) -> None:
        ...


class TrackingBullet(Projectile):
    def __init__(self, x, y, damage, speed, target, block_dim: Dimension):
        super().__init__(x, y, damage, speed, block_dim)
        self.target = target
        self.image = load_img('bullet')
        self.length: float

    def move(self):
        assert self.target
        self.length = (
            (self.x - (self.target.x)) ** 2 + (self.y - (self.target.y)) ** 2
        ) ** 0.5
        if self.length <= 0:
            return
        self.x += self.speed * ((self.target.x) - self.x) / self.length
        self.y += self.speed * ((self.target.y) - self.y) / self.length

    def checkHit(self, _: list[IMonster]):
        assert self.target
        if (
            self.speed**2
            > (self.x - (self.target.x)) ** 2 + (self.y - (self.target.y)) ** 2
        ):
            self.hit = True


class PowerShot(TrackingBullet):
    def __init__(self, x, y, damage, speed, target, slow, block_dim: Dimension):
        super().__init__(x, y, damage, speed, target, block_dim)
        self.slow = slow
        self.image = load_img('powerShot')

    def gotMonster(self):
        assert self.target
        self.target.health -= self.damage
        if self.target.movement > (self.target.speed) / self.slow:
            self.target.movement = (self.target.speed) / self.slow
        self.should_remove = True


class AngledProjectile(Projectile):
    def __init__(self, x, y, damage, speed, angle, givenRange, block_dim: Dimension):
        super().__init__(x, y, damage, speed, block_dim)
        self.xChange = speed * math.cos(angle)
        self.yChange = speed * math.sin(-angle)
        self.range = givenRange
        self.image = load_arrow_img(angle)
        self.target = None
        self.speed = speed
        self.distance = 0

    def checkHit(self, monsters: list[IMonster]):
        for monster_ in monsters:
            if (monster_.x - self.x) ** 2 + (monster_.y - self.y) ** 2 <= (
                self.block_dim
            ) ** 2:
                self.hit = True
                self.target = monster_
                return

    def gotMonster(self):
        assert self.target
        self.target.health -= self.damage
        self.target.tick = 0
        self.target.maxTick = 5
        self.should_remove = True

    def move(self):
        self.x += self.xChange
        self.y += self.yChange
        self.distance += self.speed
        if self.distance >= self.range:
            self.should_remove = True


def load_img(projectile: str) -> ImageTk.PhotoImage:
    return io.load_img_tk(_img_path(projectile))


def load_arrow_img(angle: float) -> ImageTk.PhotoImage:
    img = io.load_img(_img_path('arrow'))
    return ImageTk.PhotoImage(img.rotate(degrees(angle)))


def _img_path(p: str) -> Path:
    return Path(f'projectileImages/{p}.png')
