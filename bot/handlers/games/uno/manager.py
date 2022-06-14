from random import choices, choice
from typing import Optional, List, Union, Dict

from aiogram import Bot, types
from aiogram.dispatcher.fsm.context import FSMContext
from aiogram.dispatcher.fsm.storage.base import StorageKey
from aiogram.utils.i18n import gettext as _
from pydantic import BaseModel

from .cards import UnoCard, UnoSpecials, UnoColors, UnoDraw, get_cards
from .exceptions import UnoNoCardsException, UnoNoUsersException
from ... import get_username


class UnoKickPoll(BaseModel):
    message_id: int
    user_id: int
    amount: int


class UnoManager(BaseModel):
    users: Dict[int, List[UnoCard]]
    current_user: types.User
    current_card: Optional[UnoCard]
    current_special: UnoSpecials

    kick_polls: Optional[Dict[str, UnoKickPoll]] = dict()
    uno_users_id: Optional[List[int]] = list()

    async def next_user(self, bot: Bot, chat_id: int, user_id: Optional[int] = None) -> types.User:
        user_id = user_id or self.current_user.id
        users = tuple(self.users)

        try:
            user_id = users[users.index(user_id) + 1]
        except IndexError:
            user_id = users[0]

        return (await bot.get_chat_member(chat_id, user_id)).user

    async def prev_user(self, bot: Bot, chat_id: int, user_id: Optional[int] = None) -> types.User:
        user_id = user_id or self.current_user.id
        users = tuple(self.users)

        try:
            user_id = users[users.index(user_id) - 1]
        except IndexError:
            user_id = users[-1]

        return (await bot.get_chat_member(chat_id, user_id)).user

    async def remove_user(self, state: FSMContext, user_id: Optional[int] = None):
        user_id = user_id or self.current_user.id

        await self.remove_user_state(state, user_id)
        del self.users[user_id]

        if len(self.users) == 1:
            raise UnoNoUsersException("Only one user remained in UNO game")

    async def remove_user_state(self, state: FSMContext, user_id: Optional[int] = None):
        user_id = user_id or self.current_user.id
        state.key = StorageKey(
            bot_id=state.key.bot_id,
            chat_id=user_id,
            user_id=user_id,
            destiny=state.key.destiny
        )

        await state.set_state()
        await state.update_data(uno_chat_id=None)

    async def add_card(self, bot: Bot, user: Optional[types.User] = None, amount: Optional[int] = 1) -> str:
        user = user or self.current_user

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

    async def update_current_card(self, card: UnoCard):
        self.current_card = card

        if len(self.users[self.current_user.id]) == 1:
            if not self.current_special.draw or self.current_special.draw.user != self.current_user:
                raise UnoNoCardsException("The user has run out of cards in UNO game")
        else:
            self.users[self.current_user.id].remove(card)

    async def filter_card(
            self,
            bot: Bot,
            chat: types.Chat,
            user: types.User,
            sticker: Union[types.Sticker, UnoCard]
    ) -> Optional[tuple]:
        def get_card() -> Optional[UnoCard]:
            for user_card in self.users[user.id]:
                if user_card.id == sticker.file_unique_id:
                    return user_card

        accept, decline = None, None

        if isinstance(sticker, types.Sticker):
            card = get_card()

            if not card:
                return card, accept, _("Что за шутка, эта карта не из твоей колоды.")
        else:
            card = sticker

        if user.id in (self.current_user.id, (await self.prev_user(bot, chat.id)).id):
            if not self.current_card:
                accept = _("Первый ход сделан.")
            elif card.color is UnoColors.special:
                accept = _("Специальная карта!")
            elif card.color is self.current_card.color:
                accept = _("Так-с...")

                if self.current_special.color:
                    self.current_special.color = None

                    color = choice([color for color in UnoColors.tuple() if color is not self.current_card.color]).value
                    accept = _("Ех, нужно было брать {color} цвет.").format(color=color[0] + ' ' + str(color[1]))
            elif card.emoji == self.current_card.emoji:
                accept = _("Смена цвета!")
            else:
                decline = _(
                    "Кто-нибудь, объясните этому игроку, как играть.\n\n"
                    'Чтобы пропустить ход, выбери последнюю карту в своей колоде.'
                )
        elif card == self.current_card:
            accept = _("{user} перебил ход!").format(user=get_username(user))
        else:
            decline = _("Попридержи коней, ковбой. Твоей карте не место на этом ходу, за это ты получаешь к ней пару.")

        if accept:
            self.current_user = user
            self.current_special.skip = None

        return card, accept, decline

    async def special_card(self, bot: Bot, chat: types.Chat) -> str:
        def reverse():
            self.users = dict(reversed(self.users.items()))
            return choice(
                (
                    _("И всё наоборот!"),
                    _("Немного беспорядка..."),
                )
            ) + "\n" + _("{user} меняет очередь.")

        def color():
            self.current_special.color = self.current_card.color
            return choice(
                (
                    _("Наконец мы поменяем цвет.\nЧто выберет {user}?"),
                    _("Новый цвет, новый свет.\nby {user}."),
                )
            )

        async def skip():
            self.current_user = await self.next_user(bot, chat.id)
            self.current_special.skip = self.current_user
            return choice(
                (
                    _("{user} лишается хода?"),
                    _("{user} рискует пропустить ход."),
                )
            )

        def draw():
            if self.current_special.draw:
                self.current_card.special.draw.amount += self.current_special.draw.amount

            self.current_special.draw = UnoDraw(
                user=self.current_user,
                amount=self.current_card.special.draw.amount
            )

            return choice(
                (
                    _("Как жестоко!"),
                    _("Вот это сюрприз."),
                )
            ) + "\n" + choice(
                (
                        _("{user} рискует получить"),
                        _("{user} может получить"),
                )
            ) + " " + _("<b>{amount}</b> карты!").format(amount=self.current_special.draw.amount)

        answer = None

        if self.current_card.special.reverse:
            answer = reverse()
        else:
            if self.current_card.special.color:
                answer = color()

            if self.current_card.special.skip:
                answer = await skip()

            if self.current_card.special.draw:
                answer = draw()

        if answer:
            answer = answer.format(user=get_username(self.current_user))

        return answer
