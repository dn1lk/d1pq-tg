from random import choice

from aiogram import Router, F, types, flags
from aiogram.fsm.context import FSMContext
from aiogram.utils.i18n import I18n, gettext as _

from .. import Settings
from ..misc import keyboards as k

router = Router(name='settings:commands:start')


@router.callback_query(k.SettingsKeyboard.filter(F.action == k.SettingsAction.COMMAND))
@flags.data('messages')
async def start_handler(
        query: types.CallbackQuery,
        state: FSMContext,
        i18n: I18n,
        custom_commands: dict[str, str],
        ui_commands: dict[str, tuple[types.BotCommand]],
        messages: list[str] = None,
):
    await state.set_state(Settings.COMMAND)

    from ... import messages_to_words
    from ...help import get_answer

    answer = _(
        """
        <b>Tired of writing preset commands?</b>
        {no_args} - and I will answer this command.
        """
    ).format(no_args=get_answer(i18n, messages, choice(ui_commands[i18n.current_locale]).command,
                                choice(messages_to_words(i18n, messages))))

    message = await query.message.edit_text(answer)

    answer = _("Current custom commands:")

    if custom_commands:
        custom_commands = '\n'.join(
            f'▪ /{ui_command} - /{custom_command}' for ui_command, custom_command in custom_commands.items()
        )
    else:
        custom_commands = _("missing.")

    await message.answer(f'{answer}\n{custom_commands}')
