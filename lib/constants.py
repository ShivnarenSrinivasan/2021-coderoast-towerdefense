from enum import Enum
from pathlib import Path


class Paths(Enum):
    IMAGES = 'images'
    TEXTS = 'texts'

    @classmethod
    def ROOT(cls) -> Path:
        return Path(__file__).parent.resolve()

    @property
    def path(self) -> Path:
        return self.ROOT().joinpath(self.value)

    def join(self, *path: Path | str) -> Path:
        return self.path.joinpath(*path)
