import asyncio
import secrets

from aiogram import types
from aiogram.fsm.context import FSMContext
from aiogram.utils import formatting
from aiogram.utils.i18n import gettext as _

from handlers.commands.play import WINNER


async def task(message: types.Message, state: FSMContext) -> None:
    await asyncio.sleep(secrets.randbelow(30) + 40)

    content = formatting.Text(_("Time is over."), " ", secrets.choice(WINNER))
    await message.answer(**content.as_kwargs())
    await state.clear()
