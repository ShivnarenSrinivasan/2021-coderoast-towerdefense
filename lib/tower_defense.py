from __future__ import annotations
from abc import ABC, abstractmethod
import math
import random
from collections.abc import Sequence
from functools import cached_property

import tkinter as tk
from PIL import ImageTk

from . import (
    buttons,
    block,
    display,
    grid,
    maps,
    monster,
    mouse,
    projectile,
    tower,
)
from .block import Block
from .grid import Grid
from .maps import Dimension
from .monster import IMonster
from .tower import ITowerMap

from .game import Game, GameState, Stats

blockSize = Dimension(20)  # pixels wide of each block

pathList = []
monsters: list[IMonster] = []

projectiles: list[Projectile] = []
health = 100


class TowerDefenseGame(Game):
    def __init__(
        self,
        title: str = "Tower Defense",
        grid_dim: Dimension = Dimension(30),
        block_dim: Dimension = blockSize,
        map_name: str = 'LeoMap',
    ):
        """Create Tower Defense game.

        grid_dim: the height and width of the array of blocks
        """
        size = maps.size(grid_dim, block_dim)
        super().__init__(title, size, size)
        self.grid_dim = grid_dim
        self.block_dim = block_dim
        self.state = GameState.IDLE
        self.stats = Stats(1000, 100)

        self.displayboard = display.Displayboard(self.frame, self.stats)
        tower_map = tower.TowerMap()
        infoboard = display.Infoboard(self.frame, tower_map)
        self.towerbox = display.Towerbox(self.frame, infoboard, tower_map)
        self.grid = self._load_grid(map_name)

        self.add_objects(
            [
                maps.Map(map_name),
                Wavegenerator(self),
                Mouse(self, infoboard, self.towerbox),
                tower_map,
            ]
        )

    @cached_property
    def size(self) -> Dimension:
        return maps.size(self.grid_dim, self.block_dim)

    def _load_grid(self, map_name: str) -> Grid[Block]:
        return maps.make_grid(map_name, self.block_dim, self.grid_dim)

    @property
    def is_idle(self) -> bool:
        return self.state is GameState.IDLE

    def update(self) -> None:
        super().update()
        self.displayboard.update(self.stats)
        for p in projectiles:
            p.update()

        for monster_ in monsters:
            monster_.update()

    def paint(self) -> None:
        super().paint()

        for monster_ in monster.sort_distance(monsters):
            monster_.paint(self.canvas)

        for projectile_ in projectiles:
            projectile_.paint(self.canvas)

        self.displayboard.paint(
            'blue' if self.is_idle and len(monsters) == 0 else 'red'
        )

    def set_state(self, state: GameState) -> None:
        self.state = state


class Wavegenerator:
    def __init__(self, game: TowerDefenseGame):
        self.game = game
        self.currentWave: Sequence[int]
        self.currentMonster = 0
        self.direction = None
        self.gridx = 0
        self.gridy = 0
        self.spawn = self.findSpawn()
        self.decideMove()
        self.ticks = 1
        self.maxTicks = 2
        self.waveFile = open("texts/waveTexts/WaveGenerator2.txt", "r")

    def getWave(self) -> None:
        self.game.set_state(GameState.SPAWNING)
        self.currentMonster = 1
        wave_line = self.waveFile.readline()
        if len(wave_line) == 0:
            return
        self.currentWave = tuple(map(int, wave_line.split()))
        self.maxTicks = self.currentWave[0]

    def findSpawn(self) -> grid.Loc:
        for x in range(self.game.grid_dim):
            if block.is_path(self.game.grid[x][0]):
                self.gridx = x
                spawnx = x * self.game.block_dim + self.game.block_dim / 2
                spawny = 0
                return grid.Loc(spawnx, spawny)

        for y in range(self.game.grid_dim):
            if block.is_path(self.game.grid[0][y]):
                self.gridy = y
                spawnx = 0
                spawny = y * self.game.block_dim + self.game.block_dim / 2
                return grid.Loc(spawnx, spawny)

        raise ValueError('Some invalid config of blocks')

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

        monsters.append(monster_factory(monster_idx, self.spawn))
        self.currentMonster = self.currentMonster + 1

    def update(self):
        if self.game.state == GameState.WAIT_FOR_SPAWN:
            self.getWave()
        elif self.game.state == GameState.SPAWNING:
            if self.currentMonster == len(self.currentWave):
                self.game.set_state(GameState.IDLE)
                return
            self.ticks = self.ticks + 1
            if self.ticks == self.maxTicks:
                self.ticks = 0
                self.spawnMonster()

    def paint(self, canvas):
        pass


