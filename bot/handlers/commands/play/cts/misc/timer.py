import asyncio
from random import randint, choice

from aiogram import types
from aiogram.fsm.context import FSMContext
from aiogram.utils.i18n import gettext as _

from ... import WINNER


async def task(message: types.Message, state: FSMContext):
    await asyncio.sleep(randint(40, 70))

    answer_one = _("Time is over.")
    answer_two = choice(WINNER)
    await message.answer(f"{answer_one} {answer_two}")

    await state.clear()
