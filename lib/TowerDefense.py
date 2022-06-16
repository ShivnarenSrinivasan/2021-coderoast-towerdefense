from __future__ import annotations
import math
import random
from enum import Enum, auto
import tkinter as tk
from PIL import Image, ImageTk

import buttons
import block
import display
import grid
import maps
import tower
from game import Game

gridSize = 30  # the height and width of the array of blocks
blockSize = 20  # pixels wide of each block
mapSize = gridSize * blockSize

blockGrid: list[list[block.Block]] = []

blockDictionary = ["NormalBlock", "PathBlock", "WaterBlock"]
towerDictionary = {
    "Arrow Shooter": "ArrowShooterTower",
    "Bullet Shooter": "BulletShooterTower",
    "Tack Tower": "TackTower",
    "Power Tower": "PowerTower",
}

tower_map: dict[grid.Point, tower.Tower] = {}
pathList = []
spawnx = 0
spawny = 0
monsters: list[Monster] = []


def gen_monsters_list(monsters: list[Monster]) -> list[list[Monster]]:

    monstersByHealth = sorted(monsters, key=lambda x: x.health, reverse=True)
    monstersByHealthReversed = sorted(monsters, key=lambda x: x.health, reverse=False)
    return [
        monstersByHealth,
        monstersByHealthReversed,
        _sort_distance(monsters),
        _sort_distance(monsters, reverse=True),
    ]


def _sort_distance(monsters: list[Monster], reverse: bool = False) -> list[Monster]:
    return sorted(monsters, key=lambda x: x.distanceTravelled, reverse=reverse)


projectiles: list[Projectile] = []
health = 100
money = 5000000000
selectedTower = "<None>"
displayTower = None


class TowerDefenseGameState(Enum):
    IDLE = auto()
    WAIT_FOR_SPAWN = auto()
    SPAWNING = auto()


class TowerDefenseGame(Game):
    def __init__(
        self, title: str = "Tower Defense", width: int = mapSize, height: int = mapSize
    ):
        super().__init__(title, width, height)
        self.state = TowerDefenseGameState.IDLE

    def initialize(self):
        self.displayboard = Displayboard(self)

        self.infoboard = Infoboard(self)

        self.towerbox = Towerbox(self)
        self._load_map()
        self.add_object(Mouse(self))
        self.add_object(Wavegenerator(self))

    def _load_map(self, map_name: str = 'LeoMap') -> None:
        _map = maps.Map(map_name)
        make_grid(map_name)
        self.add_object(_map)

    @property
    def is_idle(self) -> bool:
        return self.state is TowerDefenseGameState.IDLE

    def update(self):
        super().update()
        self.displayboard.update()
        for p in projectiles:
            p.update()

        for m in monsters:
            m.update()

        for _tower in tower_map.values():
            _tower.update()

    def paint(self):
        super().paint()

        for _tower in tower_map.values():
            _tower.paint(self.canvas)

        for monster in _sort_distance(monsters):
            monster.paint(self.canvas)

        for projectile in projectiles:
            projectile.paint(self.canvas)

        if displayTower:
            displayTower.paintSelect(self.canvas)
        self.displayboard.paint()

    def set_state(self, state: TowerDefenseGameState):
        self.state = state


def create_map(map_name: str, map_size: int) -> None:
    map_canvas = Image.new("RGBA", (map_size, map_size), (255, 255, 255, 255))
    make_grid(map_name)
    paint_map_canvas(blockGrid, map_canvas)
    map_canvas.save(maps.img_path(map_name))


def make_grid(map_name: str):
    grid_vals = maps.load_template(map_name)
    blockGrid.clear()

    def make_row(x: int) -> list[block.Block]:
        return [make_block(x, y) for y in range(gridSize)]

    def make_block(x: int, y: int) -> block.Block:
        block_num = grid_vals[gridSize * y + x]
        return block.factory(
            x * blockSize + blockSize / 2,
            y * blockSize + blockSize / 2,
            block_num,
            x,
            y,
        )

    for x in range(gridSize):
        blockGrid.append(make_row(x))


