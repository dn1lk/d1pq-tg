from aiogram import Router


def setup():
    router = Router(name='game:uno')

    from .. import Game

    router.message.filter(Game.uno)
    router.poll_answer.filter(Game.uno)

    from .middleware import UnoFSMContextMiddleware

    router.inline_query.outer_middleware(UnoFSMContextMiddleware())
    router.poll_answer.outer_middleware(UnoFSMContextMiddleware())

    from .user import router as user_rt
    from .core import router as core_rt

    sub_routers = (
        user_rt,
        core_rt,
    )

    for sub_router in sub_routers:
        router.include_router(sub_router)

    return router
