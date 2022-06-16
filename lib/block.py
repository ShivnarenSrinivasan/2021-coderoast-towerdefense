from dataclasses import dataclass
import grid


@dataclass
class Block:
    loc: grid.Loc
    blockNumber: int
    grid: grid.Point
    canPlace: bool


class NormalBlock(Block):
    ...


class PathBlock(Block):
    ...


class WaterBlock(Block):
    ...


def block_factory(x: float, y: float, block_num: int, gridx: int, gridy: int) -> Block:
    blocks = (
        NormalBlock,
        PathBlock,
        WaterBlock,
    )
    BlockType = blocks[block_num]

    return BlockType(
        grid.Loc(x, y),
        block_num,
        grid.Point(gridx, gridy),
        canPlace=BlockType is NormalBlock,
    )
