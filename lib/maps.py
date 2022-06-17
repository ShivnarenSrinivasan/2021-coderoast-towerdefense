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
    return C.Paths.IMAGES.join('mapImages', f'{map_name}.png')


def load_template(map_name: str) -> Sequence[int]:
    with open("texts/mapTexts/" + map_name + ".txt") as map_file:
        grid_vals = list(map(int, (map_file.read()).split()))
    return grid_vals
