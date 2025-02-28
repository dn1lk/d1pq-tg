from aiogram import Router

from .misc import keyboards
from .misc.values import RPSValues

__all__ = (
    "RPSValues",
    "keyboards",
)


def setup(parent_router: Router):
    from . import process, start

    parent_router.include_routers(
        process.router,
        start.router,
    )
