from random import choices, choice
from typing import Optional, List, Dict

from aiogram import Router, Bot, F, types
from aiogram.utils.i18n import gettext as _
from pydantic import BaseModel

from bot import keyboards as k

from .cards import UnoCard, UnoSticker, get_cards, get_card, get_sticker, colors, specials
from ... import get_username


class UnoManager(BaseModel):
    users: Dict[int, List[UnoSticker]]
    now_user: types.User
    now_card: Optional[UnoCard]
    now_special: Optional[list]

    async def next_user(self, bot: Bot, chat: types.Chat) -> types.User:
        users_id = tuple(self.users.keys())

        try:
            user_id = users_id[users_id.index(self.now_user.id) + 1]
        except IndexError:
            user_id = users_id[0]
        print(1, self.now_user)
        self.now_user = (await bot.get_chat_member(chat.id, user_id)).user
        print(2, self.now_user)
        return self.now_user

    async def remove_user(self) -> None:
        try:
            del self.users[self.now_user.id]
        except KeyError:
            pass

    async def add_card(self, bot: Bot, user: types.User = None, count: Optional[int] = 1) -> None:
        self.users[(user or self.now_user).id].extend(
            [
                UnoSticker(file_unique_id=sticker.file_unique_id, file_id=sticker.file_id) for sticker in
                choices(tuple((await bot.get_sticker_set('uno_cards')).stickers), k=count)
            ]
        )

    def remove_card(self, bot: Bot, card: UnoCard) -> Optional[str]:
        for sticker in self.users[self.now_user.id]:
            if sticker.file_unique_id == card.id:
                self.users[self.now_user.id].remove(sticker)
                break

        if not self.users[self.now_user.id]:
            self.remove_user()

            if self.now_user.id == bot.id:
                answer = _("Что-ж, у меня закончились карты, вынужден остаться лишь наблюдателем =(.")
            else:
                answer = _(
                    "{user} использует свою последнюю карту и выходит из игры победителем."
                ).format(user=get_username(self.now_user))

            return answer

    def filter_card(self, user: types.User, card: UnoCard) -> Optional[tuple]:
        action = None
        decline = None

        if user.id == self.now_user.id:
            if not self.now_card:
                action = _("Первый ход сделан.")
            elif card.color == colors.special:
                action = _("Специальная карта!")
            elif (card.number, card.special) == (self.now_card.number, self.now_card.special):
                action = _("Смена цвета!")
            elif self.now_special and self.now_special[0] == specials.color:
                if card.color == self.now_special[1]:
                    self.now_special = None

                    action = _(
                        "Ех, надо было выбирать {color} цвет."
                    ).format(color=choice(tuple(colors.dict(exclude={self.now_special[1]}))))
                else:
                    decline = _(
                        "Ответ неверный. Твой соперник выбрал другой цвет, будь внимательнее!\n"
                        "+1 карта в коллекцию."
                    )
            elif card.color == self.now_card.color:
                action = _("Так-с...")
            else:
                decline = _(
                    "Ну, нет, это неверных ход. Держи за это карту.\n\n"
                    'Чтобы пропустить ход, выбери соответствующую иконку в меню. '
                )
        elif self.now_card and card.id == self.now_card.id:
            action = _("{user} перебил ход!").format(user=get_username(self.now_user))
        else:
            decline = _("Попридержи коней, ковбой. Твоей карте не место на этом ходу, за что ты получаешь к ней пару.")

        if action:
            self.now_user = user
            self.now_card = card

        return action, decline

    async def special_card(self, bot: Bot, chat: types.Chat) -> Optional[str]:
        answer = None

        if self.now_card.special == specials.draw:
            await self.next_user(bot, chat)
            count = self.now_special[2] if self.now_special else 0

            self.now_special = [
                self.now_card.special,
                self.now_user,
                count + (4 if self.now_card.number == 'special' else 2)
            ]
            answer = _(
                "Как жестоко! {user} рискует получить <b>{count}</b> карты."
            ).format(user=get_username(await self.next_user(bot, chat)))
        else:
            if self.now_special:
                await self.add_card(bot, self.now_special[1], self.now_special[2])
                answer = _(
                    "{user} получает {count} карты."
                ).format(user=get_username(self.now_special[1]), count=self.now_special[2])

                self.now_special = None

            if self.now_card.special:
                if self.now_card.special == specials.reverse:
                    self.users = dict(reversed(list(self.users.items())))
                    answer = _("И всё наоборот! {user} меняет очередь.")
                elif self.now_card.special == specials.color:
                    self.now_special = [specials.color, colors.special]
                    answer = _(
                        "Ох, что за стиль! Новый цвет, новый свет - by {user}.\n\n"
                        "Что мы увидим в этот раз?"
                    )
                else:
                    await self.next_user(bot, chat)
                    answer = _("А кто-то уже собирался ходить? {user} рискует пропустить ход.")

                answer = answer.format(user=get_username(self.now_user))

        await self.next_user(bot, chat)

        return answer

    async def move_queue(self, bot: Bot, action: Optional[str] = ''):
        if self.now_user.id != bot.id:
            return {
                'text': action + _(" {user}, твоя очередь.").format(user=get_username(self.now_user)),
                'reply_markup': k.game_uno_show_cards()
            }


def setup():
    from bot.handlers.games import Game

    router = Router(name='game:uno')
    router.message.filter(Game.uno)
    router.inline_query.filter(Game.uno)
    router.callback_query.filter(k.GamesData.filter(F.game == 'uno'))

    from .user import router as action_rt
    from .core import router as start_rt

    sub_routers = (
        action_rt,
        start_rt,
    )

    for sub_router in sub_routers:
        router.include_router(sub_router)

    return router
