from aiogram import Router


def setup(parent_router: Router) -> None:
    from . import chat, private

    private.setup(parent_router)
    chat.setup(parent_router)
