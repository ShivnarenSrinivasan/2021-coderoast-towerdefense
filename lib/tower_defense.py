from __future__ import annotations
import random
from collections.abc import Sequence
from functools import cached_property

import tkinter as tk

from . import (
    buttons,
    block,
    display,
    grid,
    maps,
    monster,
    mouse,
    tower,
)
from .block import Block
from .grid import Grid
from .maps import Dimension
from .monster import IMonster
from .tower import ITowerMap

from .game import Game, GameState, Stats

pathList = []


class TowerDefenseGame(Game):
    def __init__(
        self,
        title: str = "Tower Defense",
        grid_dim: Dimension = Dimension(30),
        block_dim: Dimension = Dimension(20),
        map_name: str = 'LeoMap',
        stats: Stats = Stats(1000, 100),
    ):
        """Create Tower Defense game.

        grid_dim: the height and width of the array of blocks
        block_dim: pixels width of each block
        """
        size = maps.size(grid_dim, block_dim)
        super().__init__(title, size, size)
        self.grid_dim = grid_dim
        self.block_dim = block_dim
        self.state = GameState.IDLE
        self.stats = stats

        self.displayboard = display.Displayboard(self.frame, self.stats)
        tower_map = tower.TowerMap()
        infoboard = display.Infoboard(self.frame, tower_map)  # type: ignore
        self.towerbox = display.Towerbox(self.frame, infoboard, tower_map)  # type: ignore
        self.grid = self._load_grid(map_name)
        self.monsters: list[IMonster] = []

        self._add_objects(
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

    def _update(self) -> None:
        super()._update()
        self.displayboard.update(self.stats)

        for monster_ in self.monsters:
            monster_.update()
            if monster.is_dead(monster_):
                self.monsters.remove(monster_)
                self.monsters.extend(monster_.children)
                self.stats.money += monster_.value
            if monster_.got_through:
                self.stats.health -= monster_.damage

    def _paint(self) -> None:
        super()._paint()

        for monster_ in monster.sort_distance(self.monsters):
            monster_.paint(self.canvas)

        self.displayboard.paint(
            'blue' if self.is_idle and len(self.monsters) == 0 else 'red'
        )

    def set_state(self, state: GameState) -> None:
        self.state = state


class Wavegenerator:
    def __init__(self, game: TowerDefenseGame):
        self._game = game
        self._current_wave: Sequence[int]
        self._curr_monster = 0
        self._direction = None
        self._gridx = 0
        self._gridy = 0
        self._spawn = self._findSpawn()
        self._decideMove()
        self._ticks = 1
        self._max_ticks = 2
        self._wave_file = open("texts/waveTexts/WaveGenerator2.txt", "r")

    def _getWave(self) -> None:
        self._game.set_state(GameState.SPAWNING)
        self._curr_monster = 1
        wave_line = self._wave_file.readline()
        if len(wave_line) == 0:
            return
        self._current_wave = tuple(map(int, wave_line.split()))
        self._max_ticks = self._current_wave[0]

    def _findSpawn(self) -> grid.Loc:
        for x in range(self._game.grid_dim):
            if block.is_path(self._game.grid[x][0]):
                self._gridx = x
                spawnx = x * self._game.block_dim + self._game.block_dim / 2
                spawny = 0
                return grid.Loc(spawnx, spawny)

        for y in range(self._game.grid_dim):
            if block.is_path(self._game.grid[0][y]):
                self._gridy = y
                spawnx = 0
                spawny = y * self._game.block_dim + self._game.block_dim / 2  # type: ignore
                return grid.Loc(spawnx, spawny)

        raise ValueError('Some invalid config of blocks')

    def _move(self):
        pathList.append(self._direction)
        if self._direction == 1:
            self._gridx += 1
        if self._direction == 2:
            self._gridx -= 1
        if self._direction == 3:
            self._gridy += 1
        if self._direction == 4:
            self._gridy -= 1
        self._decideMove()

    def _decideMove(self):
        if (
            self._direction != 2
            and self._gridx < self._game.grid_dim - 1
            and self._gridy >= 0
            and self._gridy <= self._game.grid_dim - 1
        ):
            if block.is_path(self._game.grid[self._gridx + 1][self._gridy]):
                self._direction = 1
                self._move()
                return

        if (
            self._direction != 1
            and self._gridx > 0
            and self._gridy >= 0
            and self._gridy <= self._game.grid_dim - 1
        ):
            if block.is_path(self._game.grid[self._gridx - 1][self._gridy]):
                self._direction = 2
                self._move()
                return

        if (
            self._direction != 4
            and self._gridy < self._game.grid_dim - 1
            and self._gridx >= 0
            and self._gridx <= self._game.grid_dim - 1
        ):
            if block.is_path(self._game.grid[self._gridx][self._gridy + 1]):
                self._direction = 3
                self._move()
                return

        if (
            self._direction != 3
            and self._gridy > 0
            and self._gridx >= 0
            and self._gridx <= self._game.grid_dim - 1
        ):
            if block.is_path(self._game.grid[self._gridx][self._gridy - 1]):
                self._direction = 4
                self._move()
                return

        pathList.append(5)

    def _spawnMonster(self):
        monster_idx = self._current_wave[self._curr_monster]

        self._game.monsters.append(
            monster_factory(monster_idx, self._spawn, self._game.block_dim)
        )
        self._curr_monster = self._curr_monster + 1

    def update(self):
        if self._game.state == GameState.WAIT_FOR_SPAWN:
            self._getWave()
        elif self._game.state == GameState.SPAWNING:
            if self._curr_monster == len(self._current_wave):
                self._game.set_state(GameState.IDLE)
                return
            self._ticks = self._ticks + 1
            if self._ticks == self._max_ticks:
                self._ticks = 0
                self._spawnMonster()

    def paint(self, canvas: tk.Canvas):
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
        self._x = 0
        self._y = 0
        self._gridx = 0
        self._gridy = 0
        self._xoffset = 0
        self._yoffset = 0
        self._pressed = False

        game.root.bind("<Button-1>", self._clicked)
        game.root.bind("<ButtonRelease-1>", self._released)
        game.root.bind("<Motion>", self._motion)

        self._image = mouse.load_img('HoveringCanPress')
        self.canNotPressImage = mouse.load_img('HoveringCanNotPress')

    def _clicked(self, _):
        self._pressed = True  # sets a variable
        self._image = mouse.load_img('Pressed')

    def _released(self, _):
        self._pressed = False
        self._image = mouse.load_img('HoveringCanPress')

    def _motion(self, event):
        if event.widget == self.game.canvas:
            self._xoffset = 0
            self._yoffset = 0
        elif event.widget == self.infoboard.canvas:
            self._xoffset = self.game.size
            self._yoffset = 0
        elif event.widget == self.game.towerbox.box:
            self._xoffset = self.game.size
            self._yoffset = 174
        elif event.widget == self.game.displayboard.canvas:
            self._yoffset = self.game.size
            self._xoffset = 0
        self._x = event.x + self._xoffset  # sets the "Mouse" x to the real mouse's x
        self._y = event.y + self._yoffset  # sets the "Mouse" y to the real mouse's y
        if self._x < 0:
            self._x = 0
        if self._y < 0:
            self._y = 0
        self._gridx = int(
            (self._x - (self._x % self.game.block_dim)) / self.game.block_dim
        )
        self._gridy = int(
            (self._y - (self._y % self.game.block_dim)) / self.game.block_dim
        )

    def update(self) -> None:
        if self._in_grid() and self._pressed:
            self._in_update()
        else:
            self._out_update()

    def _in_grid(self) -> bool:
        return (
            self._gridx >= 0
            and self._gridx <= self.game.grid_dim - 1
            and self._gridy >= 0
            and self._gridy <= self.game.grid_dim - 1
        )

    def _in_update(self) -> None:
        tower_map = self.infoboard.tower_map
        block_ = self.game.grid[self._gridx][self._gridy]
        if block_.grid_loc in tower_map:
            if not self.towerbox.is_selected:
                tower_map.select(block_.grid_loc)
                self.infoboard.displaySpecific()
        else:
            if self.towerbox.is_selected and can_add_tower(
                block_, self.towerbox.selected, self.game.stats.money
            ):
                self.game.stats.money -= add_tower(
                    tower_map,
                    block_,
                    self.towerbox.selected,
                    self.game.block_dim,
                    self.game.monsters,
                )

    def _out_update(self) -> None:
        pos = grid.Point(self._x - self._xoffset, self._y - self._yoffset)
        btn = self.game.displayboard.nextWaveButton
        if all(
            [
                self._pressed,
                buttons.is_within_bounds(btn, pos),
                can_spawn(self.game, self.game.monsters),
            ]
        ):
            self.game.set_state(GameState.WAIT_FOR_SPAWN)
        if self._pressed:
            self.game.stats.money += self.infoboard.buttonsCheck(
                pos, self.game.stats.money
            )

    def paint(self, canvas: tk.Canvas) -> None:
        if not self._in_grid():
            return None

        block_ = self.game.grid[self._gridx][self._gridy]
        img = self._image if block.is_empty(block_) else self.canNotPressImage
        canvas.create_image(
            self._gridx * self.game.block_dim,
            self._gridy * self.game.block_dim,
            image=img,
            anchor=tk.NW,
        )


def select_tower(tower_map: ITowerMap, grid_: grid.Point) -> None:
    tower_ = tower_map[grid_]
    tower_map.displayed = tower_


# TODO: Pass tower instance as param to both, instead of string.
def can_add_tower(block_: Block, tower_: str, money: int) -> bool:
    return all([block.is_empty(block_), can_buy_tower(money, tower_)])


def can_buy_tower(money_: int, tower_: str) -> bool:
    return money_ >= tower.cost(tower_)


def add_tower(
    tower_map: ITowerMap,
    block_: Block,
    tower_: str,
    block_dim: Dimension,
    monsters: list[IMonster],
) -> int:
    tower_map[block_.grid_loc] = tower.tower_factory(
        tower_, block_.loc, block_.grid_loc, block_dim, monsters
    )
    return tower.cost(tower_)


class Monster:
    def __init__(self, distance: float, spawn: grid.Loc, block_dim: Dimension):
        self.health: int
        self._max_health: int
        self.speed: float
        self.movement: float
        self.tick = 0
        self.maxTick = 1
        self._block_dim = block_dim
        self.distance_travelled = max(distance, 0.0)
        self._spawn = spawn
        self.x, self.y = self._compute_position()
        self.value = 0
        self._image = monster.load_img(self)
        self.axis: int | float
        self.children: list[IMonster] = []
        self.got_through: bool = False
        self.damage: int = 1

    def update(self):
        if monster.is_dead(self):
            self._die()
        self._move()

    def _move(self):
        if self.tick >= self.maxTick:
            self.distance_travelled += self.movement
            self.x, self.y = self._compute_position()
            self.movement = self.speed
            self.tick = 0
            self.maxTick = 1
        self.tick += 1

    # TODO: Optimize this section, as recomputing each time
    def _compute_position(self) -> grid.Loc:
        dist = self.distance_travelled
        b_dim = self._block_dim
        x = self._spawn.x
        y = self._spawn.y + b_dim / 2
        blocks = int((dist - (dist % b_dim)) / b_dim)
        if blocks != 0:
            for i in range(blocks):
                if pathList[i] == 1:
                    x += b_dim
                elif pathList[i] == 2:
                    x -= b_dim
                elif pathList[i] == 3:
                    y += b_dim
                else:
                    y -= b_dim
        if dist % b_dim != 0:
            if pathList[blocks] == 1:
                x += dist % b_dim
            elif pathList[blocks] == 2:
                x -= dist % b_dim
            elif pathList[blocks] == 3:
                y += dist % b_dim
            else:
                y -= dist % b_dim
        if pathList[blocks] == 5:
            self.health = 0
            self.got_through = True

        return grid.Loc(x, y)

    def _die(self):
        ...

    @property
    def _spawn_children_loc(self) -> float:
        return self.distance_travelled + self._block_dim * (0.5 - random.random())

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
            self.x - self.axis + (self.axis * 2 - 2) * self.health / self._max_health,
            self.y - self.axis - 2,
            fill="green",
            outline="green",
        )
        canvas.create_image(self.x, self.y, image=self._image, anchor=tk.CENTER)