def paint_map_canvas(
    block_grid: list[list[block.Block]], map_canvas: Image.Image
) -> None:
    for _block in grid.grid_iter(block_grid):
        paint(_block, map_canvas)


class Wavegenerator:
    def __init__(self, game: TowerDefenseGame):
        self.game = game
        self.currentWave = []
        self.currentMonster = 0
        self.direction = None
        self.gridx = 0
        self.gridy = 0
        self.findSpawn()
        self.decideMove()
        self.ticks = 1
        self.maxTicks = 2
        self.waveFile = open("texts/waveTexts/WaveGenerator2.txt", "r")

    def getWave(self) -> None:
        self.game.set_state(TowerDefenseGameState.SPAWNING)
        self.currentMonster = 1
        wave_line = self.waveFile.readline()
        if len(wave_line) == 0:
            return
        self.currentWave = list(map(int, wave_line.split()))
        self.maxTicks = self.currentWave[0]

    def findSpawn(self):
        global spawnx
        global spawny
        for x in range(gridSize):
            if isinstance(blockGrid[x][0], block.PathBlock):
                self.gridx = x
                spawnx = x * blockSize + blockSize / 2
                spawny = 0
                return
        for y in range(gridSize):
            if isinstance(blockGrid[0][y], block.PathBlock):
                self.gridy = y
                spawnx = 0
                spawny = y * blockSize + blockSize / 2
                return

    def move(self):
        pathList.append(self.direction)
        if self.direction == 1:
            self.gridx += 1
        if self.direction == 2:
            self.gridx -= 1
        if self.direction == 3:
            self.gridy += 1
        if self.direction == 4:
            self.gridy -= 1
        self.decideMove()

    def decideMove(self):
        if (
            self.direction != 2
            and self.gridx < gridSize - 1
            and self.gridy >= 0
            and self.gridy <= gridSize - 1
        ):
            if isinstance(blockGrid[self.gridx + 1][self.gridy], block.PathBlock):
                self.direction = 1
                self.move()
                return

        if (
            self.direction != 1
            and self.gridx > 0
            and self.gridy >= 0
            and self.gridy <= gridSize - 1
        ):
            if isinstance(blockGrid[self.gridx - 1][self.gridy], block.PathBlock):
                self.direction = 2
                self.move()
                return

        if (
            self.direction != 4
            and self.gridy < gridSize - 1
            and self.gridx >= 0
            and self.gridx <= gridSize - 1
        ):
            if isinstance(blockGrid[self.gridx][self.gridy + 1], block.PathBlock):
                self.direction = 3
                self.move()
                return

        if (
            self.direction != 3
            and self.gridy > 0
            and self.gridx >= 0
            and self.gridx <= gridSize - 1
        ):
            if isinstance(blockGrid[self.gridx][self.gridy - 1], block.PathBlock):
                self.direction = 4
                self.move()
                return

        pathList.append(5)

    def spawnMonster(self):
        monster_idx = self.currentWave[self.currentMonster]

        monsters.append(monster_factory(monster_idx))
        self.currentMonster = self.currentMonster + 1

    def update(self):
        if self.game.state == TowerDefenseGameState.WAIT_FOR_SPAWN:
            self.getWave()
        elif self.game.state == TowerDefenseGameState.SPAWNING:
            if self.currentMonster == len(self.currentWave):
                self.game.set_state(TowerDefenseGameState.IDLE)
                return
            self.ticks = self.ticks + 1
            if self.ticks == self.maxTicks:
                self.ticks = 0
                self.spawnMonster()

    def paint(self, canvas):
        pass


