"""Start up Game."""
# pylint: disable=wrong-import-position
import sys
import os
from pathlib import Path


def _config_path() -> None:
    _root = Path(__file__).resolve().parents[1]
    sys.path.insert(0, _root.as_posix())  # pylint: disable=no-member
    # Needed as image loading is on relative paths
    os.chdir(_root.joinpath('lib'))  # pylint: disable=no-member


_config_path()

from lib import tower_defense


def main() -> None:
    game = tower_defense.TowerDefenseGame()
    game.initialize()
    game.run()


if __name__ == "__main__":
    main()
