from aiogram import types
from aiogram.fsm.context import FSMContext
from aiogram.utils import formatting
from aiogram.utils.i18n import gettext as _

from handlers.commands.play.cts import CTSData


async def finish_game(message: types.Message, state: FSMContext, data_cts: CTSData, content: formatting.Text) -> None:
    await state.clear()

    _cities = len(data_cts.used_cities)
    content = formatting.Text(content, "\n", formatting.Bold(_("Cities guessed: {cities}.").format(cities=_cities)))
    await message.reply(**content.as_kwargs())
