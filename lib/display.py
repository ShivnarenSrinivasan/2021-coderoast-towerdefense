import tkinter as tk
import itertools as it
from typing import (
    Any,
    Iterable,
    NamedTuple,
)
from PIL import (
    ImageTk,
    Image,
)

from . import (
    buttons,
    tower,
    grid,
    game,
)
from .buttons import (
    Button,
    SellButton,
    StickyButton,
    TargetButton,
    UpgradeButton,
)
from .tower import (
    ITowerMap,
    ITower,
)
from ._type_aliases import _Anchor


class Infoboard:
    def __init__(self, frame: tk.Frame, tower_map: ITowerMap):
        self.canvas = tk.Canvas(
            master=frame, width=162, height=174, bg="gray", highlightthickness=0
        )
        self.tower_map = tower_map
        self.canvas.grid(row=0, column=1)
        self.image = ImageTk.PhotoImage(Image.open("images/infoBoard.png"))
        self.canvas.create_image(0, 0, image=self.image, anchor=tk.NW)
        self.currentButtons: list[buttons.Button] = []
        self.towerImage: ImageTk.PhotoImage | None
        self.text: str | None

    def buttonsCheck(self, point: grid.Point, money: int) -> int:
        amt = 0
        displayTower = self.tower_map.displayed
        for btn in self.currentButtons:
            if not btn.can_press(point):
                continue

            btn.press(self.tower_map)

            if isinstance(btn, UpgradeButton):
                assert displayTower is not None and displayTower.upgradeCost is not None
                if money >= displayTower.upgradeCost:
                    amt = -displayTower.upgradeCost
                    displayTower.upgrade()
            if isinstance(btn, SellButton):
                assert displayTower is not None and displayTower.upgradeCost is not None
                amt = int(0.5 * displayTower.upgradeCost)
            self.displaySpecific()
            return amt
        return amt

    def displaySpecific(self):
        self.canvas.delete(tk.ALL)  # clear the screen
        self.canvas.create_image(0, 0, image=self.image, anchor=tk.NW)
        self.currentButtons = []
        displayTower = self.tower_map.displayed
        if displayTower is None:
            return

        self.towerImage = tower.load_img(displayTower)
        self.canvas.create_text(80, 75, text=displayTower.name, font=("times", 20))
        self.canvas.create_image(5, 5, image=self.towerImage, anchor=tk.NW)

        if not isinstance(displayTower, ITower):
            return None

        self.currentButtons.extend(_gen_draw_info_buttons(self.canvas))

        self.currentButtons.extend(_gen_draw_misc_buttons(self.canvas, displayTower))

        self.currentButtons[displayTower.targetList].paint(self.canvas)
        if displayTower.stickyTarget:
            self.currentButtons[4].paint(self.canvas)

    def displayGeneric(self, selectedTower: str):
        self.currentButtons = []
        if selectedTower == "<None>":
            self.text = None
            self.towerImage = None
        else:
            self.text = selectedTower + " cost: " + str(tower.cost(selectedTower))
            self.towerImage = tower.load_img(selectedTower)
        self.canvas.delete(tk.ALL)  # clear the screen
        self.canvas.create_image(0, 0, image=self.image, anchor=tk.NW)
        self.canvas.create_text(80, 75, text=self.text if self.text else '')
        self.canvas.create_image(5, 5, image=self.towerImage, anchor=tk.NW)


def _gen_draw_info_buttons(canvas: tk.Canvas) -> Iterable[Button]:
    def _target_btns(canvas: tk.Canvas) -> Iterable[Button]:
        _c1, _c2 = (26, 30), (35, 39)

        def make_btn(
            c1: tuple[int, int], c2: tuple[int, int], btn_type: int
        ) -> TargetButton:
            return TargetButton(*buttons.make_coords(*c1, *c2), btn_type)

        buttons_and_text: list[tuple[Button, Value]] = [
            (make_btn(_c1, _c2, 0), Value((37, 28), '> Health')),
            (make_btn(_c1, _c2, 1), Value((37, 48), '< Health')),
            (make_btn((92, 50), (101, 59), 2), Value((103, 48), "> Distance")),
            (make_btn((92, 30), (101, 39), 2), Value((103, 28), "< Distance")),
        ]

        create_texts(
            canvas,
            buttons_and_text,
            font=('times', 12),
            fill='white',
            anchor=tk.NW,
        )

        return (item[0] for item in buttons_and_text)

    btns = _target_btns(canvas)
    return btns