class Monster1(Monster):
    def __init__(self, distance: float, spawn: grid.Loc, block_dim: Dimension):
        super().__init__(distance, spawn, block_dim)
        self._max_health = 30
        self.health = self._max_health
        self.value = 5
        self.speed = float(block_dim) / 2
        self.movement = block_dim / 3
        self.axis = block_dim / 2


class Monster2(Monster):
    def __init__(self, distance: float, spawn: grid.Loc, block_dim: Dimension):
        super().__init__(distance, spawn, block_dim)
        self._max_health = 50
        self.health = self._max_health
        self.value = 10
        self.speed = block_dim / 4
        self.movement = block_dim / 4
        self.axis = block_dim / 2

    def _die(self):
        self.children = [
            Monster1(self._spawn_children_loc, self._spawn, self._block_dim)
        ]


class AlexMonster(Monster):
    def __init__(self, distance: float, spawn: grid.Loc, block_dim: Dimension):
        super().__init__(distance, spawn, block_dim)
        self._max_health = 500
        self.health = self._max_health
        self.value = 100
        self.speed = block_dim / 5
        self.movement = block_dim / 5
        self.axis = block_dim

    def _die(self):
        self.children = [
            Monster2(self._spawn_children_loc, self._spawn, self._block_dim)
            for _ in range(5)
        ]


