from collections.abc import (
    Sequence,
)
from typing import (
    Protocol,
    runtime_checkable,
)

from .protocols import Movable
from .game import GameObject


@runtime_checkable
class IMonster(GameObject, Movable, Protocol):
    alive: bool
    health: int
    x: int
    y: int

    def __init__(self, distance: int):
        ...

    def move(self) -> None:
        ...

    def positionFormula(self, distance: float) -> None:
        ...

    def killed(self) -> None:
        ...

    def gotThrough(self) -> None:
        ...

    def die(self) -> None:
        ...


def gen_list(monsters: list[IMonster]) -> list[list[IMonster]]:

    monstersByHealth = sorted(monsters, key=lambda x: x.health, reverse=True)
    monstersByHealthReversed = sorted(monsters, key=lambda x: x.health, reverse=False)
    return [
        monstersByHealth,
        monstersByHealthReversed,
        sort_distance(monsters),
        sort_distance(monsters, reverse=True),
    ]


def sort_distance(
    monsters: Sequence[IMonster], reverse: bool = False
) -> list[IMonster]:
    return sorted(monsters, key=lambda x: x.distanceTravelled, reverse=reverse)
