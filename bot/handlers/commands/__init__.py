from aiogram import Router

from .misc.types import CommandTypes

__all__ = ("CommandTypes",)

router = Router(name="commands")


def setup(parent_router: Router):
    parent_router.include_router(router)

    from . import play, settings

    settings.setup(router)
    play.setup(router)

    from . import choose, help, start, who

    router.include_routers(
        choose.router,
        who.router,
        help.router,
        start.router,
    )
