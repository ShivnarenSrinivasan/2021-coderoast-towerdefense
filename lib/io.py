from pathlib import Path

from PIL import Image, ImageTk


def load_img(fp: Path) -> ImageTk.PhotoImage:
    return ImageTk.PhotoImage(Image.open(fp))
