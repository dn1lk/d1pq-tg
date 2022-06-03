from random import choice
from typing import Optional

from aiogram import Router, Bot, F, types
from aiogram.utils.i18n import gettext as _

from worker import keyboards as k
from worker.handlers import USERNAME
from worker.handlers.games.uno.cards import STICKERS


async def action_card(user_id: int, sticker_id: str, users: dict, user: list, bonuses: dict) -> Optional[str]:
    if [user_id] == user:
        return _("Первый ход сделан.")
    elif STICKERS[sticker_id][0] == STICKERS[user[1]][0] or STICKERS[sticker_id][0] == 'bonus':
        return _("Так-с...")
    elif STICKERS[sticker_id][1] == STICKERS[user[1]][1] and STICKERS[sticker_id][0] == bonuses.get('choose', STICKERS[sticker_id][0]):
        return _("Смена цвета!")
    elif sticker_id == user[1]:
        return _("{user} перебил ход!").format(
            user=USERNAME.format(
                id=user_id,
                name=users[user][0]
            )
        )


async def add_card(user_id: int, bot: Bot, users: dict) -> dict:
    stickers = (await bot.get_sticker_set('uno_cards')).stickers

    sticker = choice(stickers)
    while sticker.file_unique_id in users[user_id][1]:
        sticker = choice(stickers)

    users[user_id][1][sticker.file_unique_id] = sticker.file_id

    return users


async def bonus_card(message: types.Message, bot: Bot, users: dict, user: list, bonuses: dict) -> tuple[dict, list, dict]:
    print(1, users)
    reply_markup = None

    if STICKERS[message.sticker.file_unique_id][0] == 'bonus':
        if user[0] == bot.id:
            bonuses['choose'] = str(choice(list(k.COLORS)))
        else:
            reply_markup = k.game_uno_choose()

    if STICKERS[message.sticker.file_unique_id][1] == 'choose':
        answer = _("Ох, что за стиль! Новый цвет, новый свет - by {user}.")
    elif STICKERS[message.sticker.file_unique_id][1] == 'reverse':
        answer = _("И всё наоборот! {user} меняет очередь.")
        users = dict(reversed(list(users.items())))
    elif STICKERS[message.sticker.file_unique_id][0] in ('draw', 'skip'):
        user[0] = await next_user(list(users), user[0])

        if STICKERS[message.sticker.file_unique_id][1] == 'skip':
            answer = _("А кто-то уже собирался ходить? {user} рискует пропустить ход.")
        else:
            if not bonuses.get('draw'):
                bonuses['draw'] = 0, user[0]

            bonuses['draw'] = [bonuses['draw'][0] + STICKERS[message.sticker.file_unique_id][2], user[0]]
            answer = _("Как жестоко! {user} рискует получить <b>+") + str(bonuses['draw'][0]) + '.</b>'
    else:
        if bonuses.get('draw'):
            for i in range(user[-1][0]):
                users = await add_card(user[-1][1], bot, users)

            del bonuses['draw']

        return users, user, bonuses

    await message.answer(
        answer.format(user=USERNAME.format(id=user[0], name=users[user[0]][0])),
        reply_markup=reply_markup
    )

    return users, user, bonuses


async def next_user(users: list, user: int) -> list:
    try:
        return users[users.index(user) + 1]
    except IndexError:
        return users[0]


async def prep_user(message: types.Message, bot: Bot, users: dict, user: int, action: Optional[str] = '') -> Optional[list]:
    user = await next_user(list(users), user)

    if len(users[message.from_user.id][1]) == 0:
        if user == bot.id:
            await message.answer(_("Что-ж, у меня закончились карты, вынужден остаться лишь наблюдателем =(."))
        else:
            await message.answer(
                _("{user} использует свою последнюю карту и выходит из игры победителем.").format(
                    user=USERNAME.format(
                        id=message.from_user.id,
                        name=message.from_user.first_name
                    )
                )
            )

        if len(users) - 1 == 1:
            await message.answer(_("<b>Игра закончена.</b>\n\n{user} остался последним игроком.").format(user=USERNAME.format(id=user, name=users[user][0])))
            del users[message.from_user.id]

            return

    if user != bot.id:
        await message.reply(
            action + _(" {user}, твоя очередь.").format(user=USERNAME.format(id=user, name=users[user][0])),
            reply_markup=k.game_uno_show_cards()
        )

    return user


def setup():
    from worker.handlers.games import GameState

    router = Router(name='game')
    router.message.filter(state=GameState.UNO)
    router.inline_query.filter(state=GameState.UNO)
    router.callback_query.filter(k.GamesData.filter(F.game == 'uno'))

    from .user import router as action_rt
    from .start import router as start_rt

    sub_routers = (
        action_rt,
        start_rt,
    )

    for sub_router in sub_routers:
        router.include_router(sub_router)

    return router
