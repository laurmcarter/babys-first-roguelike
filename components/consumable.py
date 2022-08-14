
from __future__ import annotations

from typing import Optional, TYPE_CHECKING

from actions import (
    Action,
    ItemAction,
)
import color
from components.inventory import Inventory
from components.base_component import BaseComponent
from exceptions import Impossible

if TYPE_CHECKING:
    from entity import Actor, Item

class Consumable(BaseComponent):
    entity: Item

    def get_action(self, consumer: Actor) -> Optional[Action]:
        """
        Try to return the action for this item.
        """
        return ItemAction(consumer, self.entity)

    def activate(self, action: ItemAction) -> None:
        """
        Invoke this item's ability.

        `action` is the context for this activation.
        """
        raise NotImplementedError()

    def consume(self) -> None:
        """
        Remove the consumed item from its containing inventory.
        """
        entity = self.entity
        inventory = entity.parent
        if isinstance(inventory, Inventory):
            inventory.items.remove(entity)

class HealingConsumable(Consumable):
    def __init__(self, amount: int):
        self.amount = amount

    def activate(self, action: ItemAction) -> None:
        consumer = action.entity
        amount_recovered = consumer.fighter.heal(self.amount)

        if amount_recovered > 0:
            self.engine.message_log.add_message(
                f"You consume the {self.entity.name}, and recover {amount_recovered} HP!",
                color.health_recovered,
            )
            self.consume()
        else:
            raise Impossible("Your health is already full.")

