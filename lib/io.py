from pathlib import Path

from PIL import Image, ImageTk

from . import constants as C


def load_img(fp: Path) -> ImageTk.PhotoImage:
    return ImageTk.PhotoImage(Image.open(C.Paths.IMAGES.join(fp)))
