import asyncio
import secrets

from aiogram import types
from aiogram.fsm.context import FSMContext
from aiogram.utils import formatting

from handlers.commands.play import CLOSE


async def task(message: types.Message, state: FSMContext) -> None:
    try:
        await asyncio.sleep(secrets.randbelow(80) + 40)

        content = formatting.Text(str(secrets.choice(CLOSE)))
        await message.reply(**content.as_kwargs())
    finally:
        await state.clear()
