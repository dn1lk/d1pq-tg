import asyncio

from aiogram import types
from aiogram.fsm.context import FSMContext
from aiogram.utils.i18n import gettext as _

from handlers.commands.misc.types import PREFIX, CommandTypes


async def idle_task(message: types.Message, state: FSMContext, action: str):
    await asyncio.sleep(60)
    await state.clear()

    answer = _(
        "<b>Something you think for a long time.</b>\n"
        "When you decide with {action}, write {command} again."
    ).format(action=action, command=f'{PREFIX}{CommandTypes.SETTINGS[0]}')

    await message.reply(answer)
