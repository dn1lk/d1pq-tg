from aiogram import Router, types
from aiogram.utils.i18n import gettext as _

from core import filters
from . import CommandTypes

router = Router(name='start')


def get_answer(subject: types.User | types.Chat):
    answer = _(
        "{subject}, hello! Let's start with answering the obvious questions:\n"
        "- What am I? A text-generating bot based on current chat.\n"
        "- What can I do? Some things after which something happens...\n"
    ).format(subject=subject.mention_html())

    ui_commands = '\n'.join(str(command) for command in CommandTypes.start_commands)
    return f'{answer}\n{ui_commands}'


@router.message(filters.CommandStart())
async def start_handler(message: types.Message):
    answer = get_answer(message.from_user)
    await message.answer(answer)
