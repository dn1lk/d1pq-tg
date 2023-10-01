from aiogram import Router


def setup(parent_router: Router):
    from . import start, update

    parent_router.include_routers(
        update.router,
        start.router,
    )