def can_spawn(game: TowerDefenseGame, monsters_: Sequence[IMonster]) -> bool:
    return game.is_idle and len(monsters_) == 0


class Mouse:
    def __init__(
        self,
        game: TowerDefenseGame,
        infoboard: display.Infoboard,
        towerbox: display.Towerbox,
    ):
        self.game = game
        self.infoboard = infoboard
        self.towerbox = towerbox
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

        self.image = mouse.load_img('HoveringCanPress')
        self.canNotPressImage = mouse.load_img('HoveringCanNotPress')

    def clicked(self, _):
        self.pressed = True  # sets a variable
        self.image = mouse.load_img('Pressed')

    def released(self, _):
        self.pressed = False
        self.image = mouse.load_img('HoveringCanPress')

    def motion(self, event):
        if event.widget == self.game.canvas:
            self.xoffset = 0
            self.yoffset = 0
        elif event.widget == self.infoboard.canvas:
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
        if self._in_grid() and self.pressed:
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
        tower_map = self.infoboard.tower_map
        block_ = self.game.grid[self.gridx][self.gridy]
        if block_.grid_loc in tower_map:
            if not self.towerbox.is_selected:
                tower_map.select(block_.grid_loc)
                self.infoboard.displaySpecific()
        else:
            if self.towerbox.is_selected and can_add_tower(
                block_, self.towerbox.selected, self.game.stats.money
            ):
                self.game.stats.money -= add_tower(
                    tower_map, block_, self.towerbox.selected
                )

    def _out_update(self) -> None:
        pos = grid.Point(self.x - self.xoffset, self.y - self.yoffset)
        btn = self.game.displayboard.nextWaveButton
        if all(
            [
                self.pressed,
                buttons.is_within_bounds(btn, pos),
                can_spawn(self.game, monsters),
            ]
        ):
            self.game.set_state(GameState.WAIT_FOR_SPAWN)
        if self.pressed:
            self.game.stats.money -= self.infoboard.buttonsCheck(
                pos, self.game.stats.money
            )

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


class Projectile(ABC):
    def __init__(self, x, y, damage, speed):
        self.hit = False
        self.x = x
        self.y = y
        self.speed = blockSize / 2
        self.damage = damage
        self.speed = speed
        self.target: Monster
        self.image: ImageTk.PhotoImage

    def update(self) -> None:
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

    def paint(self, canvas: tk.Canvas) -> None:
        canvas.create_image(self.x, self.y, image=self.image)

    @abstractmethod
    def move(self) -> None:
        ...

    @abstractmethod
    def checkHit(self) -> None:
        ...


class TrackingBullet(Projectile):
    def __init__(self, x, y, damage, speed, target):
        super().__init__(x, y, damage, speed)
        self.target = target
        self.image = projectile.load_img('bullet')
        self.length: float

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
        self.image = projectile.load_img('powerShot')

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
        self.image = projectile.load_arrow_img(angle)
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
        assert self.bulletsPerSecond is not None
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

    @abstractmethod
    def shoot(self) -> None:
        ...


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
        self.angle: float

    def nextLevel(self):
        if self.level == 2:
            self.upgradeCost = 100
            self.range = blockSize * 11
            self.damage = 12
        elif self.level == 3:
            self.upgradeCost = None
            self.bulletsPerSecond = 2

    def shoot(self):
        assert self.target is not None
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
        self.angle: float

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


def select_tower(tower_map: ITowerMap, grid_: grid.Point) -> None:
    tower_ = tower_map[grid_]
    tower_.clicked = True
    tower_map.displayed = tower_


# TODO: Pass tower instance as param to both, instead of string.
def can_add_tower(block_: Block, tower_: str, money: int) -> bool:
    return all([block.is_empty(block_), can_buy_tower(money, tower_)])


def can_buy_tower(money_: int, tower_: str) -> bool:
    return money_ >= tower.cost(tower_)


def add_tower(tower_map: ITowerMap, block_: Block, tower_: str) -> int:
    tower_map[block_.grid_loc] = tower_factory(tower_, block_.loc, block_.grid_loc)
    return tower.cost(tower_)


