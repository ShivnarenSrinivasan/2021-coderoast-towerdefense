from pathlib import Path
import tkinter as tk
from collections.abc import (
    Sequence,
)

from . import (
    constants as C,
    io,
)


class Map:
    def __init__(self, name: str):
        self.name = name
        self.image = io.load_img(img_path(name))

    def update(self) -> None:
        pass

    def paint(self, canvas: tk.Canvas) -> None:
        canvas.create_image(0, 0, image=self.image, anchor=tk.NW)


def img_path(map_name: str) -> Path:
    return C.Paths.IMAGES.join('map', f'{map_name}.png')


def load_template(map_name: str) -> Sequence[int]:
    fp = Path(f'map/{map_name}.txt')
    grid_vals = tuple(map(int, io.load_map_text(fp).split()))
    return grid_vals
