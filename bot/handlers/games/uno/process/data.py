import asyncio
from enum import Enum
from random import choices, choice

from aiogram import Bot, types
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.base import StorageKey
from aiogram.utils.i18n import gettext as _, ngettext as ___
from pydantic import BaseModel

from bot.handlers import get_username
from .cards import UnoCard, UnoColors, UnoEmoji
from .exceptions import UnoNoCardsException, UnoNoUsersException, UnoOneCardException
from ..settings import UnoSettings


class UnoUser(BaseModel):
    cards: list[UnoCard]
    cards_played: int = 0


class UnoWinner(BaseModel):
    points: int
    cards_played: int


class UnoData(BaseModel):
    cards: list[UnoCard]
    users: dict[int, UnoUser]
    current_index: int

    winners: list[UnoWinner] = list()

    current_card: UnoCard | None = None

    settings: UnoSettings
    timer_amount: int = 3

    @property
    def prev_index(self) -> int:
        return self.current_index - 1

    @property
    def next_index(self) -> int:
        if self.current_index < len(self.users):
            return self.current_index + 1
        else:
            return 0

    @property
    def prev_uno_user(self) -> int:
        return tuple(self.users)[self.prev_index]

    @property
    def current_user_id(self) -> int:
        return tuple(self.users)[self.current_index]

    @property
    def next_user_id(self) -> int:
        return tuple(self.users)[self.next_index]

    async def get_user(self, state: FSMContext, user_id: int = None) -> types.User:
        return (await state.bot.get_chat_member(state.key.chat_id, user_id or self.current_uno_user.user_id)).user

    def check_sticker(self, user_id, sticker: types.Sticker) -> UnoCard | None:
        for user_card in self.users[user_id].cards:
            if user_card.file_unique_id == sticker.file_unique_id:
                return user_card

    def filter_card(self, user_id: int, card: UnoCard | None) -> tuple[str | bool, str | bool]:
        accept, decline = False, False

        if not card:
            return accept, _("What a joke, this card is not from your deck, {user}.")

        if user_id == self.current_user_id:
            if not self.current_card:
                accept = _("{user} makes the first turn.")
            elif card.color is UnoColors.black:
                accept = _("Black card by {user}!")
            elif card.color is self.current_card.color:
                accept = choice(
                    (
                        _("So... {user}."),
                        _("Wow, you got {emoji} {color}!").format(
                            emoji=card.color.value,
                            color=card.color.name
                        ),
                    )
                )
            elif card.emoji == self.current_card.emoji:
                accept = _("{user} changes color!")
            else:
                decline = choice(
                    (
                        _("{user}, attempt not counted, get a card! =)."),
                        _("Just. Skip. Turn."),
                        _("Someday {user} will be able to make the right turn.")
                    )
                )

        elif user_id == self.prev_user_id:
            if user_id == self.skipped_user_id:
                if card.emoji == self.current_card.emoji or card.color == self.current_card.color:
                    accept = choice(
                        (
                            _("{user}, you're in luck!"),
                            _("{user}, is that honest?"),
                        )
                    )
                else:
                    decline = _("No, this card is wrong. Take another one!")
            elif self.current_draw:
                if card.emoji == self.current_card.emoji:
                    accept = choice(
                        (
                            _("{user} doesn't want to take cards."),
                            _("What a heat, +2 to the queue!"),
                        )
                    )
                else:
                    decline = _("{user}, calm down and take the cards!")
            elif self.current_skip:
                if card.emoji == self.current_card.emoji:
                    accept = choice(
                        (
                            _("{user} is unskippable!"),
                            _("{user}, you can't be skipped!"),
                            _("Skips are not for you =).")
                        )
                    )
                else:
                    decline = _("{user}, your turn is skipped =(.")
            else:
                if card.emoji == self.current_card.emoji:
                    accept = choice(
                        (
                            _("{user} keeps throwing cards..."),
                            _("{user}, will anyone stop you?"),
                        )
                    )
                else:
                    decline = _("{user}, you have already made your turn.")

        elif card.file_unique_id == self.current_card.file_unique_id:
            accept = choice(
                (
                    _("We've been interrupted!"),
                    _("I bet {user} will win this game!"),
                    _("Suddenly, {user}."),
                )
            )

        else:
            decline = choice(
                (
                    _("Hold your horses, {user}. Now is not your turn."),
                    _("Hey, {user}. Your card doesn't belong this turn."),
                    _("No. No no no. No. Again, NO!"),
                    _("Someone explain to {user} how to play."),
                    _("Can I just give {user} a card and we'll pretend like nothing happened?"),
                    _("I'm betting on {user}'s defeat."),
                )
            )

        return accept, decline

    def pop_from_cards(self, amount: int = 1):
        cards = choices(self.cards, k=amount)

        for card in cards:
            self.cards.remove(card)

        return cards

    def add_card(self, bot: Bot, user: types.User, amount: int = 1) -> str:
        self.users[user.id].cards.extend(self.pop_from_cards(amount))

        if user.id == bot.id:
            answer = _("I take")
        else:
            answer = _("{user} receives").format(user=get_username(user))

        return answer + " " + ___("{amount} card.", "{amount} cards.", amount).format(amount=amount)

    def update_turn(self, user_id):
        self.current_index = tuple(self.users).index(user_id)
        self.current_uno_user.cards_played += 1
        self.current_uno_user.cards.remove(self.current_card)
        self.cards.append(self.current_card)

        if len(self.current_uno_user.cards) == 1:
            raise UnoOneCardException("The user has one card in UNO game")
        elif not self.users[self.current_user_id].cards:
            raise UnoNoCardsException("The user has run out of cards in UNO game")

    def update_current_special(self):
        if self.current_card.emoji == UnoEmoji.reverse:
            return self.special_reverse()

        if self.current_card.emoji == UnoEmoji.draw:
            return self.special_draw()

        if self.current_card.emoji == UnoEmoji.skip:
            return self.special_skip()

    async def apply_current_special(self, state: FSMContext):
        if self.current_draw:
            user = (await state.bot.get_chat_member(state.key.chat_id, self.prev_user_id)).user
            answer = self.add_card(state.bot, user, self.current_draw)
            self.current_draw = 0

            return answer

        self.current_skip = self.skipped_user_id = 0

    def special_reverse(self) -> str:
        if len(self.users) > 2:
            self.users = dict(reversed(self.users.items()))
            return choice(
                (
                    _("And vice versa!"),
                    _("A bit of a mess..."),
                )
            ) + "\n" + _("{user} changes the queue.")

        return self.special_skip()

    def special_skip(self) -> str:
        self.current_user_id = self.current_skip = self.next_user_id
        return choice(
            (
                _("{user} loses a turn?"),
                _("{user} risks missing a turn."),
            )
        )

    def special_draw(self) -> str:
        self.current_user_id = self.next_user_id
        self.current_draw += 2

        return choice(
            (
                _("How cruel!"),
                _("What a surprise."),
            )
        ) + "\n" + choice(
            (
                _("{user} risks getting"),
                _("{user} can get"),
            )
        ) + " " + ___(
            "<b>{amount}</b> card!",
            "<b>{amount}</b> cards!",
            self.current_draw,
        ).format(amount=self.current_draw)

    def special_color(self) -> str:
        if self.current_card.emoji == UnoEmoji.draw:
            self.current_draw += 2

        return choice(
            (
                _("Finally, we will change the color.\nWhat will {user} choose?"),
                _("New color, new light.\nby {user}."),
            )
        )

    async def remove_user(self, state: FSMContext, user_id: int = None):
        async def remove_state():
            key = StorageKey(
                bot_id=state.key.bot_id,
                chat_id=user_id,
                user_id=user_id,
                destiny=state.key.destiny,
            )

            await state.storage.set_state(state.bot, key)
            await state.storage.set_data(state.bot, key, {})

        user_id = user_id or self.current_user_id

        self.winners[user_id] = UnoWinner(
            cards_played=self.users[user_id].cards_played,
            points=sum(
                card.cost for card in sum(
                    user_data.cards for user, user_data in self.users.items() if user != user_id
                )
            )
        )

        del self.users[user_id]
        await remove_state()

        if len(self.users) == 1:
            raise UnoNoUsersException("Only one user remained in UNO game")

    async def finish(self, state: FSMContext) -> str:
        for task in asyncio.all_tasks():
            if task.get_name().startswith('uno') and task is not asyncio.current_task():
                task.cancel()

        while self.users:
            await self.remove_user(state, tuple(self.users)[0])

        await state.clear()

        return _("<b>Game over.</b>") + "\n"
