import asyncio
from random import choice

from aiogram import types
from aiogram.utils.i18n import gettext as _

from .action import UnoAction
from .manager import UnoManager


async def special_color(data_uno: UnoAction) -> UnoManager:
    color = choice(data_uno.data.users[data_uno.bot.id]).color
    data_uno.data.now_card.color = color

    await data_uno.move(_(
        "Я выбираю {color} цвет."
    ).format(color=' '.join((color.value[0], str(color.value[1])))))

    return data_uno.data


def get_cards(data_uno: UnoAction, bot_user: types.User):
    for card in data_uno.data.users[data_uno.bot.id]:
        card, action, decline = data_uno.data.filter_card(bot_user, card)
        if action:
            yield card, action


async def gen(data_uno: UnoAction) -> UnoManager:
    bot_user = await data_uno.bot.get_me()

    while data_uno.data.now_user.id == data_uno.bot.id:
        bot_cards = tuple(get_cards(data_uno, bot_user))

        print('- bot', data_uno.data.users.keys(), len(data_uno.data.users[data_uno.data.now_user.id]), data_uno.data.now_user.first_name, (data_uno.data.now_card.color, data_uno.data.now_card.emoji, data_uno.data.now_card.special) if data_uno.data.now_card else None, data_uno.data.now_special)

        if bot_cards:
            data_uno.data.now_card, action = choice(bot_cards)
            print(data_uno.data.now_card)
            data_uno.message = await data_uno.message.answer_sticker(data_uno.data.now_card.file_id)

            await data_uno.update(data_uno.data.now_card, action)
            await asyncio.sleep(choice(range(1, 5)))
        else:
            await data_uno.next(await data_uno.data.add_card(data_uno.bot))

    print('- bot:end', data_uno.data.users.keys(), len(data_uno.data.users[data_uno.data.now_user.id]),
          data_uno.data.now_user.first_name, (data_uno.data.now_card.color, data_uno.data.now_card.emoji,
                                              data_uno.data.now_card.special) if data_uno.data.now_card else None,
          data_uno.data.now_special)

    return data_uno.data
