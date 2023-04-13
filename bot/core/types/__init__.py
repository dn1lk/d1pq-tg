import logging


def setup():
    logging.debug('Setting up types...')

    from . import chat, message, user
    chat.setup()
    message.setup()
    user.setup()
