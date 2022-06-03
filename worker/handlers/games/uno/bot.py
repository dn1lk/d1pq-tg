from asyncio import sleep
from random import choice

from aiogram import Bot, types
from aiogram.utils.i18n import gettext as _

from worker.handlers.games.uno import STICKERS, action_card, add_card, bonus_card, prep_user


async def no_bot(message: types.Message, bot: Bot, users) -> dict:
    await bot.send_message(message.chat.id, _("Беру карту."))

    return await add_card(bot.id, bot, users)


async def gen_bot(message: types.Message, bot: Bot, users: dict, user: list, bonuses: dict) -> dict:
    print(users, user, bonuses)
    if user[0] == bot.id:
        try:
            if len(user) == 1:
                user.append(choice(list(users[user[0]][1])))
            else:
                user[1] = choice([sticker for sticker in users[user[0]][1].keys() if STICKERS[sticker][0] == 'bonus' or any(value in STICKERS[user[1]] for value in STICKERS[sticker])])

            message = await bot.send_sticker(chat_id=message.chat.id, sticker=users[user[0]][1].pop(user[1]))
            action = await action_card(message.from_user.id, message.sticker.file_unique_id, users, user, bonuses)
            users, user, bonuses = await bonus_card(message, bot, users, user, bonuses)

        except IndexError:
            if STICKERS[user[1]][1] not in ('draw', 'skip'):
                users = await no_bot(message, bot, users)
            action = ''

        print(2, users)
        user[0] = await prep_user(message, bot, users, user[0], action)
        print(3, users)

        if user[0] == bot.id:
            await sleep(choice(range(10)))
            users, user, bonuses = (await gen_bot(message, bot, users, user, bonuses)).values()

    return {'users': users, 'user': user, 'bonuses': bonuses}
