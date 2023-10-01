from aiogram import Router
from aiogram.utils.i18n import lazy_gettext as __

from core.middlewares import DestinySetMiddleware
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


router = Router(name='play')
DestinySetMiddleware().setup(router)


def setup(parent_router: Router):
    parent_router.include_router(router)

    from . import cts, rnd, rps, uno, other

    rps.setup(router)
    uno.setup(router)
    rnd.setup(router)
    cts.setup(router)

    router.include_router(other.router)
