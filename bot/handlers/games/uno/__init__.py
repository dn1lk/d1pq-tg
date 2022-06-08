from aiogram import Router, F

from bot import keyboards as k


def setup():
    from bot.handlers.games import Game

    router = Router(name='game:uno')
    router.message.filter(Game.uno)
    router.callback_query.filter(k.GamesData.filter(F.game == 'uno'))

    from .user import router as action_rt
    from .core import router as start_rt

    sub_routers = (
        action_rt,
        start_rt,
    )

    for sub_router in sub_routers:
        router.include_router(sub_router)

    return router
