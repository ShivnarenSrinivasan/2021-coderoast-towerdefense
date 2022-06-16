import tkinter as tk

from PIL import (
    Image,
    ImageTk,
)


class Map:
    def __init__(self, map_size: int):
        self.image: ImageTk.PhotoImage
        self.map_size = map_size

    def load(self, map_name: str) -> None:
        self.image = self._load_image(map_name)

    def _load_image(self, map_name: str) -> ImageTk.PhotoImage:
        return ImageTk.PhotoImage(Image.open(f'images/mapImages/{map_name}.png'))

    def update(self) -> None:
        pass

    def paint(self, canvas: tk.Canvas) -> None:
        canvas.create_image(0, 0, image=self.image, anchor=tk.NW)