class NextWaveButton:
    def __init__(self, game: TowerDefenseGame):
        self.game = game
        self.coord1 = grid.Point(450, 25)
        self.coord2 = grid.Point(550, 50)

    @property
    def can_spawn(self) -> bool:
        return self.game.is_idle and len(monsters) == 0

    def checkPress(self, click: bool, point: grid.Point):
        if not buttons.is_within_bounds(self, point):
            return
        if not click or not self.can_spawn:
            return
        self.game.set_state(TowerDefenseGameState.WAIT_FOR_SPAWN)

    def paint(self, canvas: tk.Canvas) -> None:
        color = 'blue' if self.game.is_idle and len(monsters) == 0 else 'red'
        canvas.create_rectangle(
            *self.coord1, *self.coord2, fill=color, outline=color
        )  # draws a rectangle where the pointer is
        canvas.create_text(500, 37, text="Next Wave")


class TargetButton(buttons.Button):
    def __init__(self, coord1: grid.Point, coord2: grid.Point, myType):
        super().__init__(coord1, coord2)
        self.type = myType

    def press(self):
        displayTower.targetList = self.type


class StickyButton(buttons.Button):
    def press(self):
        if displayTower.stickyTarget == False:
            displayTower.stickyTarget = True
        else:
            displayTower.stickyTarget = False


class SellButton(buttons.Button):
    def press(self):
        global displayTower
        if displayTower is None:
            raise TypeError('Display Tower should be of type <Tower>')
        displayTower.sold(tower_map)
        displayTower = None


class UpgradeButton(buttons.Button):
    def press(self):
        global money
        if money >= displayTower.upgradeCost:
            money -= displayTower.upgradeCost
            displayTower.upgrade()


class Infoboard:
    def __init__(self, game: TowerDefenseGame):
        self.canvas = tk.Canvas(
            master=game.frame, width=162, height=174, bg="gray", highlightthickness=0
        )
        self.canvas.grid(row=0, column=1)
        self.image = ImageTk.PhotoImage(Image.open("images/infoBoard.png"))
        self.canvas.create_image(0, 0, image=self.image, anchor=tk.NW)
        self.currentButtons: list[buttons.Button] = []

    def buttonsCheck(self, click: bool, point: grid.Point) -> None:
        if not click:
            return None

        for btn in self.currentButtons:
            if btn.can_press(point):
                btn.press()
                self.displaySpecific()
                return None

    def displaySpecific(self):
        self.canvas.delete(tk.ALL)  # clear the screen
        self.canvas.create_image(0, 0, image=self.image, anchor=tk.NW)
        self.currentButtons = []
        if displayTower == None:
            return

        self.towerImage = ImageTk.PhotoImage(
            Image.open(
                "images/towerImages/"
                + displayTower.__class__.__name__
                + "/"
                + str(displayTower.level)
                + ".png"
            )
        )
        self.canvas.create_text(80, 75, text=displayTower.name, font=("times", 20))
        self.canvas.create_image(5, 5, image=self.towerImage, anchor=tk.NW)

        if issubclass(displayTower.__class__, TargetingTower):
            p1 = buttons.make_coords(26, 30, 35, 39)

            self.currentButtons.append(TargetButton(*p1, 0))
            self.canvas.create_text(
                37, 28, text="> Health", font=("times", 12), fill="white", anchor=tk.NW
            )

            self.currentButtons.append(TargetButton(*p1, 1))
            self.canvas.create_text(
                37, 48, text="< Health", font=("times", 12), fill="white", anchor=tk.NW
            )

            self.currentButtons.append(
                TargetButton(*buttons.make_coords(92, 50, 101, 59), 2)
            )
            self.canvas.create_text(
                103,
                48,
                text="> Distance",
                font=("times", 12),
                fill="white",
                anchor=tk.NW,
            )

            self.currentButtons.append(
                TargetButton(*buttons.make_coords(92, 30, 101, 39), 3)
            )
            self.canvas.create_text(
                103,
                28,
                text="< Distance",
                font=("times", 12),
                fill="white",
                anchor=tk.NW,
            )

            self.currentButtons.append(
                StickyButton(*buttons.make_coords(10, 40, 19, 49))
            )
            self.currentButtons.append(
                SellButton(*buttons.make_coords(5, 145, 78, 168))
            )
            if displayTower.upgradeCost:
                self.currentButtons.append(
                    UpgradeButton(*buttons.make_coords(82, 145, 155, 168))
                )
                self.canvas.create_text(
                    120,
                    157,
                    text="Upgrade: " + str(displayTower.upgradeCost),
                    font=("times", 12),
                    fill="light green",
                    anchor=tk.CENTER,
                )

            self.canvas.create_text(
                28,
                146,
                text="Sell",
                font=("times", 22),
                fill="light green",
                anchor=tk.NW,
            )

            self.currentButtons[displayTower.targetList].paint(self.canvas)
            if displayTower.stickyTarget == True:
                self.currentButtons[4].paint(self.canvas)

    def displayGeneric(self):
        self.currentButtons = []
        if selectedTower == "<None>":
            self.text = None
            self.towerImage = None
        else:
            self.text = selectedTower + " cost: " + str(tower.cost(selectedTower))
            self.towerImage = ImageTk.PhotoImage(
                Image.open(
                    "images/towerImages/" + towerDictionary[selectedTower] + "/1.png"
                )
            )
        self.canvas.delete(tk.ALL)  # clear the screen
        self.canvas.create_image(0, 0, image=self.image, anchor=tk.NW)
        self.canvas.create_text(80, 75, text=self.text)
        self.canvas.create_image(5, 5, image=self.towerImage, anchor=tk.NW)


