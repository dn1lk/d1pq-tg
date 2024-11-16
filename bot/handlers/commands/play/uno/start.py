from aiogram import Bot, F, Router, flags, types
from aiogram.fsm.context import FSMContext
from aiogram.utils import formatting
from aiogram.utils.i18n import gettext as _

from core import filters
from handlers.commands import CommandTypes
from handlers.commands.play import PlayActions, PlayStates
from utils import TimerTasks

from .misc import errors, keyboards
from .misc.data import UnoData
from .misc.data.players import UnoPlayerData
from .misc.data.settings.additions import UnoAdd, UnoAddState
from .misc.data.settings.difficulties import UnoDifficulty
from .misc.data.settings.modes import UnoMode

router = Router(name="uno:start")
router.message.filter(filters.Command(*CommandTypes.PLAY, magic=F.args.in_(PlayActions.UNO)))


@router.message(PlayStates.UNO)
@flags.timer(cancelled=False)
async def join_handler(message: types.Message, state: FSMContext) -> None:
    assert message.from_user is not None, "wrong user"

    data_uno = await UnoData.get_data(state)
    if data_uno is None:
        return

    try:
        player_id = message.from_user.id

        data_uno.players[player_id] = await UnoPlayerData.setup(state, player_id, list(data_uno.deck(7)))
        await data_uno.set_data(state)

        content = formatting.Text(
            formatting.TextMention(message.from_user.first_name, user=message.from_user),
            " ",
            _("join to current game"),
            ".",
        )

        await message.answer(**content.as_kwargs())

    except errors.UnoExistedPlayer:
        content = formatting.Text(_("You already in the game."))
        await message.reply(**content.as_kwargs())

    except errors.UnoMaxPlayers:
        content = formatting.Text(_("Already 10 people are playing in the game."))
        await message.reply(**content.as_kwargs())


@router.message()
@flags.timer
async def start_handler(message: types.Message, bot: Bot, state: FSMContext, timer: TimerTasks) -> None:
    assert message.from_user is not None, "wrong user"

    content = formatting.Text(
        formatting.Bold("Let's play UNO?"),
        "\n\n",
        _("One minute to make a decision!"),
        "\n",
        _("Difficulty"),
        ": ",
        formatting.Bold(UnoDifficulty.NORMAL),
        ".\n",
        _("Mode"),
        ": ",
        formatting.Bold(UnoMode.FAST),
        ".\n\n",
        _("Additives"),
        ":\n",
        formatting.as_marked_list(
            *(formatting.Text(add, ": ", formatting.Bold(UnoAddState.ON), ".") for add in UnoAdd),
        ),
        "\n\n",
        formatting.Bold(_("Already in the game"), ":"),
        "\n",
        formatting.TextMention(message.from_user.first_name, user=message.from_user),
    )

    message = await message.answer(
        reply_markup=keyboards.setup_keyboard(),
        **content.as_kwargs(),
    )

    from .process import start_timer

    timer[state.key] = start_timer(message, bot, state, timer)
