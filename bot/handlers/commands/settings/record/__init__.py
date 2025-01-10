from aiogram import Router

from .misc import keyboards
from .misc.actions import RecordActions

__all__ = (
    "RecordActions",
    "keyboards",
)


def setup(parent_router: Router) -> None:
    from . import start, update

    parent_router.include_routers(
        update.router,
        start.router,
    )
