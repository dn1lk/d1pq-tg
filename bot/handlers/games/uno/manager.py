from random import choices, choice

from aiogram import Bot, types
from aiogram.dispatcher.fsm.context import FSMContext
from aiogram.dispatcher.fsm.storage.base import StorageKey
from aiogram.utils.i18n import gettext as _
from pydantic import BaseModel

from .cards import UnoCard, UnoSpecials, UnoColors, get_cards
from .exceptions import UnoNoCardsException, UnoNoUsersException
from ... import get_username


class UnoKickPoll(BaseModel):
    message_id: int
    user_id: int
    amount: int


class UnoManager(BaseModel):
    users: dict[int, list[UnoCard]]
    current_user: types.User | None
    next_user: types.User

    current_card: UnoCard | None
    current_special: UnoSpecials

    kick_polls: dict[str, UnoKickPoll] = dict()
    uno_users_id: list[int] = list()

    timer_amount: int = 0

    async def user_next(self, bot: Bot, chat_id: int, user_id: int | None = None) -> types.User:
        user_id = user_id or self.next_user.id
        users = tuple(self.users)

        try:
            user_id = users[users.index(user_id) + 1]
        except IndexError:
            user_id = users[0]

        return (await bot.get_chat_member(chat_id, user_id)).user

    async def user_remove(self, state: FSMContext, user_id: int | None = None):
        user_id = user_id or self.current_user.id

        await self.user_remove_state(state, user_id)
        del self.users[user_id]

        if len(self.users) == 1:
            raise UnoNoUsersException("Only one user remained in UNO game")

    async def user_remove_state(self, state: FSMContext, user_id: int | None = None):
        user_id = user_id or self.current_user.id
        key = StorageKey(
            bot_id=state.key.bot_id,
            chat_id=user_id,
            user_id=user_id,
            destiny=state.key.destiny
        )

        await state.storage.set_state(state.bot, key)
        await state.storage.update_data(state.bot, key, {'uno_chat_id': None})

    async def user_card_add(self, bot: Bot, user: types.User | None = None, amount: int | None = 1) -> str:
        user = user or self.next_user

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

    async def current_card_update(self, card: UnoCard):
        self.current_card = card

        if len(self.users[self.current_user.id]) == 1:
            raise UnoNoCardsException("The user has run out of cards in UNO game")

        self.users[self.current_user.id].remove(card)

    def card_filter(
            self,
            user: types.User,
            sticker: types.Sticker | UnoCard
    ) -> tuple:
        def get_card() -> UnoCard | None:
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

        if user.id == self.next_user.id:
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
                decline = choice(
                    (
                        _("Попытка не засчитана, получай карту! =)."),
                        _("Просто. Пропусти. Ход."),
                    )
                )
        elif card.emoji == self.current_card.emoji:
            if self.current_user and user.id == self.current_user.id:
                accept = _("Продолжаем накидывать карты...")
            elif self.current_special.skip and user.id == self.current_special.skip.id:
                accept = _("Ха, перекидываем ход.")
            elif card == self.current_card:
                accept = choice(
                    (
                        _("Игроку {user} удалось перебить ход!"),
                        _("Даю пари, {user} выиграет эту игру!"),
                        _("Внезапно, {user}.")
                    )
                ).format(user=get_username(user))
            else:
                decline = choice(
                    (
                        _("Попридержи коней, {user}. Сейчас не твой ход."),
                        _("Хей, {user}, твоей карте не место на этом ходу."),
                        _("Нет. Нет, нет, нет. Нет. {user}, ещё раз, нет!")
                    )
                ).format(user=get_username(user))
        else:
            decline = choice(
                (
                    _("Кто-нибудь, объясните этому игроку, как играть."),
                    _("Давай я просто дам тебе карту и мы сделаем вид, что ничего не было?"),
                    _("Делаю ставку на твоё поражение."),
                )
            )

        return card, accept, decline

    async def card_special(self, bot: Bot, chat: types.Chat) -> str:
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
            self.next_user = self.current_special.skip = await self.user_next(bot, chat.id)
            return choice(
                (
                    _("{user} лишается хода?"),
                    _("{user} рискует пропустить ход."),
                )
            )

        def draw():
            self.current_special.draw += self.current_card.special.draw
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
            ) + " " + _("<b>{amount}</b> карты!").format(amount=self.current_special.draw)

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
            answer = answer.format(user=get_username(self.current_special.skip or self.current_user))

        return answer
