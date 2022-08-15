
from typing import Tuple

import numpy as np # type: ignore

import color

# Tile graphics structured type compatible with Console.tiles_rgb.
graphic_dt = np.dtype(
    [
        ("ch", np.int32), # Unicode codepoint.
        ("fg", "3B"), # 3 unsigned bytes, for RGB colors.
        ("bg", "3B"),
    ]
)

# Tile struct used for statically defined tile data.
tile_dt = np.dtype(
    [
        ("walkable", np.bool), # True if this tile can be walked over.
        ("transparent", np.bool), # True if this tile doesn't block FOV.
        ("dark", graphic_dt), # Graphics for when this tile is not in FOV.
        ("light", graphic_dt), # Graphics for when this tile is in FOV.
    ]
)

def new_tile(
    *, # Enforce the use of keywords, so that parameter order doesn't matter.
    walkable: int,
    transparent: int,
    dark: Tuple[int, Tuple[int, int, int], Tuple[int, int, int]],
    light: Tuple[int, Tuple[int, int, int], Tuple[int, int, int]],
    ) -> np.ndarray:
    """
    Helper function for defining individual tile types
    """
    return np.array((walkable, transparent, dark, light), dtype=tile_dt)

# SHROUD represents unexplored, unseen tiles.
SHROUD = np.array((ord(" "), color.white, color.black), dtype=graphic_dt)

floor = new_tile(
    walkable=True,
    transparent=True,
    dark=(ord(" "), color.white, (0x32, 0x32, 0x96)),
    light=(ord(" "), color.white, (0xC8, 0xB4, 0x32)),
)

wall = new_tile(
    walkable=False,
    transparent=False,
    dark=(ord(" "), color.white, (0x0, 0x0, 0x64)),
   light=(ord(" "), color.white, (0x82, 0x6E, 0x32)),
)

