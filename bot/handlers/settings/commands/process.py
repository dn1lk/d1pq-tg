from random import choice

from aiogram import Router, Bot, F, types, flags, filters, html
from aiogram.filters import MagicData
from aiogram.fsm.context import FSMContext
from aiogram.utils.i18n import I18n, gettext as _

from bot import filters as f
from bot.utils.database.context import DataBaseContext
from . import get_args
from .. import Settings
from ... import NO_ARGS


router = Router(name='settings:commands:process')


async def process_filter(message: types.Message, bot: Bot, commands: dict[str, types.BotCommand]):
    return await filters.Command(*commands['en'])(message, bot)

router.message.filter(
    Settings.command,
    process_filter,
    f.AdminFilter(is_admin=True),
)


@router.message(MagicData(F.command.args.regexp(r'\w+')))
async def setup_handler(
        message: types.Message,
        command: filters.CommandObject,
        db: DataBaseContext,
        state: FSMContext,
        custom_commands: dict
):
    if len(command.args.split()) == 1:
        if not custom_commands:
            custom_commands = {}

        if command.args in custom_commands.values():
            answer = _("{prefix}{custom_command} is already in my database. Try another.").format(
                prefix=command.prefix,
                custom_command=command.args,
            )
        else:
            custom_commands[command.command] = command.args

            await state.set_state()
            await db.set_data(commands=custom_commands)

            answer = _(
                "<b>{prefix}{custom_command} added successfully!</b>\n\n"
                "Now in this chat you can write it instead of {prefix}{command}."
            ).format(
                prefix=command.prefix,
                command=command.command,
                custom_command=command.args,
            )

    else:
        answer = _("No, I can record only one custom command. You'll have to choose!")

    await message.answer(answer)


@router.message()
@flags.throttling('gen')
async def decline_handler(
        message: types.Message,
        command: filters.CommandObject,
        i18n: I18n,
        messages: list | None,
):
    message = await message.answer(html.bold(_("Custom command not recognized.")))
    await message.answer(NO_ARGS.format(command=command.command, args=choice(get_args(i18n, messages))).lower())
