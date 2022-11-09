from aiogram import Dispatcher


async def setup(dp: Dispatcher):
    from . import database
    dp['pool_db'] = await database.setup()

    from . import balaboba
    dp['yalm'] = await balaboba.Yalm.setup()
