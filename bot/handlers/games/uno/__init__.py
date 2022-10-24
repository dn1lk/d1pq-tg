from aiogram import Router, F
from aiogram.utils.i18n import lazy_gettext as __

from .. import Game, keyboards as k

DRAW_CARD = __("Take a card.")


def setup():
    router = Router(name='game:uno')
    router.message.filter(Game.uno)
    router.poll.filter(Game.uno)
    router.chat_member.filter(Game.uno)
    router.callback_query.filter(k.UnoGame.filter(F.game))

    from .process.middleware import UnoFSMContextMiddleware

    router.inline_query.outer_middleware(UnoFSMContextMiddleware())
    router.poll.outer_middleware(UnoFSMContextMiddleware())

    from .action import router as action_rt
    from .core import router as core_rt
    from .inline import router as inline_rt
    from .poll import router as poll_rt
    from .settings import router as settings_rt
    from .user import router as user_rt

    sub_routers = (
        user_rt,
        inline_rt,
        poll_rt,
        core_rt,
        settings_rt,
        action_rt,
    )

    for sub_router in sub_routers:
        router.include_router(sub_router)

    return router
