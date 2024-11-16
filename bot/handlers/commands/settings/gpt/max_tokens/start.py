from aiogram import F, Router, flags, types
from aiogram.fsm.context import FSMContext
from aiogram.utils import formatting
from aiogram.utils.i18n import gettext as _

from handlers.commands.settings.gpt import GPTOptionsActions, GPTSettingsStates, keyboards
from handlers.commands.settings.misc.tasks import idle_task
from utils import TimerTasks, database

router = Router(name="gpt:max_tokens:start")
router.callback_query.filter(keyboards.GPTOptionsData.filter(F.action == GPTOptionsActions.MAX_TOKENS))


@router.callback_query()
@flags.database("gpt_settings")
@flags.timer
async def start_handler(
    query: types.CallbackQuery,
    state: FSMContext,
    timer: TimerTasks,
    gpt_settings: database.GPTSettings,
) -> None:
    assert isinstance(query.message, types.Message), "wrong message"

    await state.set_state(GPTSettingsStates.MAX_TOKENS)

    content = formatting.Text(
        formatting.Bold(_("Change max tokens per message")),
        ".\n",
        _("Current max tokens"),
        ": ",
        formatting.Bold(gpt_settings.max_tokens),
        ".\n\n",
        _("Write a number from 0 to 2000."),
    )

    message = await query.message.edit_text(**content.as_kwargs())
    assert isinstance(message, types.Message), "wrong message"

    timer[state.key] = idle_task(message, state, _("max tokens"))
    await query.answer()
