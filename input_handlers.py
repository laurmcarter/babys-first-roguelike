
from __future__ import annotations

from typing import Optional, TYPE_CHECKING

import tcod.event

from actions import (
    Action,
    ExitAction,
    BumpAction,
    DropAction,
    PickupAction,
    WaitAction,
)
import color
import exceptions

if TYPE_CHECKING:
    from engine import Engine

MOVE_KEYS = { # {{{
    # Arrow keys.
    tcod.event.K_UP:        (0, -1),
    tcod.event.K_DOWN:      (0,  1),
    tcod.event.K_LEFT:     (-1,  0),
    tcod.event.K_RIGHT:     (1,  0),
    tcod.event.K_HOME:     (-1, -1),
    tcod.event.K_END:      (-1,  1),
    tcod.event.K_PAGEUP:    (1, -1),
    tcod.event.K_PAGEDOWN:  (1,  1),
    # Numpad keys.
    tcod.event.K_KP_1: (-1,  1),
    tcod.event.K_KP_2:  (0,  1),
    tcod.event.K_KP_3:  (1,  1),
    tcod.event.K_KP_4: (-1,  0),
    tcod.event.K_KP_6:  (1,  0),
    tcod.event.K_KP_7: (-1, -1),
    tcod.event.K_KP_8:  (0, -1),
    tcod.event.K_KP_9:  (1, -1),
    # Vi keys.
    tcod.event.K_h: (-1,  0),
    tcod.event.K_j:  (0,  1),
    tcod.event.K_k:  (0, -1),
    tcod.event.K_l:  (1,  0),
    tcod.event.K_y: (-1, -1),
    tcod.event.K_u:  (1, -1),
    tcod.event.K_b: (-1,  1),
    tcod.event.K_n:  (1,  1),
} # }}}
WAIT_KEYS = { # {{{
    tcod.event.K_PERIOD,
    tcod.event.K_KP_5,
    tcod.event.K_CLEAR,
} # }}}

class EventHandler(tcod.event.EventDispatch[Action]): # {{{
    def __init__(self, engine: Engine):
        self.engine = engine

    def handle_events(
        self,
        event: tcod.event.Event,
    ) -> None:
        action = self.dispatch(event)

        self.handle_action(action)

    def handle_action(self, action: Optional[Action]) -> None:
        """
        Handle actions returned from event methods.

        Returns True if the action will advance a turn.
        """
        advance_turn = False

        if action:
            try:
                advance_turn = action.perform()
            except exceptions.Impossible as exc:
                self.engine.message_log.add_message(
                    exc.args[0],
                    color.impossible
                )

        if advance_turn:
            self.engine.handle_enemy_turns()

            self.engine.update_fov()

    def ev_mousemotion(
        self,
        event: tcod.event.MouseMotion,
    ) -> None:
        if self.engine.game_map.in_bounds(event.tile.x, event.tile.y):
            self.engine.mouse_location = event.tile.x, event.tile.y

    def ev_quit(self, event: tcod.event.Quit) -> Optional[Action]:
        return ExitAction()

    def on_render(self, console: tcod.Console) -> None:
        self.engine.render(console)

# }}}

MODIFIER_KEYS = { # {{{
    tcod.event.K_LSHIFT,
    tcod.event.K_RSHIFT,
    tcod.event.K_LCTRL,
    tcod.event.K_RCTRL,
    tcod.event.K_LALT,
    tcod.event.K_RALT,
}

# }}}

class AskUserEventHandler(EventHandler): # {{{
    """
    Handles user input for actions which require special input.
    """

    def handle_action(self, action: Optional[Action]) -> bool:
        """
        Return to the main event handler when a valid action was performed.
        """
        if super().handle_action(action):
            self.engine.event_handler = MainGameEventHandler(self.engine)
            return True
        return False

    def ev_keydown(self, event: tcod.event.KeyDown) -> Optional[Action]:
        """
        By default, any key exits this input handler.
        """
        if event.sym in MODIFIER_KEYS:
            return None
        return self.on_exit()

    def ev_mousebuttondown(
        self,
        event: tcod.event.MouseButtonDown,
    ) -> Optional[Action]:
        """
        By default, any mouse click exits this input handler.
        """
        return self.on_exit()

    def on_exit(self) -> Optional[Action]:
        """
        Called when the user is trying to exit or cancel an action.

        By default, this returns to the main event handler.
        """
        self.engine.event_handler = MainGameEventHandler(self.engine)
        return None

# }}}

