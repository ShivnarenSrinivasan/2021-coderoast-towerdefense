import grid


class Block:
    def __init__(self, x: float, y: float, blockNumber: int, gridx: int, gridy: int):
        self.loc = grid.Loc(x, y)
        self.canPlace = True
        self.blockNumber = blockNumber
        self.grid = grid.Point(gridx, gridy)
        self.image = None


class NormalBlock(Block):
    def __init__(self, x, y, blockNumber, gridx, gridy):
        super(NormalBlock, self).__init__(x, y, blockNumber, gridx, gridy)


class PathBlock(Block):
    def __init__(self, x, y, blockNumber, gridx, gridy):
        super(PathBlock, self).__init__(x, y, blockNumber, gridx, gridy)
        self.canPlace = False


class WaterBlock(Block):
    def __init__(self, x, y, blockNumber, gridx, gridy):
        super(WaterBlock, self).__init__(x, y, blockNumber, gridx, gridy)
        self.canPlace = False


def block_factory(x: float, y: float, block_num: int, gridx: int, gridy: int) -> Block:
    blocks = (
        NormalBlock,
        PathBlock,
        WaterBlock,
    )
    BlockType = blocks[block_num]
    return BlockType(x, y, block_num, gridx, gridy)
