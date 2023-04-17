from aiogram import Router, Bot, F, types, html, flags
from aiogram.fsm.context import FSMContext
from aiogram.utils.i18n import gettext as _

from bot.core import filters
from bot.core.utils import TimerTasks
from bot.handlers.commands import CommandTypes
from .misc import errors, keyboards
from .misc.data import UnoData
from .misc.data.players import UnoPlayerData
from .misc.data.settings.additions import UnoAdd, UnoAddState
from .misc.data.settings.difficulties import UnoDifficulty
from .misc.data.settings.modes import UnoMode
from .. import PlayActions, PlayStates

router = Router(name='play:uno:start')
router.message.filter(filters.Command(*CommandTypes.PLAY, magic=F.args.in_(PlayActions.UNO)))


@router.message(PlayStates.UNO)
@flags.timer(name='play', cancelled=False)
async def join_handler(message: types.Message, bot: Bot, state: FSMContext):
    data_uno = await UnoData.get_data(state)

    try:
        player_id = message.from_user.id

        data_uno.players[player_id] = await UnoPlayerData.setup(bot, state, player_id, list(data_uno.deck(7)))
        await data_uno.set_data(state)

        await message.answer(_("{user} join to current game.").format(user=message.from_user.mention_html()))

    except errors.UnoExistedPlayer:
        await message.reply(_("You already in the game."))

    except errors.UnoMaxPlayers:
        await message.reply(_("Already 10 people are playing in the game."))


@router.message()
@flags.timer('play')
async def start_handler(message: types.Message, bot: Bot, state: FSMContext, timer: TimerTasks):
    answer = _(
        "<b>Let's play UNO?</b>\n\n"
        "One minute to make a decision!\n"
        "Difficulty: {difficulty}.\n"
        "Mode: {mode}.\n\n"
        "{additives}\n\n"
        "<b>Already in the game:</b>\n"
        "{user}"
    )

    message = await message.answer(
        answer.format(
            difficulty=html.bold(UnoDifficulty.NORMAL),
            mode=html.bold(UnoMode.FAST),
            additives='\n'.join(f'{add}: {html.bold(UnoAddState.ON)}' for add in UnoAdd),
            user=message.from_user.mention_html(),
        ),
        reply_markup=keyboards.setup_keyboard(),
    )

    from .process import start_timer
    timer[state.key] = start_timer(message, bot, state, timer)
