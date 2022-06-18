from math import degrees
from pathlib import Path
from PIL import ImageTk

from . import io


def load_img(projectile: str) -> ImageTk.PhotoImage:
    return io.load_img_tk(_img_path(projectile))


def load_arrow_img(angle: float) -> ImageTk.PhotoImage:
    img = io.load_img(_img_path('arrow'))
    return ImageTk.PhotoImage(img.rotate(degrees(angle)))


def _img_path(p: str) -> Path:
    return Path(f'projectileImages/{p}.png')
