from random import choice

from aiogram import Router, F, types, flags
from aiogram.fsm.context import FSMContext
from aiogram.utils.i18n import gettext as _

from core import filters, helpers
from core.utils import database, TimerTasks
from handlers.commands import CommandTypes
from handlers.commands.misc.types import PREFIX
from .. import SettingsActions, SettingsStates, keyboards
from ..misc.tasks import idle_task

router = Router(name='commands:start')
router.callback_query.filter(keyboards.SettingsData.filter(F.action == SettingsActions.COMMAND))


@router.callback_query()
@flags.database('gen_settings')
@flags.timer
async def start_handler(
        query: types.CallbackQuery,
        state: FSMContext,
        timer: TimerTasks,
        main_settings: database.MainSettings,
        gen_settings: database.GenSettings,
):
    from handlers.commands.help import get_answer

    await state.set_state(SettingsStates.COMMANDS)

    command = filters.CommandObject(
        prefix=PREFIX,
        command=choice(list(CommandTypes)[:-1])[0]
    )

    answer = _(
        "<b>Tired of writing preset commands?</b>\n\n"
        "{no_args} — and I will answer this command."
    ).format(
        no_args=get_answer(
            command,
            choice(helpers.get_split_text(gen_settings.messages or [_('bla bla')])).lower()
        )
    )

    message = await query.message.edit_text(answer)

    if main_settings.commands:
        answer = _("Current custom commands:")
        commands = '\n'.join(
            f'▪ /{ui_command} — /{custom_command}'
            for ui_command, custom_command in main_settings.commands.items()
        )

        await message.answer(f'{answer}\n{commands}')

    timer[state.key] = idle_task(message, state, 'commands')
