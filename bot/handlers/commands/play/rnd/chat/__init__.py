from aiogram import Router


def setup(parent_router: Router) -> None:
    from . import process, start

    parent_router.include_routers(
        process.router,
        start.router,
    )
