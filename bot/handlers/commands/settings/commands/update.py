from random import choice

from aiogram import Router, F, types, flags, html
from aiogram.fsm.context import FSMContext
from aiogram.utils.i18n import I18n, gettext as _

from bot.core import filters
from bot.core.utils import database
from bot.handlers.commands import CommandTypes
from .. import SettingsStates

router = Router(name='commands:update')
router.message.filter(SettingsStates.commands,
                      filters.Command(*(command[0] for command in CommandTypes)),
                      filters.IsAdmin(is_admin=True))


@router.message(filters.MagicData(F.command.args.regexp(r'^\w{1,10}$')))
async def accept_handler(
        message: types.Message,
        db: database.SQLContext,
        state: FSMContext,
        commands: dict[str, str] | None,
        command: filters.CommandObject,
):
    if commands and command.args in commands.values():
        answer = _("{prefix}{custom_command} is already recorded. Try another.").format(
            prefix=command.prefix,
            custom_command=command.args,
        )
    else:
        if commands is None:
            commands = {command.command: command.args}
        else:
            commands[command.command] = command.args

        await state.set_state()
        await db.commands.set(message.chat.id, commands)

        answer = _(
            "<b>{prefix}{custom_command} added successfully!</b>\n\n"
            "Now in this chat you can write it instead of {prefix}{command}."
        ).format(
            prefix=command.prefix,
            command=command.command,
            custom_command=command.args,
        )

    await message.answer(answer)


@router.message()
@flags.throttling('gen')
@flags.sql('messages')
async def decline_handler(
        message: types.Message,
        i18n: I18n,
        command: filters.CommandObject,
        messages: list | None,
):
    message = await message.answer(html.bold(_("Custom command not recognized.")))

    from bot.handlers import messages_to_words
    from bot.handlers.commands.help import get_answer

    await message.answer(get_answer(command,
                                    choice(messages_to_words(i18n, messages)).lower()))
