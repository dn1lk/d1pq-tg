from aiogram import Router, F, types, flags, html
from aiogram.fsm.context import FSMContext
from aiogram.utils.i18n import gettext as _

from core.utils import database, TimerTasks
from .. import GPTOptionsActions, GPTSettingsStates, keyboards
from ...misc.tasks import idle_task

router = Router(name='gpt:max_tokens:start')
router.callback_query.filter(keyboards.GPTOptionsData.filter(F.action == GPTOptionsActions.MAX_TOKENS))


@router.callback_query()
@flags.database('gpt_settings')
@flags.timer
async def start_handler(
        query: types.CallbackQuery,
        state: FSMContext,
        timer: TimerTasks,
        gpt_settings: database.GPTSettings,
):
    await state.set_state(GPTSettingsStates.MAX_TOKENS)

    answer = _(
        "<b>Update max tokens per message.</b>\n"
        "Current max tokens: {max_tokens}.\n"
        "\n"
        "Write a number from 0 to 2000."
    ).format(max_tokens=html.bold(gpt_settings.max_tokens))

    message = await query.message.edit_text(answer)

    timer[state.key] = idle_task(message, state, _('max tokens'))
