import logging

from aiogram import Router

from .misc.text_workers import resolve_text, messages_to_words


def setup(parent_router: Router):
    logging.debug('Setting up handlers...')

    from . import commands, transitions

    commands.setup(parent_router)
    transitions.setup(parent_router)

    from . import error, other
    parent_router.include_routers(
        error.router,
        other.router,
    )
