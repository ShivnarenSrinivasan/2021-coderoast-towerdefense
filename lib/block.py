from dataclasses import dataclass
from enum import Enum
from pathlib import Path

from PIL import Image

from . import (
    grid,
    io,
)


class BlockType(Enum):
    NORMAL = 'Empty'
    PATH = 'Not Empty Path'
    WATER = 'Not Empty Water'


@dataclass
class Block:
    loc: grid.Loc
    grid_loc: grid.Point
    type: BlockType


def factory(x: float, y: float, block_num: int, gridx: int, gridy: int) -> Block:
    return Block(
        grid.Loc(x, y),
        grid.Point(gridx, gridy),
        tuple(BlockType)[block_num],
    )


def load_img(block: Block) -> Image.Image:
    filename = f'{block.type.name}Block'
    img_fp = Path(f'block/{filename}.png')
    return io.load_img(img_fp)


def is_empty(block: Block) -> bool:
    return block.type is BlockType.NORMAL


def is_path(block: Block) -> bool:
    return block.type is BlockType.PATH
