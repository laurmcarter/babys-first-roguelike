
from __future__ import annotations

from typing import TYPE_CHECKING

import color
from components.base_component import BaseComponent
from input_handlers import GameOverEventHandler
from render_order import RenderOrder
import utility

if TYPE_CHECKING:
    from entity import Actor

class Fighter(BaseComponent):
    entity: Actor

    def __init__(
        self,
        hp: int,
        defense: int,
        power: int,
    ):
        self.max_hp = hp
        self._hp = hp
        self.defense = defense
        self.power = power

    @property
    def hp(self) -> int:
        return self._hp

    @hp.setter
    def hp(self, value: int) -> None:
        self._hp = utility.clamp(value, lo=0, hi=self.max_hp)
        if self._hp == 0 and self.entity.ai:
            self.die()

    def die(self) -> None:
        if self.entity is self.engine.player:
            death_message = "You died!"
            death_message_color = color.player_die
            self.engine.event_handler = GameOverEventHandler(self.engine)
        else:
            death_message = f"{self.entity.name} is dead!"
            death_message_color = color.enemy_die

        self.entity.char = "%"
        self.entity.color = (191, 0, 0)
        self.entity.blocks_movement = False
        self.entity.ai = None
        self.entity.name = f"remains of {self.entity.name}"
        self.entity.render_order = RenderOrder.CORPSE

        self.engine.message_log.add_message(
            death_message,
            death_message_color,
        )

    def heal(self, amount: int) -> int:
        if self.hp == self.max_hp:
            return 0

        new_hp_value = min(self.hp + amount, self.max_hp)

        amount_recovered = new_hp_value - self.hp

        self.hp = new_hp_value

        return amount_recovered

    def take_damage(self, amount: int) -> None:
        self.hp -= amount

