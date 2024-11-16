from aiogram import Router

from .misc.data import CTSData
from .misc.filter import CTSFilter
from .misc.timer import task

__all__ = (
    "CTSData",
    "CTSFilter",
    "task",
)


def setup(parent_router: Router) -> None:
    from . import process, start

    parent_router.include_routers(
        process.router,
        start.router,
    )
