from aiogram import Router, types
from aiogram.utils.i18n import I18n, gettext as _

from . import commands_to_str
from .. import filters

router = Router(name='start')


def get_answer(i18n: I18n, ui_commands: dict[str, tuple[types.BotCommand]]):
    answer = _(
        "{name}, hello! Let's start with answering the obvious questions:\n"
        "- What am I? A text-generating bot based on current chat.\n"
        "- What can I do? Some things after which something happens...\n"
    )
    ui_commands = commands_to_str(ui_commands[i18n.current_locale][:3])
    return f'{answer}\n\n{ui_commands}'


@router.message(filters.CommandStart())
async def start_handler(message: types.Message, i18n: I18n, ui_commands: dict[str, tuple[types.BotCommand]]):
    await message.answer(get_answer(i18n, ui_commands).format(name=message.from_user))
