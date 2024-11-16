from aiogram import Dispatcher

from .gpt import client as gpt_client

__all__ = ("gpt_client",)


async def setup(dispatcher: Dispatcher) -> None:
    await gpt_client.setup()
    dispatcher.shutdown.register(gpt_client.close)
