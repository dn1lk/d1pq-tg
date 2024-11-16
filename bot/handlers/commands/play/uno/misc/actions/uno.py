import logging
import secrets
from dataclasses import replace

from aiogram import Bot, types
from aiogram.fsm.context import FSMContext
from aiogram.utils import formatting
from aiogram.utils.i18n import gettext as _

from handlers.commands.play.uno.misc import keyboards
from handlers.commands.play.uno.misc.data import UnoData
from utils import TimerTasks

logger = logging.getLogger("bot.uno")


async def update_uno(
    message: types.Message,
    bot: Bot,
    state: FSMContext,
    timer: TimerTasks,
    data_uno: UnoData,
) -> None:
    logger.debug("[UNO] uno updating: %s", data_uno)

    user = message.from_user
    assert user is not None, "wrong user"

    if data_uno.players[user.id].is_me:
        a, b = 0, 2
        content = formatting.Text(
            secrets.choice(
                (
                    _("I have only one card!"),
                    _("I am left with one card."),
                    _("I am on the verge of victory!"),
                    _("This is my penultimate card..."),
                ),
            ),
        )
    else:
        _user = formatting.TextMention(user.first_name, user=user)

        a, b = 2, 4
        content = formatting.Text(
            *secrets.choice(
                (
                    (_user, " ", _("is left with one card"), "!"),
                    (_user, " ", _("is on the verge of victory"), "!"),
                    (_user, " ", _("can get +2 cards right now"), "."),
                    (_("I want to note"), " — ", _user, " ", _("has the last card left!")),
                ),
            ),
        )

    key = replace(state.key, destiny="play:uno:last")
    async with timer.lock(key):
        message = await message.answer(reply_markup=keyboards.say_uno(), **content.as_kwargs())

        from .bot import UnoBot

        bot_uno = UnoBot(message, bot, state, data_uno)
        timer[key] = bot_uno.gen_uno(timer, a, b)


async def proceed_uno(
    message: types.Message,
    bot: Bot,
    state: FSMContext,
    data_uno: UnoData,
    user: types.User,
) -> None:
    logger.debug("[UNO] uno proceeding: %s", data_uno)

    if data_uno.players[user.id].is_me:
        _action = formatting.Text(
            secrets.choice(
                (
                    _("I toss 2 cards"),
                    _("I give 2 cards"),
                    _("I throw 2 cards"),
                    _("I say UNO"),
                ),
            ),
        )
    else:
        _user = formatting.TextMention(user.first_name, user=user)
        _action = formatting.Text(
            *secrets.choice(
                (
                    (_user, " ", _("tosses 2 cards")),
                    (_user, " ", _("gives 2 cards")),
                    (_user, " ", _("throws 2 cards")),
                    (_user, " ", _("say UNO")),
                ),
            ),
        )

    if message.entities:  # if user has one card
        uno_user = message.entities[0].user
        assert uno_user is not None, "wrong user"

        _mention = formatting.Text(_("to"), " ", formatting.TextMention(uno_user.first_name, user=uno_user))
    else:  # if bot has one card
        uno_user = await bot.me()
        _mention = formatting.Text(
            secrets.choice(
                (
                    _("to me"),
                    _("to your servitor"),
                ),
            ),
        )

    data_uno.players.playing[uno_user.id].add_card(*data_uno.deck(2))
    await data_uno.set_data(state)

    content = formatting.Text(_action, " ", _mention, ".")
    await message.edit_text(**content.as_kwargs())
