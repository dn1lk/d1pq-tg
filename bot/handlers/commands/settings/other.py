from aiogram import Bot, F, Router, types

from core import filters
from handlers.commands import CommandTypes

from . import SettingsActions, keyboards
from .misc.helpers import get_start_content

router = Router(name="other")


@router.callback_query(keyboards.SettingsData.filter(F.action == SettingsActions.BACK))
async def back_handler(query: types.CallbackQuery, bot: Bot) -> None:
    assert isinstance(query.message, types.Message), "wrong message"

    content = await get_start_content(query.message, bot)
    await query.message.edit_text(**content)
    await query.answer()


@router.message(filters.Command(*CommandTypes.SETTINGS))
async def start_handler(message: types.Message, bot: Bot) -> None:
    content = await get_start_content(message, bot)
    await message.answer(**content)
