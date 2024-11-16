import secrets

from aiogram import Router, flags, types
from aiogram.fsm.context import FSMContext
from aiogram.utils import formatting
from aiogram.utils.i18n import gettext as _

from handlers.commands.play import PlayStates
from utils import TimerTasks

from . import CTSData, CTSFilter, task
from .misc.helpers import finish_game

router = Router(name="cts:process")
router.message.filter(PlayStates.CTS)


@router.message(CTSFilter())
@flags.timer
async def answer_handler(message: types.Message, state: FSMContext, timer: TimerTasks, data_cts: CTSData) -> None:
    assert message.text is not None, "wrong message object"

    if data_cts.bot_city:
        content = formatting.Text(
            secrets.choice(
                (
                    _("Hmm."),
                    _("And you're smarter than you look."),
                    _("Right!"),
                ),
            ),
            " ",
            _("My city"),
            ": ",
            formatting.Bold(data_cts.bot_city),
            ".",
        )

        message = await message.reply(**content.as_kwargs())

        await data_cts.set_data(state)
        timer[state.key] = task(message, state)
    else:
        _last_letter = formatting.Bold(f'"{message.text[-1]}"')
        content = formatting.Text(
            *secrets.choice(
                (
                    (
                        _("Okay, I have nothing to write on"),
                        " ",
                        _last_letter,
                        "... ",
                        _("Victory is yours."),
                    ),
                    (
                        _("Can't find the right something on"),
                        " ",
                        _last_letter,
                        "... ",
                        _("My defeat."),
                    ),
                    (
                        _("VICTORY... yours. I can't remember that name... You know, it also starts with"),
                        " ",
                        _last_letter,
                        "...",
                    ),
                ),
            ),
        )

        await finish_game(message, state, data_cts, content)


@router.message()
@flags.timer(cancelled=False)
async def mistake_handler(message: types.Message, state: FSMContext, timer: TimerTasks) -> None:
    data_cts = await CTSData.get_data(state)
    if data_cts is None:
        return

    data_cts.fail_amount -= 1

    if data_cts.fail_amount:
        await data_cts.set_data(state)

        if message.text in data_cts.used_cities:
            _title = secrets.choice(
                (
                    _("We have already used this name. Choose another!"),
                    _("I remember exactly that we already used this. Let's try something else."),
                    _("But no, you can’t fool me — this name was already in the game. Be original!"),
                ),
            )
        else:
            _title = secrets.choice(
                (
                    _("I do not understand something or your word is WRONG!"),
                    _("And here it is not. Think better, user!"),
                    _("My algorithms do not deceive me — you are mistaken!"),
                ),
            )

        content = formatting.Text(
            _title,
            "\n",
            formatting.Bold(_("Remaining attempts"), ": ", data_cts.fail_amount),
        )

        await message.reply(**content.as_kwargs())
    else:
        del timer[state.key]

        content = formatting.Text(
            secrets.choice(
                (
                    _("You have no attempts left."),
                    _("Looks like all attempts have been spent."),
                    _("Where is an ordinary user up to artificial intelligence. All attempts have ended."),
                ),
            ),
        )

        await finish_game(message, state, data_cts, content)
