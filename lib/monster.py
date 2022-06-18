import tkinter as tk
from abc import (
    ABC,
    abstractmethod,
)
from collections.abc import (
    Sequence,
)
from .protocols import Movable


class BaseMonster(ABC, Movable):
    alive: bool
    health: int
    x: int
    y: int
    distanceTravelled: int

    @abstractmethod
    def __init__(self, distance: int):
        ...

    @abstractmethod
    def update(self) -> None:
        ...

    @abstractmethod
    def move(self) -> None:
        ...

    @abstractmethod
    def positionFormula(self, distance: int) -> None:
        ...

    @abstractmethod
    def killed(self) -> None:
        ...

    @abstractmethod
    def gotThrough(self) -> None:
        ...

    @abstractmethod
    def die(self) -> None:
        ...

    @abstractmethod
    def paint(self, canvas: tk.Canvas) -> None:
        ...


def gen_list(monsters: list[BaseMonster]) -> list[list[BaseMonster]]:

    monstersByHealth = sorted(monsters, key=lambda x: x.health, reverse=True)
    monstersByHealthReversed = sorted(monsters, key=lambda x: x.health, reverse=False)
    return [
        monstersByHealth,
        monstersByHealthReversed,
        sort_distance(monsters),
        sort_distance(monsters, reverse=True),
    ]


def sort_distance(
    monsters: Sequence[BaseMonster], reverse: bool = False
) -> list[BaseMonster]:
    return sorted(monsters, key=lambda x: x.distanceTravelled, reverse=reverse)
