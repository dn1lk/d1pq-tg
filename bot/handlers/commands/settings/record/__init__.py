from aiogram import Router

from .misc import keyboards
from .misc.actions import RecordActions


def setup(parent_router: Router):
    from . import start, update

    parent_router.include_routers(
        update.router,
        start.router,
    )
