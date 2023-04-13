from aiogram import Router, types
from aiogram.utils.i18n import gettext as _

from bot.core import filters
from . import CommandTypes

router = Router(name='start')


def get_answer():
    answer = _(
        "{name}, hello! Let's start with answering the obvious questions:\n"
        "- What am I? A text-generating bot based on current chat.\n"
        "- What can I do? Some things after which something happens...\n"
    )
    ui_commands = '\n'.join(str(command) for command in list(CommandTypes)[:3])
    return f'{answer}\n{ui_commands}'


@router.message(filters.CommandStart())
async def start_handler(message: types.Message):
    await message.answer(get_answer().format(name=message.from_user.mention_html()))
