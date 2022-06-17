from pathlib import Path

from PIL import Image, ImageTk

from . import constants as C


def load_img(fp: Path) -> ImageTk.PhotoImage:
    return ImageTk.PhotoImage(Image.open(C.Paths.IMAGES.join(fp)))


def load_map_text(fp: Path) -> str:
    with open(C.Paths.TEXTS.join(fp)) as f:
        return f.read()
