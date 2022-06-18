from dataclasses import dataclass
from collections.abc import Mapping
from enum import Enum
from functools import cache
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


@cache
def load_imgs() -> Mapping[BlockType, Image.Image]:
    return {block_type: load_img(block_type) for block_type in BlockType}


@cache
def load_img(block_type: BlockType) -> Image.Image:
    filename = _img_name(block_type)
    img_fp = Path(f'block/{filename}.png')
    return io.load_img(img_fp)


def _img_name(block_type: BlockType) -> str:
    return f'{block_type.name}Block'


def is_empty(block: Block) -> bool:
    return block.type is BlockType.NORMAL


def is_path(block: Block) -> bool:
    return block.type is BlockType.PATH
