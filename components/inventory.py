
from __future__ import annotations

from typing import List, TYPE_CHECKING

from components.base_component import BaseComponent

if TYPE_CHECKING:
    from entity import Actor, Item

class Inventory(BaseComponent):
    entity: Actor

    def __init__(self, capacity: int):
        self.capacity = capacity
        self.items: List[Item] = []

    def drop(self, item: Item) -> None:
        """
        Removes an item from the inventory and restores it to the game map, at the entity's current location.
        """
        self.items.remove(item)
        item.place(self.entity.x, self.entity.y, self.game_map)

        if self.entity is self.engine.player:
            self.engine.message_log.add_message(f"You dropped the {item.name}.")

