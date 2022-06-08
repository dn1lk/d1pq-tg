import asyncio
from random import choice

from aiogram import types
from aiogram.utils.chat_action import ChatActionSender
from aiogram.utils.i18n import gettext as _

from .action import UnoAction
from .exceptions import UnoNoCardsException
from .manager import UnoManager


async def special_color(data_uno: UnoAction) -> UnoManager:
    color = choice(data_uno.data.now_user_cards).color
    data_uno.data.now_card.color = color

    await data_uno.move(_(
        "Я выбираю {color} цвет."
    ).format(color=' '.join((color.value[0], str(color.value[1])))))

    return data_uno.data


async def get_cards(data_uno: UnoAction, bot_user: types.User):
    for card in data_uno.data.now_user_cards:
        card, action, decline = await data_uno.data.filter_card(data_uno.bot, data_uno.message.chat, bot_user, card)
        if action:
            yield card, action


async def gen(data_uno: UnoAction) -> UnoManager:
    bot_user = await data_uno.bot.get_me()

    while data_uno.data.now_user.id == data_uno.bot.id:
        async with ChatActionSender.choose_sticker(chat_id=data_uno.message.chat.id, interval=1):
            await asyncio.sleep(choice(range(0, 3)))

            data_uno.data.now_user_cards = await data_uno.data.get_now_user_cards(
                data_uno.bot,
                data_uno.state,
                bot_user
            )

            if not data_uno.data.now_user_cards:
                raise UnoNoCardsException

            bot_cards = [card async for card in get_cards(data_uno, bot_user)]
            if bot_cards:
                data_uno.data.now_card, action = choice(bot_cards)
                data_uno.message = await data_uno.message.answer_sticker(data_uno.data.now_card.file_id)

                await data_uno.update(data_uno.data.now_card, action)
            else:
                await data_uno.next(await data_uno.data.add_card(data_uno.bot, data_uno.state))

    return data_uno.data
