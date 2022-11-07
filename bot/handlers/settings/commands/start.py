from random import choice

from aiogram import Router, F, types, flags
from aiogram.fsm.context import FSMContext
from aiogram.utils.i18n import I18n, gettext as _

from . import get_args
from .. import Settings
from ..misc import keyboards as k
from ... import NO_ARGS


router = Router(name='settings:commands:start')


@router.callback_query(k.SettingsKeyboard.filter(F.action == 'commands'))
@flags.data('messages')
async def commands_handler(
        query: types.CallbackQuery,
        state: FSMContext,
        i18n: I18n,
        commands: dict[str, tuple[types.BotCommand]],
        messages: list | None,
        custom_commands: dict,
):
    await state.set_state(Settings.command)

    message = await query.message.edit_text(
        _(
            "<b>Tired of writing preset commands?</b>"
            "{no_args} - and I will answer this command."
        ).format(
            no_args=NO_ARGS.format(
                command=choice(commands[i18n.current_locale]).command,
                args=choice(get_args(i18n, messages)).lower()
            )
        )
    )

    if custom_commands:
        custom_commands = '\n'.join(f'/{command[0]} - /{command[1]}' for command in custom_commands.items())
    else:
        custom_commands = _("missing.")

    await message.answer(_("Current custom commands:") + "\n\n" + custom_commands)
