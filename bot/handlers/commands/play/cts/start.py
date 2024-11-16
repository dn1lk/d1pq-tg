import secrets

from aiogram import F, Router, flags, types
from aiogram.fsm.context import FSMContext
from aiogram.utils import formatting
from aiogram.utils.i18n import I18n
from aiogram.utils.i18n import gettext as _

from core import filters
from handlers.commands import CommandTypes
from handlers.commands.play import PlayActions, PlayStates
from utils import TimerTasks

from . import CTSData, task

router = Router(name="cts:start")
router.message.filter(filters.Command(*CommandTypes.PLAY, magic=F.args.in_(PlayActions.CTS)))


@router.message()
@flags.timer
async def start_handler(message: types.Message, state: FSMContext, i18n: I18n, timer: TimerTasks) -> None:
    content = formatting.Text(
        _(
            "Oh, Geography. Well, let's try!\n"
            "\n"
            "You need to answer city that begin with the letter "
            "that the previous city ended.",
        ),
    )

    message = await message.answer(**content.as_kwargs())

    data_cts = CTSData()
    if secrets.randbelow(2) == 1:
        cities = data_cts.get_cities(i18n.current_locale)
        data_cts.gen_city(cities)

        assert data_cts.bot_city is not None, "bot city not generated"
        content = formatting.Text(_("I start! My city:"), " ", formatting.Bold(data_cts.bot_city), ".")
    else:
        content = formatting.Text(_("You start! Your city?"))

    await state.set_state(PlayStates.CTS)
    await data_cts.set_data(state)

    message = await message.answer(**content.as_kwargs())
    timer[state.key] = task(message, state)
