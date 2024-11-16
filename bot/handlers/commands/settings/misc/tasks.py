import asyncio

from aiogram import types
from aiogram.fsm.context import FSMContext
from aiogram.utils import formatting
from aiogram.utils.i18n import gettext as _

from handlers.commands.misc.types import PREFIX, CommandTypes


async def idle_task(message: types.Message, state: FSMContext, action: str) -> None:
    await asyncio.sleep(60)
    await state.clear()

    _command = f"{PREFIX}{CommandTypes.SETTINGS[0]}"
    content = formatting.Text(
        formatting.Bold(_("Something you think for a long time.")),
        "\n",
        _("When you decide with {action}, write {command} again.").format(action=action, command=_command),
    )

    await message.reply(**content.as_kwargs())
