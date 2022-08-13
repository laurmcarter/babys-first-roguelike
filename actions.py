
from __future__ import annotations

from typing import Optional, Tuple, TYPE_CHECKING

import color
import exceptions

if TYPE_CHECKING:
    from engine import Engine
    from entity import Actor, Entity

class Action:
    def perform(self) -> bool:
        """
        Return whether the game's turn advances.
        """
        raise NotImplementedError()

class ExitAction(Action):
    def perform(self) -> bool:
        raise SystemExit()

class InGameAction(Action):
    def __init__(self, entity: Entity):
        super().__init__()

        self.entity = entity

    @property
    def engine(self) -> Engine:
        """
        Return the engine this action belongs to.
        """
        return self.entity.game_map.engine

class WaitAction(InGameAction):
    def perform(self) -> bool:
        return True

class ActionWithDirection(InGameAction):
    def __init__(
        self,
        entity: Actor,
        dx: int,
        dy: int,
    ):
        super().__init__(entity)

        self.dx = dx
        self.dy = dy

    @property
    def dest_xy(self) -> Tuple[int, int]:
        """
        Returns this action's destination.
        """
        return self.entity.x + self.dx, self.entity.y + self.dy

    @property
    def blocking_entity(self) -> Optional[Entity]:
        """
        Returns the blocking entity at this action's destination, if any.
        """
        return self.engine.game_map.get_blocking_entity_at_location(*self.dest_xy)

    @property
    def target_actor(self) -> Optional[Actor]:
        """
        Returns the actor at this action's destination.
        """
        return self.engine.game_map.get_actor_at_location(*self.dest_xy)

class MeleeAction(ActionWithDirection):
    def perform(self) -> bool:
        target = self.target_actor

        if target is None:
            raise exceptions.Impossible("No entity to attack.") 

        damage = self.entity.fighter.power - target.fighter.defense

        attack_desc = f"{self.entity.name.capitalize()} attacks {target.name}"
        if self.entity is self.engine.player:
            attack_color = color.player_atk
        else:
            attack_color = color.enemy_atk

        if damage > 0:
            self.engine.message_log.add_message(
                f"{attack_desc} for {damage} hit points.",
                attack_color,
            )
            target.fighter.hp -= damage
        else:
            self.engine.message_log.add_message(
                f"{attack_desc} but does no damage.",
                attack_color,
            )
        return True # Advance turn.

class MovementAction(ActionWithDirection):
    def perform(self) -> bool:
        dest_x, dest_y = self.dest_xy

        if not self.engine.game_map.in_bounds(dest_x, dest_y):
            return  # Destination is out of bounds.
        if not self.engine.game_map.tiles["walkable"][dest_x, dest_y]:
            return  # Destination is blocked by a tile.
        if self.blocking_entity:
            return  # Destination is blocked by an entity.

        self.entity.move(self.dx, self.dy)
        return True # Advance turn.

class BumpAction(ActionWithDirection):
    def perform(self) -> bool:
        if self.target_actor:
            return MeleeAction(self.entity, self.dx, self.dy).perform()
        else:
            return MovementAction(self.entity, self.dx, self.dy).perform()

