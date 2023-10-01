from aiogram import Router
from aiogram.utils.i18n import lazy_gettext as __

DRAW_CARD = __("Take a card.")
UNO = "UNO!"


def setup(parent_router: Router):
    from . import inline, process, settings, start, transitions, user
    parent_router.include_routers(
        user.router,
        inline.router,
        settings.router,
        process.router,
        start.router,
        transitions.router,
    )
