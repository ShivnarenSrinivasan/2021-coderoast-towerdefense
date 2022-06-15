from abc import ABC, abstractmethod


class Button(ABC):
    """Generic Button."""

    def __init__(self, x, y, xTwo, yTwo):
        self.x = x
        self.y = y
        self.xTwo = xTwo
        self.yTwo = yTwo

    def checkPress(self, x: int, y: int):
        if x >= self.x and y >= self.y and x <= self.xTwo and y <= self.yTwo:
            self.pressed()
            return True
        return False

    @abstractmethod
    def pressed(self) -> None:
        """Implement press functionality."""

    def paint(self, canvas):
        canvas.create_rectangle(
            self.x, self.y, self.xTwo, self.yTwo, fill="red", outline="black"
        )


def is_within_bounds(self, x: int, y: int) -> bool:
    return self.x <= x <= self.xTwo and self.y <= y <= self.yTwo