class InventoryEventHandler(AskUserEventHandler): # {{{
    """
    This handler lets the user select an item.

    What happens then depends on the subclass.
    """

    TITLE = "<missing title>"

    def on_render(self, console: tcod.Console) -> None:
        """
        Render an inventory menu, which displays the items in the inventory,
        and the letter to select them. Will move to a different position
        based on where the player is located, so the player can see
        where they are.
        """
        super().on_render(console)
        number_of_items_in_inventory = len(self.engine.player.inventory.items)

        height = number_of_items_in_inventory + 2
        width = len(self.TITLE) + 4

        if height <= 3:
            height = 3

        if self.engine.player.x <= 30:
            x = 40
        else:
            x = 0

        y = 0

        console.draw_frame(
            x=x,
            y=y,
            width=width,
            height=height,
            title=self.TITLE,
            clear=True,
            fg=color.white,
            bg=color.black,
        )

        if number_of_items_in_inventory > 0:
            for i, item in enumerate(self.engine.player.inventory.items):
                item_key = chr(ord("a") + i)
                console.print(x + 1, y + i + 1, f"({item_key}) {item.name}")
        else:
            console.print(x + 1, y + 1, "(Empty)")

    def ev_keydown(self, event: tcod.events.KeyDown) -> Optional[Action]:
        player = self.engine.player
        key = event.sym
        index = key - tcod.event.K_a

        if 0 <= index <= 26:
            try:
                selected_item = player.inventory.items[index]
            except IndexError:
                self.engine.message_log.add_message("Invalid entry.", color.invalid)
                return None
            return self.on_item_selected(selected_item)
        return super().ev_keydown(event)

    def on_item_selected(self, item: Item) -> Optional[Action]:
        """
        Called when the user selects a valid item.
        """
        raise NotImplementedError()

# }}}

class InventoryActivateHandler(InventoryEventHandler): # {{{
    """
    Handle using an inventory item.
    """

    TITLE = "Select an item to use."

    def on_item_selected(self, item: Item) -> Optional[Action]:
        """
        Return the action for the selected item.
        """
        self.engine.event_handler = MainGameEventHandler(self.engine)
        return item.consumable.get_action(self.engine.player)

# }}}

class InventoryDropHandler(InventoryEventHandler): # {{{
    """
    Handle dropping an inventory item.
    """

    TITLE = "Select an item to drop."

    def on_item_selected(self, item: Item) -> Optional[Action]:
        """
        Drop this item.
        """
        self.engine.event_handler = MainGameEventHandler(self.engine)
        return DropAction(self.engine.player, item)

# }}}

CURSOR_Y_KEYS = { # {{{
    tcod.event.K_UP: -1,
    tcod.event.K_DOWN: 1,
    tcod.event.K_PAGEUP: -10,
    tcod.event.K_PAGEDOWN: 10,
} # }}}

class HistoryViewer(EventHandler): # {{{
    """
    Print the history on a larger window which can be navigated.
    """

    def __init__(self, engine: Engine):
        super().__init__(engine)
        self.log_length = len(engine.message_log.messages)
        self.cursor = self.log_length - 1

    def on_render(self, console: tcod.Console) -> None:
        # Draw the main state as the background.
        super().on_render(console)

        log_console = tcod.Console(console.width - 6, console.height - 6)

        # Draw a frame with a custom banner title.
        log_console.draw_frame(
            x=0,
            y=0,
            width=log_console.width,
            height=log_console.height
        )
        log_console.print_box(
            x=0,
            y=0,
            width=log_console.width,
            height=1,
            string="┤Message history├",
            alignment=tcod.CENTER,
        )

        # Render the message log using the cursor parameter.
        self.engine.message_log.render_messages(
            console=log_console,
            x=1,
            y=1,
            width=log_console.width - 2,
            height=log_console.height - 2,
            messages=self.engine.message_log.messages[: self.cursor + 1],
        )
        log_console.blit(console, 3, 3)

    def ev_keydown(self, event: tcod.event.KeyDown) -> None:
        # Fancy conditional movement to make it feel right.
        if event.sym in CURSOR_Y_KEYS:
            adjust = CURSOR_Y_KEYS[event.sym]
            if adjust < 0 and self.cursor == 0:
                # Only move from the top to the bottom when already on the edge.
                self.cursor = self.log_length - 1
            elif adjust > 0 and self.cursor == self.log_length - 1:
                # Same with bottom to top movement.
                self.cursor = 0
            else: # Otherwise move while staying clamped to the bounds of the history log.
                self.cursor = max(0, min(self.cursor + adjust, self.log_length - 1))
        elif event.sym == tcod.event.K_HOME:
            # Move directly to the first message.
            self.cursor = 0
        elif event.sym == tcod.event.K_END:
            # Move directly to the last message.
            self.cursor = self.log_length - 1
        else: # Any other key moves back to the main game state.
            self.engine.event_handler = MainGameEventHandler(self.engine)

# }}}

class MainGameEventHandler(EventHandler): # {{{
    def ev_keydown(self, event: tcod.event.KeyDown) -> Optional[Action]:
        action: Optional[Action] = None

        key = event.sym

        player = self.engine.player

        if key in MOVE_KEYS:
            dx, dy = MOVE_KEYS[key]
            action = BumpAction(player, dx, dy)
        elif key in WAIT_KEYS:
            action = WaitAction(player)
        elif key == tcod.event.K_ESCAPE:
            action = ExitAction()
        elif key == tcod.event.K_v:
            self.engine.event_handler = HistoryViewer(self.engine)
        elif key == tcod.event.K_g:
            action = PickupAction(player)
        elif key == tcod.event.K_i:
            self.engine.event_handler = InventoryActivateHandler(self.engine)
        elif key == tcod.event.K_d:
            self.engine.event_handler = InventoryDropHandler(self.engine)

        return action

# }}}

class GameOverEventHandler(EventHandler): # {{{
    def ev_keydown(self, event: tcod.event.KeyDown) -> Optional[Action]:
        action: Optional[Action] = None

        key = event.sym

        if key == tcod.event.K_ESCAPE:
            action = ExitAction()

        # No valid key was pressed
        return action

# }}}

