import secrets

from aiogram import F, Router, flags, types
from aiogram.fsm.context import FSMContext
from aiogram.utils import formatting
from aiogram.utils.i18n import gettext as _

from core import filters, helpers
from handlers.commands import CommandTypes
from handlers.commands.misc.helpers import get_help_content
from handlers.commands.misc.types import PREFIX
from handlers.commands.settings import SettingsActions, SettingsStates, keyboards
from handlers.commands.settings.misc.tasks import idle_task
from utils import TimerTasks, database

router = Router(name="commands:start")
router.callback_query.filter(keyboards.SettingsData.filter(F.action == SettingsActions.COMMAND))


@router.callback_query()
@flags.database("gen_settings")
@flags.timer
async def start_handler(
    query: types.CallbackQuery,
    state: FSMContext,
    timer: TimerTasks,
    main_settings: database.MainSettings,
    gen_settings: database.GenSettings,
) -> None:
    assert isinstance(query.message, types.Message), "wrong message"

    await state.set_state(SettingsStates.COMMANDS)

    command = filters.CommandObject(
        prefix=PREFIX,
        command=secrets.choice(list(CommandTypes)[:-1])[0],
    )

    _no_args = get_help_content(
        command,
        secrets.choice(helpers.get_split_text(gen_settings.messages or [_("bla bla")])).lower(),
    )

    content = formatting.Text(
        formatting.Bold(_("Tired of writing preset commands?")),
        "\n\n",
        _no_args,
        " — ",
        _("and I will answer this command"),
        ".",
    )

    message = await query.message.edit_text(**content.as_kwargs())
    assert isinstance(message, types.Message), "wrong message"

    if main_settings.commands:
        content = formatting.as_marked_section(
            _("Current custom commands:"),
            *(f"/{ui} — /{command}" for ui, command in main_settings.commands.items()),
        )

        await message.answer(**content.as_kwargs())
        timer[state.key] = idle_task(message, state, "commands")
