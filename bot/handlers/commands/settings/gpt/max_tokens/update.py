from aiogram import Router, F, types, flags, html
from aiogram.fsm.context import FSMContext
from aiogram.utils.i18n import gettext as _

from core import filters
from core.utils import database, TimerTasks
from handlers.commands import CommandTypes
from handlers.commands.misc.types import PREFIX
from .. import GPTSettingsStates

router = Router(name='gpt:max_tokens:update')
router.message.filter(GPTSettingsStates.MAX_TOKENS, filters.IsAdmin(is_admin=True))


@router.message(F.text.isdigit() & F.text.func(lambda text: 0 < int(text) <= 2000))
@flags.database('gpt_settings')
async def accept_handler(
        message: types.Message,
        state: FSMContext,
        timer: TimerTasks,
        gpt_settings: database.GPTSettings,
):
    gpt_settings.max_tokens = int(message.text)

    del timer[state.key]
    await gpt_settings.save()
    await state.clear()

    answer = _(
        "<b>Max tokens has been successfully updated.</b>\n"
        "Current max tokens: {max_tokens}."
    ).format(max_tokens=html.bold(gpt_settings.max_tokens))

    await message.answer(answer)


@router.message()
@flags.database('gpt_settings')
async def decline_handler(
        message: types.Message,
        state: FSMContext,
        timer: TimerTasks,
):
    data = await state.get_data()
    tries = data.get('tries', 1)

    if tries > 1:
        await state.clear()
        del timer[state.key]

        answer = _(
            "<b>Something is not working for you.</b>\n"
            "{command} - if you decide to set max tokens again."
        ).format(command=f'{PREFIX}{CommandTypes.SETTINGS[0]}')

        await message.answer(answer)
    else:
        await state.update_data(tries=tries + 1)

        answer = _("Wrong number - I accept only from 0 to 2000.")

        await message.answer(answer)