class Displayboard:
    def __init__(self, game: TowerDefenseGame):
        self.canvas = tk.Canvas(
            master=game.frame, width=600, height=80, bg="gray", highlightthickness=0
        )
        self.canvas.grid(row=2, column=0)
        self.healthbar = display.Healthbar(health)
        self.moneybar = display.Moneybar(money)
        self.nextWaveButton = NextWaveButton(game)
        self.paint()

    def update(self):
        self.healthbar.update(health)
        self.moneybar.update(money)

    def paint(self):
        self.canvas.delete(tk.ALL)  # clear the screen
        self.healthbar.paint(self.canvas)
        self.moneybar.paint(self.canvas)
        self.nextWaveButton.paint(self.canvas)


class Towerbox:
    def __init__(self, game: TowerDefenseGame):
        self.game = game
        self.box = tk.Listbox(
            master=game.frame,
            selectmode="SINGLE",
            font=("times", 18),
            height=18,
            width=13,
            bg="gray",
            fg="dark blue",
            bd=1,
            highlightthickness=0,
        )
        self.box.insert(tk.END, "<None>")
        for i in towerDictionary:
            self.box.insert(tk.END, i)
        for i in range(50):
            self.box.insert(tk.END, "<None>")
        self.box.grid(row=1, column=1, rowspan=2)
        self.box.bind("<<ListboxSelect>>", self.onselect)

    def onselect(self, event):
        global selectedTower
        global displayTower
        selectedTower = str(self.box.get(self.box.curselection()))
        displayTower = None
        self.game.infoboard.displayGeneric()


