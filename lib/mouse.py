from pathlib import Path
from PIL import ImageTk

from . import io


def load_img(cond: str) -> ImageTk.PhotoImage:
    return io.load_img_tk(Path(f'mouseImages/{cond}.png'))