class Monster:
    def __init__(self, distance: float, spawn: grid.Loc):
        self.alive = True
        self.image = None
        self.health = 0
        self.maxHealth = 0
        self.speed = 0.0
        self.movement = 0.0
        self.tick = 0
        self.maxTick = 1
        self.distanceTravelled = max(distance, 0.0)
        self.spawn = spawn
        self.x, self.y = self.positionFormula()
        self.armor = 0
        self.magicresist = 0
        self.value = 0
        self.image = monster.load_img(self)
        self.axis: int | float

    def update(self):
        if self.health <= 0:
            # TODO: Handle money increase when monsters killed
            self.killed()
        self.move()

    def move(self):
        if self.tick >= self.maxTick:
            self.distanceTravelled += self.movement
            self.x, self.y = self.positionFormula()
            self.movement = self.speed
            self.tick = 0
            self.maxTick = 1
        self.tick += 1

    def positionFormula(self) -> grid.Loc:
        dist = self.distanceTravelled
        x = self.spawn.x
        y = self.spawn.y + blockSize / 2
        blocks = int((dist - (dist % blockSize)) / blockSize)
        if blocks != 0:
            for i in range(blocks):
                if pathList[i] == 1:
                    x += blockSize
                elif pathList[i] == 2:
                    x -= blockSize
                elif pathList[i] == 3:
                    y += blockSize
                else:
                    y -= blockSize
        if dist % blockSize != 0:
            if pathList[blocks] == 1:
                x += dist % blockSize
            elif pathList[blocks] == 2:
                x -= dist % blockSize
            elif pathList[blocks] == 3:
                y += dist % blockSize
            else:
                y -= dist % blockSize
        if pathList[blocks] == 5:
            self.gotThrough()

        return grid.Loc(x, y)

    def killed(self):
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
    def __init__(self, distance: float, spawn: grid.Loc):
        super().__init__(distance, spawn)
        self.maxHealth = 30
        self.health = self.maxHealth
        self.value = 5
        self.speed = float(blockSize) / 2
        self.movement = blockSize / 3
        self.axis = blockSize / 2


class Monster2(Monster):
    def __init__(self, distance: float, spawn: grid.Loc):
        super().__init__(distance, spawn)
        self.maxHealth = 50
        self.health = self.maxHealth
        self.value = 10
        self.speed = float(blockSize) / 4
        self.movement = float(blockSize) / 4
        self.axis = blockSize / 2

    def killed(self):
        monsters.append(
            Monster1(
                self.distanceTravelled + blockSize * (0.5 - random.random()), self.spawn
            )
        )
        self.die()


class AlexMonster(Monster):
    def __init__(self, distance: float, spawn: grid.Loc):
        super().__init__(distance, spawn)
        self.maxHealth = 500
        self.health = self.maxHealth
        self.value = 100
        self.speed = float(blockSize) / 5
        self.movement = float(blockSize) / 5
        self.axis = blockSize

    def killed(self):
        for _ in range(5):
            monsters.append(
                Monster2(
                    self.distanceTravelled + blockSize * (0.5 - random.random()),
                    self.spawn,
                )
            )
        self.die()


class BenMonster(Monster):
    def __init__(self, distance: float, spawn: grid.Loc):
        super().__init__(distance, spawn)
        self.maxHealth = 200
        self.health = self.maxHealth
        self.value = 30
        self.speed = float(blockSize) / 4
        self.movement = float(blockSize) / 4
        self.axis = blockSize / 2

    def killed(self):
        for _ in range(2):
            monsters.append(
                LeoMonster(
                    self.distanceTravelled + blockSize * (0.5 - random.random()),
                    self.spawn,
                )
            )
        self.die()


class LeoMonster(Monster):
    def __init__(self, distance: float, spawn: grid.Loc):
        super().__init__(distance, spawn)
        self.maxHealth = 20
        self.health = self.maxHealth
        self.value = 2
        self.speed = float(blockSize) / 2
        self.movement = float(blockSize) / 2
        self.axis = blockSize / 4


class MonsterBig(Monster):
    def __init__(self, distance: float, spawn: grid.Loc):
        super().__init__(distance, spawn)
        self.maxHealth = 1000
        self.health = self.maxHealth
        self.value = 10
        self.speed = float(blockSize) / 6
        self.movement = float(blockSize) / 6
        self.axis = 3 * blockSize / 2


def monster_factory(idx: int, spawn: grid.Loc) -> Monster:
    monsters_ = (
        Monster1,
        Monster2,
        AlexMonster,
        BenMonster,
        LeoMonster,
        MonsterBig,
    )
    monster_ = monsters_[idx](0.0, spawn)
    return monster_