class Mouse:
    def __init__(self, game: TowerDefenseGame):
        self.game = game
        self.x = 0
        self.y = 0
        self.gridx = 0
        self.gridy = 0
        self.xoffset = 0
        self.yoffset = 0
        self.pressed = False

        game.root.bind("<Button-1>", self.clicked)
        game.root.bind("<ButtonRelease-1>", self.released)
        game.root.bind("<Motion>", self.motion)

        self.image = Image.open("images/mouseImages/HoveringCanPress.png")
        self.image = ImageTk.PhotoImage(self.image)
        self.canNotPressImage = Image.open("images/mouseImages/HoveringCanNotPress.png")
        self.canNotPressImage = ImageTk.PhotoImage(self.canNotPressImage)

    def clicked(self, event):
        self.pressed = True  # sets a variable
        self.image = Image.open("images/mouseImages/Pressed.png")
        self.image = ImageTk.PhotoImage(self.image)

    def released(self, event):
        self.pressed = False
        self.image = Image.open("images/mouseImages/HoveringCanPress.png")
        self.image = ImageTk.PhotoImage(self.image)

    def motion(self, event):
        if event.widget == self.game.canvas:
            self.xoffset = 0
            self.yoffset = 0
        elif event.widget == self.game.infoboard.canvas:
            self.xoffset = mapSize
            self.yoffset = 0
        elif event.widget == self.game.towerbox.box:
            self.xoffset = mapSize
            self.yoffset = 174
        elif event.widget == self.game.displayboard.canvas:
            self.yoffset = mapSize
            self.xoffset = 0
        self.x = event.x + self.xoffset  # sets the "Mouse" x to the real mouse's x
        self.y = event.y + self.yoffset  # sets the "Mouse" y to the real mouse's y
        if self.x < 0:
            self.x = 0
        if self.y < 0:
            self.y = 0
        self.gridx = int((self.x - (self.x % blockSize)) / blockSize)
        self.gridy = int((self.y - (self.y % blockSize)) / blockSize)

    def update(self) -> None:
        if self._in_grid():
            self._in_update()
        else:
            self._out_update()

    def _in_grid(self) -> bool:
        return (
            self.gridx >= 0
            and self.gridx <= gridSize - 1
            and self.gridy >= 0
            and self.gridy <= gridSize - 1
        )

    def _in_update(self) -> None:
        if not self.pressed:
            return None

        block = blockGrid[self.gridx][self.gridy]
        if block.grid_loc in tower_map:
            if not is_tower_selected():
                select_tower(block.grid_loc)
                self.game.infoboard.displaySpecific()
        else:
            if is_tower_selected() and can_add_tower(block, selectedTower):
                add_tower(block, selectedTower)

    def _out_update(self) -> None:
        pos = grid.Point(self.x - self.xoffset, self.y - self.yoffset)
        self.game.displayboard.nextWaveButton.checkPress(self.pressed, pos)
        self.game.infoboard.buttonsCheck(self.pressed, pos)

    def paint(self, canvas: tk.Canvas) -> None:
        if not self._in_grid():
            return None

        block = blockGrid[self.gridx][self.gridy]
        img = self.image if block.can_place else self.canNotPressImage
        canvas.create_image(
            self.gridx * blockSize,
            self.gridy * blockSize,
            image=img,
            anchor=tk.NW,
        )


class Projectile:
    def __init__(self, x, y, damage, speed):
        self.hit = False
        self.x = x
        self.y = y
        self.speed = blockSize / 2
        self.damage = damage
        self.speed = speed

    def update(self):
        if self.target and not self.target.alive:
            projectiles.remove(self)
            return
        if self.hit:
            self.gotMonster()
        self.move()
        self.checkHit()

    def gotMonster(self):
        self.target.health -= self.damage
        projectiles.remove(self)

    def paint(self, canvas: tk.Canvas):
        canvas.create_image(self.x, self.y, image=self.image)


class TrackingBullet(Projectile):
    def __init__(self, x, y, damage, speed, target):
        super().__init__(x, y, damage, speed)
        self.target = target
        self.image = Image.open("images/projectileImages/bullet.png")
        self.image = ImageTk.PhotoImage(self.image)

    def move(self):
        self.length = (
            (self.x - (self.target.x)) ** 2 + (self.y - (self.target.y)) ** 2
        ) ** 0.5
        if self.length <= 0:
            return
        self.x += self.speed * ((self.target.x) - self.x) / self.length
        self.y += self.speed * ((self.target.y) - self.y) / self.length

    def checkHit(self):
        if (
            self.speed ** 2
            > (self.x - (self.target.x)) ** 2 + (self.y - (self.target.y)) ** 2
        ):
            self.hit = True


class PowerShot(TrackingBullet):
    def __init__(self, x, y, damage, speed, target, slow):
        super(PowerShot, self).__init__(x, y, damage, speed, target)
        self.slow = slow
        self.image = Image.open("images/projectileImages/powerShot.png")
        self.image = ImageTk.PhotoImage(self.image)

    def gotMonster(self):
        self.target.health -= self.damage
        if self.target.movement > (self.target.speed) / self.slow:
            self.target.movement = (self.target.speed) / self.slow
        projectiles.remove(self)


