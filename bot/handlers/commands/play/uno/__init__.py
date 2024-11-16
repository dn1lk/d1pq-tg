from aiogram import Router
from aiogram.utils.i18n import lazy_gettext as __

MAX_PLAYERS = 10
MIN_PLAYERS = 2

DRAW_CARD = __("Take a card.")
UNO = "UNO!"


def setup(parent_router: Router) -> None:
    from . import inline, process, settings, start, transitions, user

    parent_router.include_routers(
        user.router,
        inline.router,
        settings.router,
        process.router,
        start.router,
        transitions.router,
    )
