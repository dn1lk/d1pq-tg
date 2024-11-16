import logging

from aiogram import Router

logger = logging.getLogger("bot")


def setup(parent_router: Router) -> None:
    logger.debug("setting up handlers...")

    from . import commands, transitions

    commands.setup(parent_router)
    transitions.setup(parent_router)

    from . import error, other

    parent_router.include_routers(
        error.router,
        other.router,
    )