class AngledProjectile(Projectile):
    def __init__(self, x, y, damage, speed, angle, givenRange):
        super(AngledProjectile, self).__init__(x, y, damage, speed)
        self.xChange = speed * math.cos(angle)
        self.yChange = speed * math.sin(-angle)
        self.range = givenRange
        self.image = Image.open("images/projectileImages/arrow.png")
        self.image = ImageTk.PhotoImage(self.image.rotate(math.degrees(angle)))
        self.target = None
        self.speed = speed
        self.distance = 0

    def checkHit(self):
        for monster in monsters:
            if (monster.x - self.x) ** 2 + (monster.y - self.y) ** 2 <= (
                blockSize
            ) ** 2:
                self.hit = True
                self.target = monster
                return

    def gotMonster(self):
        self.target.health -= self.damage
        self.target.tick = 0
        self.target.maxTick = 5
        projectiles.remove(self)

    def move(self):
        self.x += self.xChange
        self.y += self.yChange
        self.distance += self.speed
        if self.distance >= self.range:
            try:
                projectiles.remove(self)
            except ValueError:
                pass


class TargetingTower(tower.ShootingTower):
    def __init__(self, x, y, gridx, gridy):
        super(TargetingTower, self).__init__(x, y, gridx, gridy)
        self.target = None
        self.targetList = 0
        self.stickyTarget = False

    def prepareShot(self):
        monster_list = gen_monsters_list(monsters)[self.targetList]

        if self.ticks != 20 / self.bulletsPerSecond:
            self.ticks += 1

        if not self.stickyTarget:
            for monster in monster_list:
                if (self.range + blockSize / 2) ** 2 >= (self.x - monster.x) ** 2 + (
                    self.y - monster.y
                ) ** 2:
                    self.target = monster

        if self.target:
            if (
                self.target.alive
                and (self.range + blockSize / 2)
                >= ((self.x - self.target.x) ** 2 + (self.y - self.target.y) ** 2)
                ** 0.5
            ):
                if self.ticks >= 20 / self.bulletsPerSecond:
                    self.shoot()
                    self.ticks = 0
            else:
                self.target = None
        elif self.stickyTarget:
            for monster in monster_list:
                if (self.range + blockSize / 2) ** 2 >= (self.x - monster.x) ** 2 + (
                    self.y - monster.y
                ) ** 2:
                    self.target = monster


class ArrowShooterTower(TargetingTower):
    def __init__(self, x, y, gridx, gridy):
        super(ArrowShooterTower, self).__init__(x, y, gridx, gridy)
        self.name = "Arrow Shooter"
        self.infotext = "ArrowShooterTower at [" + str(gridx) + "," + str(gridy) + "]."
        self.range = blockSize * 10
        self.bulletsPerSecond = 1
        self.damage = 10
        self.speed = blockSize
        self.upgradeCost = 50

    def nextLevel(self):
        if self.level == 2:
            self.upgradeCost = 100
            self.range = blockSize * 11
            self.damage = 12
        elif self.level == 3:
            self.upgradeCost = None
            self.bulletsPerSecond = 2

    def shoot(self):
        self.angle = math.atan2(self.y - self.target.y, self.target.x - self.x)
        projectiles.append(
            AngledProjectile(
                self.x,
                self.y,
                self.damage,
                self.speed,
                self.angle,
                self.range + blockSize / 2,
            )
        )


class BulletShooterTower(TargetingTower):
    def __init__(self, x, y, gridx, gridy):
        super(BulletShooterTower, self).__init__(x, y, gridx, gridy)
        self.name = "Bullet Shooter"
        self.infotext = "BulletShooterTower at [" + str(gridx) + "," + str(gridy) + "]."
        self.range = blockSize * 6
        self.bulletsPerSecond = 4
        self.damage = 5
        self.speed = blockSize / 2

    def shoot(self):
        projectiles.append(
            TrackingBullet(self.x, self.y, self.damage, self.speed, self.target)
        )

    def nextLevel(self) -> None:
        ...


