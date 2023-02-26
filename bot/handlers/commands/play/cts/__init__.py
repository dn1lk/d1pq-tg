from aiogram import Router

from .misc.data import CTSData
from .misc.timer import task


def setup(parent_router: Router):
    from . import process, start
    parent_router.include_routers(
        process.router,
        start.router
    )
