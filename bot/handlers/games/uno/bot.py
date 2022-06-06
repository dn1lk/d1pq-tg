from random import choice

from aiogram import Bot, types
from aiogram.dispatcher.fsm.context import FSMContext
from aiogram.utils.i18n import gettext as _

from bot import keyboards as k
from . import UnoManager, UnoCard, get_card, get_username, specials


def filter_card(bot: Bot, bot_user: types.User, data_uno: UnoManager):
    for card in data_uno.users[bot.id]:
        card = get_card(card)
        action, decline = data_uno.filter_card(bot_user, card)
        if action:
            yield card, action


async def action_card(
        message: types.Message,
        bot: Bot,
        state: FSMContext,
        data: dict,
        data_uno: UnoManager,
        card: UnoCard,
        action: str
):
    answer = data_uno.remove_card(bot, card)
    if answer:
        message = await message.answer(answer)

        if len(data_uno.users) == 1:
            await message.answer(
                _(
                    "<b>Игра закончена.</b>\n\n{user} остался последним игроком."
                ).format(
                    user=get_username(
                        await data_uno.next_user(
                            bot,
                            message.chat
                        )
                    )
                )
            )

            await state.set_state()
            await state.set_data(data)

    special = await data_uno.special_card(bot, message.chat)
    if special:
        message = await message.reply(
            special,
            reply_markup=k.game_uno_color() if data_uno.now_special == specials.color else None
        )

    answer = await data_uno.move_queue(bot, action)
    if answer:
        await message.reply(**answer)
    else:
        data_uno = await gen(message, bot, state, data, data_uno)

    return data_uno


async def gen(message: types.Message, bot: Bot, state: FSMContext, data: dict, data_uno: UnoManager) -> UnoManager:
    bot_user = await bot.get_me()
    bot_cards = tuple(filter_card(bot, bot_user, data_uno))
    if bot_cards:
        data_uno.now_card, action = choice(bot_cards)
        data_uno.now_user = bot_user

        data_uno = await action_card(message, bot, state, data, data_uno, data_uno.now_card, action)
    else:
        await data_uno.add_card(bot, bot_user)
        await message.answer(_("Беру карту."))

    return data_uno
