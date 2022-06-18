from dataclasses import dataclass
from enum import Enum

from . import grid


class BlockType(Enum):
    NORMAL = 'Empty'
    PATH = 'Not Empty Path'
    WATER = 'Not Empty Water'


@dataclass
class Block:
    loc: grid.Loc
    block_num: int
    grid_loc: grid.Point
    type: BlockType


def factory(x: float, y: float, block_num: int, gridx: int, gridy: int) -> Block:
    return Block(
        grid.Loc(x, y),
        block_num,
        grid.Point(gridx, gridy),
        tuple(BlockType)[block_num],
    )


def is_empty(block: Block) -> bool:
    return block.type is BlockType.NORMAL


def is_path(block: Block) -> bool:
    return block.type is BlockType.PATH
