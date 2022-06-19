from aiogram import Router

from bot import config


def get_cities(locale: str) -> list:
    with open(config.BASE_DIR / 'locales' / locale / 'cities.txt', 'r', encoding='utf8') as f:
        return f.read().splitlines()


def setup():
    router = Router(name='game:cts')

    from .. import Game

    router.message.filter(Game.cts)

    from .core import router as core_rt

    sub_routers = (
        core_rt,
    )

    for sub_router in sub_routers:
        router.include_router(sub_router)

    return router
