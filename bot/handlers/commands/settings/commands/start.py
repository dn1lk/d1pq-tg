from random import choice

from aiogram import Router, F, types, flags
from aiogram.fsm.context import FSMContext
from aiogram.utils.i18n import I18n, gettext as _

from bot.core import filters
from bot.handlers.commands import CommandTypes
from .. import SettingsActions, SettingsStates, keyboards
from ...misc.types import PREFIX

router = Router(name='commands:start')
router.callback_query.filter(keyboards.SettingsData.filter(F.action == SettingsActions.COMMAND))


@router.callback_query()
@flags.sql(('messages', 'commands'))
async def start_handler(
        query: types.CallbackQuery,
        state: FSMContext,
        i18n: I18n,
        commands: dict[str, str] | None,
        messages: list[str] | None,
):
    await state.set_state(SettingsStates.commands)

    from bot.handlers import messages_to_words
    from bot.handlers.commands.help import get_answer

    command = filters.CommandObject(
        prefix=PREFIX,
        command=choice(list(CommandTypes))[0]
    )

    answer = _(
        "<b>Tired of writing preset commands?</b>"
        "{no_args} - and I will answer this command."
    ).format(no_args=get_answer(command,
                                choice(messages_to_words(i18n, messages)).lower()))

    message = await query.message.edit_text(answer)

    if commands:
        answer = _("Current custom commands:")
        commands = '\n'.join(
            f'▪ /{ui_command} - /{custom_command}'
            for ui_command, custom_command in commands.items()
        )

        await message.answer(f'{answer}\n{commands}')
