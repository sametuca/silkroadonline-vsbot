"""Explicit hunt-loop states.

A single long tick() function that "just knows" what to do next gets hard
to extend (loot support, buffing, death confirmation all tangled
together). Making the states explicit keeps each concern isolated and
makes the log output legible - you can see exactly which phase the bot
was in when something went wrong.
"""

from enum import Enum, auto


class State(Enum):
    SCANNING = auto()       # looking for a monster candidate in the hunt region
    CONFIRMING = auto()     # clicked a candidate, verifying it actually became our target
    ATTACKING = auto()      # target confirmed, pressing skill keys
    AWAITING_DEATH = auto()  # watching the HP bar (or a timeout) for the target to die
    LOOTING = auto()        # brief pause/loot-key press after a kill