class PowerTower(TargetingTower):
    def __init__(self, x, y, gridx, gridy):
        super(PowerTower, self).__init__(x, y, gridx, gridy)
        self.name = "Power Tower"
        self.infotext = "PowerTower at [" + str(gridx) + "," + str(gridy) + "]."
        self.range = blockSize * 8
        self.bulletsPerSecond = 10
        self.damage = 1
        self.speed = blockSize
        self.slow = 3

    def shoot(self):
        projectiles.append(
            PowerShot(self.x, self.y, self.damage, self.speed, self.target, self.slow)
        )

    def nextLevel(self) -> None:
        ...


class TackTower(TargetingTower):
    def __init__(self, x, y, gridx, gridy):
        super(TackTower, self).__init__(x, y, gridx, gridy)
        self.name = "Tack Tower"
        self.infotext = "TackTower at [" + str(gridx) + "," + str(gridy) + "]."
        self.range = blockSize * 5
        self.bulletsPerSecond = 1
        self.damage = 10
        self.speed = blockSize

    def shoot(self):
        for i in range(8):
            self.angle = math.radians(i * 45)
            projectiles.append(
                AngledProjectile(
                    self.x, self.y, self.damage, self.speed, self.angle, self.range
                )
            )

    def nextLevel(self) -> None:
        ...


def tower_factory(tower: str, loc: grid.Loc, grid: grid.Point) -> tower.Tower:
    towers = {
        "Arrow Shooter": ArrowShooterTower,
        "Bullet Shooter": BulletShooterTower,
        "Tack Tower": TackTower,
        "Power Tower": PowerTower,
    }
    _tower = towers[tower]
    return _tower(loc.x, loc.y, grid.x, grid.y)


def select_tower(_grid: grid.Point) -> None:
    _tower = tower_map[_grid]
    _tower.clicked = True
    global displayTower
    displayTower = _tower


def is_tower_selected() -> bool:
    return selectedTower != '<None>'


def can_add_tower(block: block.Block, _tower: str) -> bool:
    return all([block.can_place, can_buy_tower(money, _tower)])


def can_buy_tower(money: int, _tower: str) -> bool:
    return money >= tower.cost(_tower)


def add_tower(block: block.Block, _tower: str) -> None:
    global money
    tower_map[block.grid_loc] = tower_factory(_tower, block.loc, block.grid_loc)
    money -= tower.cost(_tower)


class Monster(object):
    def __init__(self, distance):
        self.alive = True
        self.image = None
        self.health = 0
        self.maxHealth = 0
        self.speed = 0.0
        self.movement = 0.0
        self.tick = 0
        self.maxTick = 1
        self.distanceTravelled = distance
        if self.distanceTravelled <= 0:
            self.distanceTravelled = 0
        self.x, self.y = self.positionFormula(self.distanceTravelled)
        self.armor = 0
        self.magicresist = 0
        self.value = 0
        self.image = Image.open(
            "images/monsterImages/" + self.__class__.__name__ + ".png"
        )
        self.image = ImageTk.PhotoImage(self.image)

    def update(self):
        if self.health <= 0:
            self.killed()
        self.move()

    def move(self):
        if self.tick >= self.maxTick:
            self.distanceTravelled += self.movement
            self.x, self.y = self.positionFormula(self.distanceTravelled)

            self.movement = self.speed
            self.tick = 0
            self.maxTick = 1
        self.tick += 1

    def positionFormula(self, distance):
        self.xPos = spawnx
        self.yPos = spawny + blockSize / 2
        self.blocks = int((distance - (distance % blockSize)) / blockSize)
        if self.blocks != 0:
            for i in range(self.blocks):
                if pathList[i] == 1:
                    self.xPos += blockSize
                elif pathList[i] == 2:
                    self.xPos -= blockSize
                elif pathList[i] == 3:
                    self.yPos += blockSize
                else:
                    self.yPos -= blockSize
        if distance % blockSize != 0:
            if pathList[self.blocks] == 1:
                self.xPos += distance % blockSize
            elif pathList[self.blocks] == 2:
                self.xPos -= distance % blockSize
            elif pathList[self.blocks] == 3:
                self.yPos += distance % blockSize
            else:
                self.yPos -= distance % blockSize
        if pathList[self.blocks] == 5:
            self.gotThrough()
        return self.xPos, self.yPos

    def killed(self):
        global money
        money += self.value
        self.die()

    def gotThrough(self):
        global health
        health -= 1
        self.die()

    def die(self):
        self.alive = False
        monsters.remove(self)

    def paint(self, canvas: tk.Canvas):
        canvas.create_rectangle(
            self.x - self.axis,
            self.y - 3 * self.axis / 2,
            self.x + self.axis - 1,
            self.y - self.axis - 1,
            fill="red",
            outline="black",
        )
        canvas.create_rectangle(
            self.x - self.axis + 1,
            self.y - 3 * self.axis / 2 + 1,
            self.x - self.axis + (self.axis * 2 - 2) * self.health / self.maxHealth,
            self.y - self.axis - 2,
            fill="green",
            outline="green",
        )
        canvas.create_image(self.x, self.y, image=self.image, anchor=tk.CENTER)


