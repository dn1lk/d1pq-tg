from random import choices, choice
from typing import Optional, List, Union

from aiogram import Bot, types
from aiogram.dispatcher.fsm.context import FSMContext
from aiogram.dispatcher.fsm.storage.base import StorageKey
from aiogram.utils.i18n import gettext as _
from pydantic import BaseModel

from .cards import UnoCard, UnoSpecials, UnoColors, UnoDraw, get_cards
from .exceptions import UnoNoCardsException
from ... import get_username


class UnoManager(BaseModel):
    users: List[int]
    now_user: types.User
    now_card: Optional[UnoCard]
    now_special: UnoSpecials

    now_user_cards: Optional[List[UnoCard]]

    async def next_user(self, bot: Bot, chat: types.Chat):
        try:
            user_id = self.users[self.users.index(self.now_user.id) + 1]
        except (IndexError, ValueError):
            user_id = self.users[0]

        self.now_user = (await bot.get_chat_member(chat.id, user_id)).user

    async def prev_user(self, bot, chat: types.Chat, user: Optional[types.User] = None):
        user = user or self.now_user.id

        try:
            user_id = self.users[self.users.index(user) - 1]
        except (IndexError, ValueError):
            user_id = self.users[-1]

        return (await bot.get_chat_member(chat.id, user_id)).user

    async def remove_user(self, bot: Bot, state: FSMContext) -> str:
        self.users.remove(self.now_user.id)
        self.now_user_cards = None

        await self.update_now_user_cards(bot, state)

        if self.now_user.id == bot.id:
            answer = _("Что-ж, у меня закончились карты, вынужден остаться лишь наблюдателем =(.")
        else:
            answer = _(
                "{user} использует свою последнюю карту и выходит из игры победителем."
            ).format(user=get_username(self.now_user))

        return answer

    async def add_card(
            self,
            bot: Bot,
            state: FSMContext,
            user: Optional[types.User] = None,
            amount: Optional[int] = 1
    ) -> str:
        user = user or self.now_user

        now_user_cards = await self.get_now_user_cards(bot, state, user)
        now_user_cards.extend(choices(await get_cards(bot), k=amount))

        await self.update_now_user_cards(bot, state, user.id, now_user_cards)

        if user.id == bot.id:
            return _("Я беру {amount} карты =(.").format(amount=amount)
        else:
            return _(
                "{user} получает {amount} карты."
            ).format(
                user=get_username(user),
                amount=amount
            )

    @staticmethod
    async def get_now_user_cards(bot: Bot, state: FSMContext, user: types.User) -> Optional[List[UnoCard]]:
        return (
            await state.storage.get_data(
                bot,
                StorageKey(bot.id, user.id, user.id),
            )
        ).get('uno_cards')

    async def update_now_user_cards(
            self,
            bot: Bot,
            state: FSMContext,
            user_id: Optional[int] = None,
            cards: Optional[List[UnoCard]] = None
    ):
        user_id = user_id or self.now_user.id
        cards = cards or self.now_user_cards

        await state.storage.update_data(
            bot,
            StorageKey(bot.id, user_id, user_id),
            {'uno_cards': cards}
        )

    async def update_card(self, bot: Bot, state: FSMContext, card: UnoCard):
        self.now_user_cards.remove(card)
        self.now_card = card

        await self.update_now_user_cards(bot, state)

        if not self.now_user_cards:
            if not self.now_special.draw or self.now_special.draw.user != self.now_user:
                raise UnoNoCardsException("The user has run out of cards in UNO game")

    async def filter_card(
            self,
            bot: Bot,
            chat: types.Chat,
            user: types.User,
            sticker: Union[types.Sticker, UnoCard]
    ) -> Optional[tuple]:
        def get_card() -> Optional[UnoCard]:
            for user_card in self.now_user_cards:
                if user_card.id == sticker.file_unique_id:
                    return user_card

        action, decline = None, None

        if isinstance(sticker, types.Sticker):
            card = get_card()

            if not card:
                return card, action, _("Что за шутка, эта карта не из твоей колоды.")
        else:
            card = sticker

        if user.id == self.now_user.id or user.id == (await self.prev_user(bot, chat, user)).id:
            if not self.now_card:
                action = _("Первый ход сделан.")
            elif card.color is UnoColors.special:
                action = _("Специальная карта!")
            elif card.color is self.now_card.color:
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
                self.users = list(reversed(self.users))
                special = _("И всё наоборот! {user} меняет очередь.")
            elif self.now_card.special.skip:
                await self.next_user(bot, chat)
                self.now_special.skip = self.now_user

                special = _("А кто-то уже собирался ходить? {user} рискует пропустить ход.")

            if special:
                special = special.format(user=get_username(self.now_user))

        return special
