import secrets

from aiogram import Bot, F, Router, types
from aiogram.fsm.context import FSMContext
from aiogram.utils import formatting
from aiogram.utils.i18n import gettext as _

from handlers.commands.play import PlayStates
from handlers.commands.play.uno.misc.data.deck.colors import UnoColors
from utils import TimerTasks

from . import DRAW_CARD
from .misc import keyboards
from .misc.actions import next_turn, proceed_turn, proceed_uno
from .misc.actions.turn import update_timer
from .misc.data import UnoData
from .misc.data.deck.base import STICKER_SET_NAME

router = Router(name="uno:user")
router.message.filter(PlayStates.UNO)
router.callback_query.filter(PlayStates.UNO)


@router.message(F.sticker.set_name == STICKER_SET_NAME)
async def turn_handler(
    message: types.Message,
    bot: Bot,
    state: FSMContext,
    timer: TimerTasks,
) -> None:
    assert isinstance(message, types.Message), "wrong message"

    data_uno = await UnoData.get_data(state)
    if data_uno is None:
        return

    data = await data_uno.filter.for_turn(message, state, timer)
    if data:
        async with timer.lock(state.key):
            data_uno = await UnoData.get_data(state)
            assert data_uno is not None, "wrong data uno"

            await proceed_turn(message, bot, state, timer, data_uno, **data)


@router.message(F.text == DRAW_CARD)
async def pass_handler(
    message: types.Message,
    bot: Bot,
    state: FSMContext,
    timer: TimerTasks,
) -> None:
    assert isinstance(message, types.Message), "wrong message"
    assert message.from_user is not None, "wrong user"

    data_uno = await UnoData.get_data(state)
    if data_uno is None:
        return

    filtered = await data_uno.filter.for_pass(message, bot, state, timer)
    if filtered:
        async with timer.lock(state.key):
            data_uno = await UnoData.get_data(state)
            assert data_uno is not None, "wrong data uno"

            content = data_uno.do_pass(message.from_user)
            await next_turn(message, bot, state, timer, data_uno, content)


@router.callback_query(keyboards.UnoData.filter(F.action == keyboards.UnoActions.BLUFF))
async def bluff_handler(
    query: types.CallbackQuery,
    bot: Bot,
    state: FSMContext,
    timer: TimerTasks,
) -> None:
    assert isinstance(query.message, types.Message), "wrong message"

    data_uno = await UnoData.get_data(state)
    if data_uno is None:
        return

    filtered = await data_uno.filter.for_bluff(query, bot, state, timer)
    if filtered:
        async with timer.lock(state.key):
            data_uno = await UnoData.get_data(state)
            assert data_uno is not None, "wrong data uno"

            content = formatting.Text(
                await data_uno.do_bluff(bot, state.key.chat_id),
                "\n",
                await data_uno.do_next(bot, state),
            )

            message = await query.message.edit_text(
                reply_markup=keyboards.show_cards(bluffed=False),
                **content.as_kwargs(),
            )

            assert isinstance(message, types.Message), "wrong message"

            await update_timer(message, bot, state, timer, data_uno)
            await query.answer()


@router.message(F.entities.func(lambda entities: entities[0].type in ("mention", "text_mention")))
async def seven_handler(
    message: types.Message,
    bot: Bot,
    state: FSMContext,
    timer: TimerTasks,
) -> None:
    data_uno = await UnoData.get_data(state)
    if data_uno is None:
        return

    data = await data_uno.filter.for_seven(message, bot, state, timer)
    if data:
        async with timer.lock(state.key):
            data_uno = await UnoData.get_data(state)
            assert data_uno is not None, "wrong data uno"

            content = data_uno.do_seven(**data)
            await next_turn(message, bot, state, timer, data_uno, content)


@router.callback_query(keyboards.UnoData.filter(F.action == keyboards.UnoActions.COLOR))
async def color_handler(
    query: types.CallbackQuery,
    bot: Bot,
    state: FSMContext,
    timer: TimerTasks,
    callback_data: keyboards.UnoData,
) -> None:
    assert isinstance(query.message, types.Message), "wrong message"

    data_uno = await UnoData.get_data(state)
    if data_uno is None:
        return

    filtered = await data_uno.filter.for_color(query, state, timer)
    if filtered:
        async with timer.lock(state.key):
            data_uno = await UnoData.get_data(state)
            assert data_uno is not None, "wrong data uno"

            color = callback_data.value
            assert isinstance(color, UnoColors), "wrong callback_data"

            content_color = data_uno.do_color(query.from_user, color)

            content = formatting.Text(
                formatting.TextMention(query.from_user.first_name, user=query.from_user),
                " ",
                _("changes the color to"),
                " ",
                color,
                "!",
            )

            message = await query.message.edit_text(**content.as_kwargs())
            assert isinstance(message, types.Message), "wrong message"

            await next_turn(message, bot, state, timer, data_uno, content_color or formatting.Text())
            await query.answer()


@router.callback_query(keyboards.UnoData.filter(F.action == keyboards.UnoActions.UNO))
async def uno_handler(query: types.CallbackQuery, bot: Bot, state: FSMContext, timer: TimerTasks) -> None:
    assert isinstance(query.message, types.Message), "wrong message"

    data_uno = await UnoData.get_data(state)
    if data_uno is None:
        return

    filtered = await data_uno.filter.for_uno(query, state, timer)
    if filtered:
        async with timer.lock(state.key):
            data_uno = await UnoData.get_data(state)
            assert data_uno is not None, "wrong data uno"

            if not query.message.entities or query.from_user.id != query.message.entities[0].user.id:
                await proceed_uno(query.message, bot, state, data_uno, query.from_user)

            text = secrets.choice(
                (
                    _("Good job!"),
                    _("And you don't want to lose. 😎"),
                    _("On reaction. 😎"),
                    _("Yep!"),
                    _("Like a pro."),
                ),
            )

            await query.answer(text)
