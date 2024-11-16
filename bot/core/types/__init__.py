import logging

from . import message

__all__ = ("setup",)

logger = logging.getLogger("bot")


def setup() -> None:
    logger.debug("setting up types...")

    message.setup()
