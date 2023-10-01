import logging

from . import chat, message, user

__all__ = (
    "setup",
)

logger = logging.getLogger('bot')


def setup():
    logger.debug('Setting up types...')

    chat.setup()
    message.setup()
    user.setup()
