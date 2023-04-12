from aiogram import Router
from aiogram.utils.i18n import lazy_gettext as __

from .misc.actions import PlayActions
from .misc.data import PlayData
from .misc.states import PlayStates

WINNER = (
    __("Victory for me."),
    __("I am a winner."),
    __("I am the winner in this game."),
)

CLOSE = (
    __("You know I won't play with you! Maybe..."),
    __("Well don't play with me!"),
    __("I thought we were playing..."),
    __("It's too slow, I won't play with you!"),
)


def setup(parent_router: Router):
    from . import cts, rnd, rps, uno, other

    rps.setup(parent_router)
    uno.setup(parent_router)
    rnd.setup(parent_router)
    cts.setup(parent_router)

    parent_router.include_router(other.router)