class BenMonster(Monster):
    def __init__(self, distance: float, spawn: grid.Loc, block_dim: Dimension):
        super().__init__(distance, spawn, block_dim)
        self._max_health = 200
        self.health = self._max_health
        self.value = 30
        self.speed = block_dim / 4
        self.movement = block_dim / 4
        self.axis = block_dim / 2

    def _die(self):
        self.children = [
            LeoMonster(self._spawn_children_loc, self._spawn, self._block_dim)
            for _ in range(2)
        ]


class LeoMonster(Monster):
    def __init__(self, distance: float, spawn: grid.Loc, block_dim: Dimension):
        super().__init__(distance, spawn, block_dim)
        self._max_health = 20
        self.health = self._max_health
        self.value = 2
        self.speed = block_dim / 2
        self.movement = block_dim / 2
        self.axis = block_dim / 4


class MonsterBig(Monster):
    def __init__(self, distance: float, spawn: grid.Loc, block_dim: Dimension):
        super().__init__(distance, spawn, block_dim)
        self._max_health = 1000
        self.health = self._max_health
        self.value = 10
        self.speed = block_dim / 6
        self.movement = block_dim / 6
        self.axis = 3 * block_dim / 2


def monster_factory(idx: int, spawn: grid.Loc, block_dim: Dimension) -> Monster:
    monsters_ = (
        Monster1,
        Monster2,
        AlexMonster,
        BenMonster,
        LeoMonster,
        MonsterBig,
    )
    monster_ = monsters_[idx](0.0, spawn, block_dim)
    return monster_
