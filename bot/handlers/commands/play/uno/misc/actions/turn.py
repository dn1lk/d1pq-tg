import logging
import secrets

from aiogram import Bot, types
from aiogram.fsm.context import FSMContext
from aiogram.utils import formatting
from aiogram.utils.i18n import gettext as _

from handlers.commands.play.uno.misc import errors, keyboards
from handlers.commands.play.uno.misc.data import UnoData
from handlers.commands.play.uno.misc.data.deck import UnoCard
from handlers.commands.play.uno.misc.data.settings.modes import UnoMode
from utils import TimerTasks

from .base import finish, restart
from .bot import UnoBot
from .kick import kick_for_cards
from .uno import update_uno

MAX_POINTS = 500


logger = logging.getLogger("bot.uno")


async def proceed_turn(
    message: types.Message,
    bot: Bot,
    state: FSMContext,
    timer: TimerTasks,
    data_uno: UnoData,
    card: UnoCard,
    content: formatting.Text,
) -> None:
    assert message.from_user is not None, "wrong user"

    logger.debug("[UNO] turn proceeding: %s", data_uno)

    try:
        try:
            data_uno.update_turn(message.from_user.id, card)

        except errors.UnoOneCard:
            await update_uno(message, bot, state, timer, data_uno)

        except errors.UnoNoCards as err:
            await kick_for_cards(bot, state, data_uno, message.from_user)

            if (
                data_uno.settings.mode is UnoMode.FAST
                and len(data_uno.players.playing) == 1
                or data_uno.settings.mode is UnoMode.WITH_POINTS
                and max(player.points for player in data_uno.players.finished.values()) >= MAX_POINTS
            ):
                raise errors.UnoFinish from err
            raise errors.UnoRestart from err

    except errors.UnoFinish:
        await finish(bot, state, timer, data_uno)

    except errors.UnoRestart:
        await restart(bot, state, timer, data_uno)

    else:
        await proceed_state(message, bot, state, timer, data_uno, content)


async def proceed_state(
    message: types.Message,
    bot: Bot,
    state: FSMContext,
    timer: TimerTasks,
    data_uno: UnoData,
    content: formatting.Text,
) -> None:
    assert message.from_user is not None, "wrong user"

    logger.debug("[UNO] state proceeding: %s", data_uno)

    try:
        content = await data_uno.update_state(message.from_user, bot, message.chat.id) or content

    except errors.UnoSeven:
        if data_uno.players.current_data.is_me:
            bot_uno = UnoBot(message, bot, state, data_uno)
            content = await bot_uno.do_seven()
        else:
            await _proceed_seven(message, bot, state, timer, data_uno)
            return

    except errors.UnoColor:
        if data_uno.players.current_data.is_me:
            bot_uno = UnoBot(message, bot, state, data_uno)
            content = await bot_uno.do_color()
        else:
            await _proceed_color(message, bot, state, timer, data_uno)
            return

    await next_turn(message, bot, state, timer, data_uno, content)


async def _proceed_seven(
    message: types.Message,
    bot: Bot,
    state: FSMContext,
    timer: TimerTasks,
    data_uno: UnoData,
) -> None:
    assert message.from_user is not None, "wring user"

    logger.debug("[UNO] seven proceeding: %s", data_uno)

    await data_uno.set_data(state)

    content = formatting.Text(
        formatting.TextMention(message.from_user.first_name, user=message.from_user),
        ", ",
        _("with whom will you exchange cards"),
        "?\n",
        _("Mention (@) this player in your next message."),
    )

    message = await message.answer(**content.as_kwargs())
    await update_timer(message, bot, state, timer, data_uno)


async def _proceed_color(
    message: types.Message,
    bot: Bot,
    state: FSMContext,
    timer: TimerTasks,
    data_uno: UnoData,
) -> None:
    assert message.from_user is not None, "wring user"

    logger.debug("[UNO] color proceeding: %s", data_uno)

    await data_uno.set_data(state)

    _user = formatting.TextMention(message.from_user.first_name, user=message.from_user)
    content = formatting.Text(
        *secrets.choice(
            (
                (_("Finally, we will change the color."), "\n", _("What will"), " ", _user, " ", _("choose"), "?"),
                (_("New color, new light."), "\n", _("by"), " ", _user, "."),
            ),
        ),
    )

    message = await message.answer(reply_markup=keyboards.choice_color(), **content.as_kwargs())
    await update_timer(message, bot, state, timer, data_uno)


async def next_turn(
    message: types.Message,
    bot: Bot,
    state: FSMContext,
    timer: TimerTasks,
    data_uno: UnoData,
    content: formatting.Text,
) -> None:
    assert message.from_user is not None, "wring user"

    logger.debug("[UNO] next turn executing: %s", data_uno)

    content = formatting.Text(content, "\n", await data_uno.do_next(bot, state))
    message = await message.reply(
        reply_markup=keyboards.show_cards(bluffed=data_uno.state.bluffed),
        **content.as_kwargs(),
    )

    await update_timer(message, bot, state, timer, data_uno)


async def update_timer(
    message: types.Message,
    bot: Bot,
    state: FSMContext,
    timer: TimerTasks,
    data_uno: UnoData,
) -> None:
    logger.debug("[UNO] timer updating: %s", data_uno)

    from .bot import UnoBot

    bot_uno = UnoBot(message, bot, state, data_uno)
    cards = tuple(bot_uno.get_cards(await bot.me()))

    if cards or data_uno.players.current_data.is_me:
        # Run bot turn
        timer[state.key] = bot_uno.gen_turn(timer, *cards)

    from .timer import task

    timer[state.key] = task(message, bot, state, timer, data_uno)
