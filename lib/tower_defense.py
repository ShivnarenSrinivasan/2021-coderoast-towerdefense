from __future__ import annotations
import math
import random
from enum import Enum, auto
from functools import cached_property
import tkinter as tk
from PIL import Image, ImageTk

from . import (
    buttons,
    block,
    display,
    grid,
    maps,
    monster,
    tower,
)
from .block import Block
from .maps import Dimension
from .monster import IMonster

from .game import Game

blockSize = Dimension(20)  # pixels wide of each block

tower_map: dict[grid.Point, tower.Tower] = {}
pathList = []
spawnx = 0
spawny = 0
monsters: list[IMonster] = []

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
        self,
        title: str = "Tower Defense",
        grid_dim: Dimension = Dimension(30),
        block_dim: Dimension = blockSize,
    ):
        """Create Tower Defense game.

        grid_dim: the height and width of the array of blocks
        """
        size = maps.size(grid_dim, block_dim)
        super().__init__(title, size, size)
        self.grid_dim = grid_dim
        self.block_dim = block_dim
        self.state = TowerDefenseGameState.IDLE
        self.grid: list[list[Block]]

    @cached_property
    def size(self) -> Dimension:
        return maps.size(self.grid_dim, self.block_dim)

    def initialize(self) -> None:
        self.displayboard = Displayboard(self)

        self.infoboard = Infoboard(self)

        self.towerbox = Towerbox(self)
        self.grid = self._load_map()
        self.add_object(Mouse(self))
        self.add_object(Wavegenerator(self))

    def _load_map(self, map_name: str = 'LeoMap') -> list[list[Block]]:
        _map = maps.Map(map_name)
        self.add_object(_map)
        return maps.make_grid(map_name, self.block_dim, self.grid_dim)

    @property
    def is_idle(self) -> bool:
        return self.state is TowerDefenseGameState.IDLE

    def update(self) -> None:
        super().update()
        self.displayboard.update()
        for p in projectiles:
            p.update()

        for monster_ in monsters:
            monster_.update()

        for tower_ in tower_map.values():
            tower_.update()

    def paint(self) -> None:
        super().paint()

        for tower_ in tower_map.values():
            tower_.paint(self.canvas)

        for monster_ in monster.sort_distance(monsters):
            monster_.paint(self.canvas)

        for projectile in projectiles:
            projectile.paint(self.canvas)

        if displayTower:
            displayTower.paintSelect(self.canvas)
        self.displayboard.paint()

    def set_state(self, state: TowerDefenseGameState) -> None:
        self.state = state


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
        for x in range(self.game.grid_dim):
            if block.is_path(self.game.grid[x][0]):
                self.gridx = x
                spawnx = x * self.game.block_dim + self.game.block_dim / 2
                spawny = 0
                return
        for y in range(self.game.grid_dim):
            if block.is_path(self.game.grid[0][y]):
                self.gridy = y
                spawnx = 0
                spawny = y * self.game.block_dim + self.game.block_dim / 2
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
            and self.gridx < self.game.grid_dim - 1
            and self.gridy >= 0
            and self.gridy <= self.game.grid_dim - 1
        ):
            if block.is_path(self.game.grid[self.gridx + 1][self.gridy]):
                self.direction = 1
                self.move()
                return

        if (
            self.direction != 1
            and self.gridx > 0
            and self.gridy >= 0
            and self.gridy <= self.game.grid_dim - 1
        ):
            if block.is_path(self.game.grid[self.gridx - 1][self.gridy]):
                self.direction = 2
                self.move()
                return

        if (
            self.direction != 4
            and self.gridy < self.game.grid_dim - 1
            and self.gridx >= 0
            and self.gridx <= self.game.grid_dim - 1
        ):
            if block.is_path(self.game.grid[self.gridx][self.gridy + 1]):
                self.direction = 3
                self.move()
                return

        if (
            self.direction != 3
            and self.gridy > 0
            and self.gridx >= 0
            and self.gridx <= self.game.grid_dim - 1
        ):
            if block.is_path(self.game.grid[self.gridx][self.gridy - 1]):
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

        self.towerImage = tower.load_img(displayTower)
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
            self.towerImage = tower.load_img(selectedTower)
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
        for i in tower.towers:
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
            self.xoffset = self.game.size
            self.yoffset = 0
        elif event.widget == self.game.towerbox.box:
            self.xoffset = self.game.size
            self.yoffset = 174
        elif event.widget == self.game.displayboard.canvas:
            self.yoffset = self.game.size
            self.xoffset = 0
        self.x = event.x + self.xoffset  # sets the "Mouse" x to the real mouse's x
        self.y = event.y + self.yoffset  # sets the "Mouse" y to the real mouse's y
        if self.x < 0:
            self.x = 0
        if self.y < 0:
            self.y = 0
        self.gridx = int(
            (self.x - (self.x % self.game.block_dim)) / self.game.block_dim
        )
        self.gridy = int(
            (self.y - (self.y % self.game.block_dim)) / self.game.block_dim
        )

    def update(self) -> None:
        if self._in_grid():
            self._in_update()
        else:
            self._out_update()

    def _in_grid(self) -> bool:
        return (
            self.gridx >= 0
            and self.gridx <= self.game.grid_dim - 1
            and self.gridy >= 0
            and self.gridy <= self.game.grid_dim - 1
        )

    def _in_update(self) -> None:
        if not self.pressed:
            return None

        block_ = self.game.grid[self.gridx][self.gridy]
        if block_.grid_loc in tower_map:
            if not is_tower_selected():
                select_tower(block_.grid_loc)
                self.game.infoboard.displaySpecific()
        else:
            if is_tower_selected() and can_add_tower(block_, selectedTower):
                add_tower(block_, selectedTower)

    def _out_update(self) -> None:
        pos = grid.Point(self.x - self.xoffset, self.y - self.yoffset)
        self.game.displayboard.nextWaveButton.checkPress(self.pressed, pos)
        self.game.infoboard.buttonsCheck(self.pressed, pos)

    def paint(self, canvas: tk.Canvas) -> None:
        if not self._in_grid():
            return None

        block_ = self.game.grid[self.gridx][self.gridy]
        img = self.image if block.is_empty(block_) else self.canNotPressImage
        canvas.create_image(
            self.gridx * self.game.block_dim,
            self.gridy * self.game.block_dim,
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
            self.speed**2
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
        for monster_ in monsters:
            if (monster_.x - self.x) ** 2 + (monster_.y - self.y) ** 2 <= (
                blockSize
            ) ** 2:
                self.hit = True
                self.target = monster_
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
        monster_list = monster.gen_list(monsters)[self.targetList]

        if self.ticks != 20 / self.bulletsPerSecond:
            self.ticks += 1

        if not self.stickyTarget:
            for monster_ in monster_list:
                if (self.range + blockSize / 2) ** 2 >= (self.x - monster_.x) ** 2 + (
                    self.y - monster_.y
                ) ** 2:
                    self.target = monster_

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
            for monster_ in monster_list:
                if (self.range + blockSize / 2) ** 2 >= (self.x - monster_.x) ** 2 + (
                    self.y - monster_.y
                ) ** 2:
                    self.target = monster_


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


def tower_factory(tower_: str, loc: grid.Loc, grid_: grid.Point) -> tower.Tower:
    towers = {
        "Arrow Shooter": ArrowShooterTower,
        "Bullet Shooter": BulletShooterTower,
        "Tack Tower": TackTower,
        "Power Tower": PowerTower,
    }
    tower_type = towers[tower_]
    return tower_type(loc.x, loc.y, grid_.x, grid_.y)


def select_tower(grid_: grid.Point) -> None:
    tower_ = tower_map[grid_]
    tower_.clicked = True
    global displayTower
    displayTower = tower_


def is_tower_selected() -> bool:
    return selectedTower != '<None>'


def can_add_tower(block_: Block, tower_: str) -> bool:
    return all([block.is_empty(block_), can_buy_tower(money, tower_)])


def can_buy_tower(money_: int, tower_: str) -> bool:
    return money_ >= tower.cost(tower_)


def add_tower(block_: Block, tower_: str) -> None:
    global money
    tower_map[block_.grid_loc] = tower_factory(tower_, block_.loc, block_.grid_loc)
    money -= tower.cost(tower_)


class Monster:
    def __init__(self, distance: float):
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
        self.image = monster.load_img(self)

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
        blocks = int((distance - (distance % blockSize)) / blockSize)
        if blocks != 0:
            for i in range(blocks):
                if pathList[i] == 1:
                    self.xPos += blockSize
                elif pathList[i] == 2:
                    self.xPos -= blockSize
                elif pathList[i] == 3:
                    self.yPos += blockSize
                else:
                    self.yPos -= blockSize
        if distance % blockSize != 0:
            if pathList[blocks] == 1:
                self.xPos += distance % blockSize
            elif pathList[blocks] == 2:
                self.xPos -= distance % blockSize
            elif pathList[blocks] == 3:
                self.yPos += distance % blockSize
            else:
                self.yPos -= distance % blockSize
        if pathList[blocks] == 5:
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
    monsters_ = (
        Monster1,
        Monster2,
        AlexMonster,
        BenMonster,
        LeoMonster,
        MonsterBig,
    )
    monster_ = monsters_[idx](0.0)
    return monster_
