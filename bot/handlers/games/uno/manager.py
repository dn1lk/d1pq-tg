from random import choices, choice
from typing import Optional, List, Dict, Union

from aiogram import Bot, types
from aiogram.utils.i18n import gettext as _
from pydantic import BaseModel

from .cards import UnoCard, UnoSpecials, UnoColors, UnoDraw, get_cards
from ... import get_username


class UnoManager(BaseModel):
    users: Dict[int, List[UnoCard]]
    now_user: types.User
    now_card: Optional[UnoCard]
    now_special: UnoSpecials

    async def next_user(self, bot: Bot, chat: types.Chat):
        users_id = tuple(self.users)

        try:
            user_id = users_id[users_id.index(self.now_user.id) + 1]
        except (IndexError, ValueError):
            user_id = users_id[0]

        self.now_user = (await bot.get_chat_member(chat.id, user_id)).user

    def remove_user(self, bot) -> str:
        del self.users[self.now_user.id]

        if self.now_user.id == bot.id:
            answer = _("Что-ж, у меня закончились карты, вынужден остаться лишь наблюдателем =(.")
        else:
            answer = _(
                "{user} использует свою последнюю карту и выходит из игры победителем."
            ).format(user=get_username(self.now_user))

        return answer

    async def add_card(self, bot: Bot, user: types.User = None, amount: Optional[int] = 1) -> str:
        user = user or self.now_user
        self.users[user.id].extend(choices(await get_cards(bot), k=amount))

        if user.id == bot.id:
            return _("Я беру {amount} карты =(.").format(amount=amount)
        else:
            return _(
                "{user} получает {amount} карты."
            ).format(
                user=get_username(user),
                amount=amount
            )

    def update_card(self, bot: Bot, card: UnoCard) -> Optional[str]:
        self.users[self.now_user.id].remove(card)
        self.now_card = card

        if not self.users[self.now_user.id]:
            if self.now_special.draw and self.now_user != self.now_special.draw.user:
                return self.remove_user(bot)

    def filter_card(self, user: types.User, sticker: Union[types.Sticker, UnoCard]) -> Optional[tuple]:
        def get_card() -> Optional[UnoCard]:
            for user_card in self.users[user.id]:
                print(user_card)
                if user_card.id == sticker.file_unique_id:
                    return user_card

        action, decline = None, None

        if isinstance(sticker, types.Sticker):
            card = get_card()

            if not card:
                return card, action, _("Что за шутка, эта карта не из твоей колоды.")
        else:
            card = sticker

        if user.id == self.now_user.id or self.now_special.skip and user.id == self.now_special.skip.id:
            if not self.now_card:
                action = _("Первый ход сделан.")
            elif card.color is UnoColors.special:
                action = _("Специальная карта!")
            elif card.color == self.now_card.color:
                action = _("Так-с...")

                if self.now_special.color:
                    self.now_special.color = None

                    color = choice([color for color in UnoColors.tuple() if color is not self.now_card.color]).value
                    action = _(
                        "Ух ты! У тебя оказалась карта этого цвета...\n"
                        "Точно нужно было брать {color} цвет."
                    ).format(
                        color=' '.join((color[0], str(color[1])))
                    )

            elif card.emoji == self.now_card.emoji:
                action = _("Смена цвета!")
            else:
                decline = _(
                    "Ну, нет, это неверных ход. Держи за это карту.\n\n"
                    'Чтобы пропустить ход, выбери соответствующую иконку в меню.'
                )
        elif self.now_card and card.id == self.now_card.id:
            action = _("{user} перебил ход!").format(user=get_username(self.now_user))
        else:
            decline = _("Попридержи коней, ковбой. Твоей карте не место на этом ходу, за это ты получаешь к ней пару.")

        if action:
            self.now_user = user
            self.now_special.skip = None
            print('- filter', self.now_user.first_name, card.id)

        return card, action, decline

    async def card_special(self, bot: Bot, chat: types.Chat) -> str:
        def card_draw():
            if self.now_card.special.color:
                self.now_special.color = self.now_card.color

                answer = _("\nНу и ждём выбора цвета...")
            else:
                answer = ""

            if self.now_special.draw:
                self.now_card.special.draw.amount += self.now_special.draw.amount

            return answer

        special = None

        if self.now_card.special.draw:
            special = card_draw()

            await self.next_user(bot, chat)
            self.now_special.skip = self.now_card
            self.now_special.draw = UnoDraw(
                user=self.now_user,
                amount=self.now_card.special.draw.amount
            )

            special = _(
                "Как жестоко! {user} рискует получить <b>{amount}</b> карты!"
            ).format(user=get_username(self.now_special.draw.user), amount=self.now_special.draw.amount) + special

        else:
            if self.now_card.special.color:
                self.now_special.color = self.now_card.color
                special = _("Ох, что за стиль! Новый цвет, новый свет - by {user}.")
            elif self.now_card.special.reverse:
                self.users = {user_id: self.users[user_id] for user_id in reversed(tuple(self.users))}
                special = _("И всё наоборот! {user} меняет очередь.")
            elif self.now_card.special.skip:
                await self.next_user(bot, chat)
                self.now_special.skip = self.now_user

                special = _("А кто-то уже собирался ходить? {user} рискует пропустить ход.")

            if special:
                special = special.format(user=get_username(self.now_user))

        return special
