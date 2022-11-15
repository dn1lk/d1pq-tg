from random import random, choice

from aiogram import Router, types, F, html, flags
from aiogram.fsm.context import FSMContext
from aiogram.utils.i18n import gettext as _, I18n

from bot.utils.timer import timer
from .misc.data import CTSData, get_cities
from .. import Games, win_timeout
from ...settings.commands import CustomCommandFilter

router = Router(name='game:cts:start')
router.message.filter(CustomCommandFilter(commands=['play', 'поиграем'], magic=F.args.in_(('cts', 'грд'))))


@router.message()
@flags.timer('game')
async def start_handler(message: types.Message, state: FSMContext, i18n: I18n):
    message = await message.answer(
        _(
            "Oh, the game of cities. Well, let's try!\n\n"
            "The rules are as follows: you need to answer the name of the settlement, "
            "starting with the last letter of the name of the previous settlement.\n"
            "You have 60 seconds to think."
        )
    )

    if random() > 0.5:
        bot_var = choice(get_cities(i18n.current_locale))
        data_cts = CTSData(bot_var=bot_var, cities=[bot_var])
        answer = _("I start! My word: {bot_var}.").format(bot_var=html.bold(bot_var))

    else:
        data_cts = CTSData()
        answer = _("You start! Your word?")

    await state.set_state(Games.CTS)
    await data_cts.set_data(state)

    return timer.dict(win_timeout(await message.answer(answer), state))
