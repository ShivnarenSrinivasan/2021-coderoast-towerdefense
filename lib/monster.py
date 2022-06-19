from __future__ import annotations
from collections.abc import (
    Sequence,
)
from pathlib import Path
from typing import (
    Protocol,
    runtime_checkable,
)

from PIL import ImageTk

from . import io
from .protocols import (
    Movable,
    GameObject,
)


@runtime_checkable
class IMonster(GameObject, Movable, Protocol):
    health: int
    value: int
    tick: int
    maxTick: int
    got_through: bool
    damage: int
    children: list[IMonster]


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
    return sorted(monsters, key=lambda x: x.distance_travelled, reverse=reverse)


def load_img(monster: IMonster) -> ImageTk.PhotoImage:
    img_fp = Path(f'monster/{monster.__class__.__name__}.png')
    return io.load_img_tk(img_fp)


def is_dead(monster: IMonster) -> bool:
    return monster.health <= 0