def _gen_draw_misc_buttons(canvas: tk.Canvas, tower_: ITower) -> Iterable[Button]:
    BtnVal = list[tuple[Button, Value | None]]
    btn_text: BtnVal = [
        (StickyButton(*buttons.make_coords(10, 40, 19, 49)), None),
        (
            SellButton(*buttons.make_coords(5, 145, 78, 168)),
            Value((28, 146), 'Sell'),
        ),
    ]

    # NOTE: This section is quite confusing, see if it can be simplified
    btn_text1: BtnVal
    if tower_.upgradeCost:
        btn_text1 = [(UpgradeButton(*buttons.make_coords(82, 145, 155, 168)), None)]
        canvas.create_text(
            (120, 157),
            text="Upgrade: " + str(tower_.upgradeCost),
            font=("times", 12),
            fill="light green",
            anchor=tk.CENTER,
        )
    else:
        btn_text1 = []

    btn_texts_ = tuple(it.chain(btn_text, btn_text1))
    # --------------------------

    create_texts(
        canvas,
        btn_texts_,
        font=("times", 22),
        fill="light green",
        anchor=tk.NW,
    )

    return (item[0] for item in btn_texts_)


class Displayboard:
    def __init__(self, frame: tk.Frame, stats: game.Stats):
        self.canvas = tk.Canvas(
            master=frame, width=600, height=80, bg="gray", highlightthickness=0
        )
        self.canvas.grid(row=2, column=0)
        self.healthbar = Healthbar(stats.health)
        self.moneybar = Moneybar(stats.money)
        self.nextWaveButton = buttons.NextWaveButton()

    def update(self, stats: game.Stats) -> None:
        self.healthbar.update(stats.health)
        self.moneybar.update(stats.money)

    def paint(self, color: str) -> None:
        self.canvas.delete(tk.ALL)  # clear the screen
        self.healthbar.paint(self.canvas)
        self.moneybar.paint(self.canvas)
        self.nextWaveButton.paint(self.canvas, color)


class Healthbar:
    def __init__(self, health: int):
        self.text = str(health)

    def update(self, health: int) -> None:
        self.text = str(health)

    def paint(self, canvas: tk.Canvas) -> None:
        canvas.create_text(40, 40, text=f"Health: {self.text}", fill="black")


class Moneybar:
    def __init__(self, money: int):
        self.text = str(money)

    def update(self, money: int) -> None:
        self.text = str(money)

    def paint(self, canvas: tk.Canvas) -> None:
        canvas.create_text(240, 40, text=f"Money: {self.text}", fill="black")


class Towerbox:
    def __init__(
        self, frame: tk.Frame, infoboard: Infoboard, tower_map: tower.ITowerMap
    ):
        self.infoboard = infoboard
        self.tower_map = tower_map
        self.box = tk.Listbox(
            master=frame,
            selectmode="SINGLE",
            font=("times", 18),
            height=18,
            width=13,
            bg="gray",
            fg="dark blue",
            bd=1,
            highlightthickness=0,
        )
        self.selected: str = '<None>'
        self.box.insert(tk.END, "<None>")
        for i in tower.towers:
            self.box.insert(tk.END, i)
        for _ in range(50):
            self.box.insert(tk.END, "<None>")
        self.box.grid(row=1, column=1, rowspan=2)
        self.box.bind("<<ListboxSelect>>", self.onselect)

    @property
    def is_selected(self) -> bool:
        return self.selected != '<None>'

    def onselect(self, _):
        self.selected = str(self.box.get(self.box.curselection()))
        self.tower_map.displayed = None
        self.infoboard.displayGeneric(self.selected)


class Value(NamedTuple):
    coord: tuple[float, float]
    text: str


def create_texts(
    canvas: tk.Canvas,
    items: Iterable[tuple[Any, Value | None]],
    font: tuple[str, int],
    fill: str,
    anchor: _Anchor,
) -> None:
    for _, val in items:
        if val is None:
            continue
        canvas.create_text(
            val.coord, text=val.text, font=font, fill=fill, anchor=anchor
        )
