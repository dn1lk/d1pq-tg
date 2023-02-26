from random import random

from aiogram import Router, types, F, html, flags
from aiogram.fsm.context import FSMContext
from aiogram.utils.i18n import gettext as _, I18n

from bot import filters
from bot.handlers.commands import CommandTypes
from bot.utils import TimerTasks
from . import CTSData, task
from .. import PlayActions, PlayStates

router = Router(name='play:cts:start')
router.message.filter(filters.Command(*CommandTypes.PLAY, magic=F.args.in_(PlayActions.CTS)))


@router.message()
@flags.timer(name='play')
async def start_handler(message: types.Message, state: FSMContext, i18n: I18n, timer: TimerTasks):
    answer = _(
        "Oh, Geography. Well, let's try!\n"
        "\n"
        "You need to answer city that begin with the letter or "
        "letters that the previous city ended."
    )

    message = await message.answer(answer)

    data_cts = CTSData()

    if random() > 0.5:
        cities = data_cts.get_cities(i18n.current_locale)
        data_cts.gen_city(cities)

        answer = _("I start! My city: {bot_city}.").format(bot_city=html.bold(data_cts.bot_city))
    else:
        answer = _("You start! Your city?")

    await state.set_state(PlayStates.CTS)
    await data_cts.set_data(state)

    message = await message.answer(answer)

    timer[state.key] = task(message, state)
