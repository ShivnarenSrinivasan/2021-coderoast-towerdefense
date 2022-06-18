from pathlib import Path
import tkinter as tk
from collections.abc import (
    Sequence,
)
from typing import NewType

from PIL import Image

from . import (
    constants as C,
    block,
    io,
    grid,
)
from .block import Block

Dimension = NewType('Dimension', int)


class Map:
    def __init__(self, name: str):
        self.name = name
        self.image = io.load_img_tk(img_path(name))

    def update(self) -> None:
        pass

    def paint(self, canvas: tk.Canvas) -> None:
        canvas.create_image(0, 0, image=self.image, anchor=tk.NW)


def size(grid_dim: Dimension, block_dim: Dimension) -> Dimension:
    return Dimension(grid_dim * block_dim)


def img_path(map_name: str) -> Path:
    return C.Paths.IMAGES.join('map', f'{map_name}.png')


def load_template(map_name: str) -> Sequence[int]:
    fp = Path(f'map/{map_name}.txt')
    grid_vals = tuple(map(int, io.load_map_text(fp).split()))
    return grid_vals


def make_grid(map_name: str, blockSize: int, gridSize: int) -> list[list[Block]]:
    grid_vals = load_template(map_name)
    blockGrid = []

    def make_row(x: int) -> list[Block]:
        return [make_block(x, y) for y in range(gridSize)]

    def make_block(x: int, y: int) -> Block:
        block_num = grid_vals[gridSize * y + x]
        return block.factory(
            x * blockSize + blockSize / 2,
            y * blockSize + blockSize / 2,
            block_num,
            x,
            y,
        )

    for x in range(gridSize):
        blockGrid.append(make_row(x))

    return blockGrid


def create_map(
    map_name: str,
    block_grid: list[list[Block]],
    block_dim: Dimension,
    grid_dim: Dimension,
) -> None:
    map_size = size(grid_dim, block_dim)
    map_canvas = Image.new("RGBA", (map_size, map_size), (255, 255, 255, 255))
    block_grid = make_grid(map_name, block_dim, grid_dim)
    paint_map_canvas(block_grid, block_dim, map_canvas)
    map_canvas.save(img_path(map_name))


def paint_map_canvas(
    block_grid: list[list[Block]], block_size: int, map_canvas: Image.Image
) -> None:
    axis = block_size / 2
    images = block.load_imgs()

    for block_ in grid.grid_iter(block_grid):
        paint(block_, images[block_.type], map_canvas, axis)


def paint(
    block_: block.Block, img: Image.Image, img_canvas: Image.Image, axis: float
) -> None:
    offset = (int(block_.loc.x - axis), int(block_.loc.y - axis))
    img_canvas.paste(img, offset)