class Monster1(Monster):
    def __init__(self, distance):
        super(Monster1, self).__init__(distance)
        self.maxHealth = 30
        self.health = self.maxHealth
        self.value = 5
        self.speed = float(blockSize) / 2
        self.movement = blockSize / 3
        self.axis = blockSize / 2


class Monster2(Monster):
    def __init__(self, distance):
        super(Monster2, self).__init__(distance)
        self.maxHealth = 50
        self.health = self.maxHealth
        self.value = 10
        self.speed = float(blockSize) / 4
        self.movement = float(blockSize) / 4
        self.axis = blockSize / 2

    def killed(self):
        global money
        money += self.value
        monsters.append(
            Monster1(self.distanceTravelled + blockSize * (0.5 - random.random()))
        )
        self.die()


class AlexMonster(Monster):
    def __init__(self, distance):
        super(AlexMonster, self).__init__(distance)
        self.maxHealth = 500
        self.health = self.maxHealth
        self.value = 100
        self.speed = float(blockSize) / 5
        self.movement = float(blockSize) / 5
        self.axis = blockSize

    def killed(self):
        global money
        money += self.value
        for i in range(5):
            monsters.append(
                Monster2(self.distanceTravelled + blockSize * (0.5 - random.random()))
            )
        self.die()


class BenMonster(Monster):
    def __init__(self, distance):
        super(BenMonster, self).__init__(distance)
        self.maxHealth = 200
        self.health = self.maxHealth
        self.value = 30
        self.speed = float(blockSize) / 4
        self.movement = float(blockSize) / 4
        self.axis = blockSize / 2

    def killed(self):
        global money
        money += self.value
        for i in range(2):
            monsters.append(
                LeoMonster(self.distanceTravelled + blockSize * (0.5 - random.random()))
            )
        self.die()


class LeoMonster(Monster):
    def __init__(self, distance):
        super(LeoMonster, self).__init__(distance)
        self.maxHealth = 20
        self.health = self.maxHealth
        self.value = 2
        self.speed = float(blockSize) / 2
        self.movement = float(blockSize) / 2
        self.axis = blockSize / 4


class MonsterBig(Monster):
    def __init__(self, distance):
        super(MonsterBig, self).__init__(distance)
        self.maxHealth = 1000
        self.health = self.maxHealth
        self.value = 10
        self.speed = float(blockSize) / 6
        self.movement = float(blockSize) / 6
        self.axis = 3 * blockSize / 2


def monster_factory(idx: int) -> Monster:
    monsters = (
        Monster1,
        Monster2,
        AlexMonster,
        BenMonster,
        LeoMonster,
        MonsterBig,
    )
    monster = monsters[idx](0)
    return monster


def paint(
    _block: block.Block, img_canvas: Image.Image, axis: float = blockSize / 2
) -> None:
    image = Image.open("images/blockImages/" + _block.__class__.__name__ + ".png")
    offset = (int(_block.loc.x - axis), int(_block.loc.y - axis))
    img_canvas.paste(image, offset)
