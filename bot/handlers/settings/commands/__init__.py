from random import choice
from re import findall
from typing import Optional

from aiogram import Router, Bot, F, types, flags
from aiogram.dispatcher import filters
from aiogram.dispatcher.fsm.context import FSMContext
from aiogram.utils.i18n import I18n, gettext as _

from bot import filters as f, keyboards as k
from bot.utils import markov
from bot.utils.database.context import DataBaseContext

from .middleware import CustomCommandsMiddleware
from ... import NO_ARGS
from ...settings import Settings

router = Router(name='settings:commands')
router.message.filter(f.AdminFilter(is_admin=True), Settings.command)

router.message.outer_middleware(CustomCommandsMiddleware())
router.edited_message.outer_middleware(CustomCommandsMiddleware())

router.callback_query.outer_middleware(CustomCommandsMiddleware())


@router.callback_query(k.SettingsData.filter(F.name == 'commands'))
@flags.data('messages')
async def commands_handler(
        query: types.CallbackQuery,
        state: FSMContext,
        bot: Bot,
        i18n: I18n,
        messages: Optional[list] = None,
        custom_commands: Optional[dict] = None,
):
    await state.set_state(Settings.command)

    args = markov.get_base(locale=choice(i18n.available_locales)).parsed_sentences
    if messages:
        args = messages + args

    message = await query.message.edit_text(
        _(
            "<b>Tired of writing preset commands?</b>"
            "{no_args} - and I will answer this command."
        ).format(
            no_args=NO_ARGS.format(
                command=choice(bot.commands[i18n.current_locale]).command,
                args=choice(findall(r'\w+', str(args))).lower()
            )
        )
    )

    if custom_commands:
        custom_commands = '\n'.join(map(lambda command: f'/{command[0]} - /{command[1]}', custom_commands.items()))
    else:
        custom_commands = _("missing.")

    await message.answer(_("Current custom commands:\n\n") + custom_commands)


async def commands_setup_no_args_filter(
        message: types.Message,
        bot: Bot,
        command_magic: Optional[filters.CommandObject.args] = None
):
    return await filters.Command(
        commands=[command.command for command in bot.commands['en']],
        commands_ignore_case=True,
        command_magic=command_magic
    )(message, bot)


async def commands_setup_filter(message, bot):
    return await commands_setup_no_args_filter(message, bot, F.args)


@router.message(commands_setup_filter)
async def commands_setup_handler(
        message: types.Message,
        command: filters.CommandObject,
        db: DataBaseContext,
        state: FSMContext,
        custom_commands: Optional[dict] = None
):
    if len(command.args.split()) == 1:
        if not custom_commands:
            custom_commands = {}

        if command.args in custom_commands.values():
            answer = _("The /{args} command is already in my database. Try another.").format(args=command.args)
        else:
            custom_commands[command.command] = command.args

            await state.set_state()
            await db.set_data(commands=custom_commands)

            answer = _(
                "<b>Command /{args} added successfully!</b>\n\n"
                "Now in this chat you can write it instead of the /{command} command."
            ).format(command=command.command, args=command.args)

    else:
        answer = _("No, I can record only one custom command. You'll have to choose!")

    await message.answer(answer)


@router.message(commands_setup_no_args_filter)
@flags.data('messages')
async def commands_setup_no_args_handler(
        message: types.Message,
        command: filters.CommandObject,
        i18n: I18n,
        messages: Optional[list] = None,
):
    args = markov.get_base(locale=choice(i18n.available_locales)).parsed_sentences

    if messages:
        args = messages + args

    message = await message.answer(_("<b>Custom command not recognized.</b>"))
    await message.answer(
        NO_ARGS.format(
            command=command.command,
            args=choice(findall(r'\w+', str(args))).lower()
        )
    )


@router.message()
async def commands_back_handler(message: types.Message, state: FSMContext):
    await state.clear()

    await message.answer(_("<b>Default command not recognized.</b>\n\n/settings - repeat the procedure."))
