from json import dumps
from random import choice
from re import findall
from typing import Optional

from aiogram import Router, Bot, F, types, flags
from aiogram.dispatcher import filters
from aiogram.dispatcher.fsm.context import FSMContext
from aiogram.utils.i18n import I18n, gettext as _

from worker import filters as f, keyboards as k
from worker.handlers import NO_ARGS
from worker.handlers.settings import BaseSettingsState
from worker.utils import markov

router = Router(name='settings_commands')
router.message.filter(f.AdminFilter(is_admin=True), state=BaseSettingsState.COMMAND)
router.callback_query.filter(k.SettingsData.filter(F.name == 'commands'))


@router.callback_query()
@flags.data('messages')
async def settings_commands_one_handler(
        query: types.CallbackQuery,
        state: FSMContext,
        bot: Bot,
        i18n: I18n,
        messages: Optional[list] = None,
        commands: Optional[dict] = None,
):
    if commands:
        commands = '\n'.join(map(lambda command: f'/{command[0]} - /{command[1]}', commands.items()))
    else:
        commands = _("missing.")

    args = markov.get_base_data(locale=choice(i18n.available_locales)).parsed_sentences

    if messages:
        args = messages + args

    await state.set_state(state=BaseSettingsState.COMMAND)

    await query.message.edit_text(
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

    await query.message.answer(_("Current custom commands:\n\n") + commands)


async def settings_commands_two_filter(message: types.Message, bot: Bot, i18n: I18n) -> bool:
    return await filters.Command(
        commands=[command.command for command in bot.commands[i18n.current_locale]],
        commands_ignore_case=True,
    )(message=message, bot=bot)


@router.message(settings_commands_two_filter)
async def settings_commands_two_handler(
        message: types.Message,
        bot: Bot,
        i18n: I18n,
        command: filters.CommandObject,
        state: FSMContext,
        commands: Optional[dict] = None):
    if command.args:
        if len(command.args.split()) == 1:
            if commands and command.args in commands.values():
                answer = _("The /{args} command is already in my database. Try another.").format(args=command.args)
            else:
                if commands:
                    commands[command.command] = command.args
                else:
                    commands = {command.command: command.args}

                await bot.sql.set_data(message.chat.id, 'commands', dumps(commands), state)
                await state.set_state(state=None)

                answer = _(
                    "<b>Command /{args} added successfully!</b>\n\n"
                    "Now in this chat you can write it instead of the /{command} command."
                ).format(command=command.command, args=command.args)

        else:
            answer = _("No, I can only record one custom command. You'll have to choose!")

        await message.answer(answer)

    else:
        args = markov.get_base_data(locale=choice(i18n.available_locales)).parsed_sentences
        messages = await bot.sql.get_data(message.chat.id, 'messages', state)

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
async def settings_commands_back_handler(message: types.Message, state: FSMContext):
    await state.clear()

    await message.answer(_("<b>Default command not recognized.</b>\n\n/settings - repeat the procedure."))
