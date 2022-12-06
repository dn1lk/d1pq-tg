from aiogram import Dispatcher

from .wiki import Wikipedia

wiki = Wikipedia()


async def setup(dp: Dispatcher):
    from . import database
    dp['pool_db'] = await database.setup()
