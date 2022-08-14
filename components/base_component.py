
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from engine import Engine
    from entity import Entity
    from game_map import GameMap

class BaseComponent:
    entity: Entity # Owning entity instance

    def __init__(self, entity: Entity):
        super().__init__()

        self.entity = entity

    @property
    def game_map(self) -> GameMap:
        return self.entity.game_map

    @property
    def engine(self) -> Engine:
        return self.game_map.engine

