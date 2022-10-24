import asyncio
from random import choice, shuffle

from aiogram import Bot, types
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.base import StorageKey
from aiogram.utils.i18n import gettext as _, ngettext as ___
from pydantic import BaseModel

from bot.handlers import get_username
from .cards import UnoCard, UnoColors, UnoEmoji
from .exceptions import UnoNoCardsException, UnoNoUsersException, UnoOneCardException
from ..settings import UnoSettings, UnoMode


class UnoUser(BaseModel):
    cards: list[UnoCard]
    cards_played: int = 0


class UnoWinner(BaseModel):
    points: int = 0
    cards_played: int = 0


class UnoSpecials(BaseModel):
    drawn: int = 0
    skipped: int | None = None

    passed: int | None = None


class UnoData(BaseModel):
    deck: list[UnoCard]
    users: dict[int, UnoUser]
    winners: dict[int, UnoWinner] = {}

    current_index: int
    current_card: UnoCard | None = None
    current_special: UnoSpecials = UnoSpecials()

    settings: UnoSettings
    timer_amount: int = 3

    @property
    def prev_index(self) -> int:
        return self.current_index - 1

    @property
    def next_index(self) -> int:
        if self.current_index < len(self.users) - 1:
            return self.current_index + 1
        else:
            return 0

    @property
    def prev_user_id(self) -> int:
        return tuple(self.users)[self.prev_index]

    @property
    def current_user_id(self) -> int:
        return tuple(self.users)[self.current_index]

    @property
    def next_user_id(self) -> int:
        return tuple(self.users)[self.next_index]

    async def get_user(self, state: FSMContext, user_id: int = None) -> types.User:
        return (await state.bot.get_chat_member(state.key.chat_id, user_id or self.current_user_id)).user

    def check_sticker(self, user_id, sticker: types.Sticker) -> UnoCard | None:
        for user_card in self.users[user_id].cards:
            if user_card.file_unique_id == sticker.file_unique_id:
                return user_card

    def filter_card(self, user_id: int, card: UnoCard | None) -> tuple[str | bool, str | bool]:
        accept, decline = False, False

        if not card:
            return accept, _("What a joke, this card is not from your hand, {user}.")

        if user_id == self.current_user_id:
            if not self.current_card:
                accept = _("{user} makes the first turn.")
            elif card.color is UnoColors.black:
                accept = _("Black card by {user}!")
            elif card.color is self.current_card.color:
                accept = choice(
                    (
                        _("So... {user}."),
                        _("Wow, you got {color}!").format(
                            color=card.color.word
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
            if self.current_special.passed:
                if card is self.users[user_id].cards[-1] and \
                        (card.emoji == self.current_card.emoji or card.color is self.current_card.color):
                    accept = choice(
                        (
                            _("{user}, you're in luck!"),
                            _("{user}, is that honest?"),
                        )
                    )
                else:
                    decline = _("No, this card is wrong. Take another one!")
            elif self.current_special.drawn:
                if card.emoji == self.current_card.emoji and card.cost == self.current_card.cost:
                    accept = choice(
                        (
                            _("{user} doesn't want to take cards."),
                            _("What a heat, +2 to the queue!"),
                        )
                    )
                else:
                    decline = _("{user}, calm down and take the cards!")
            elif self.current_special.skipped:
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
                if self.current_card and card.emoji == self.current_card.emoji:
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

    @staticmethod
    def pop_from_deck(deck, amount: int = 1):
        shuffle(deck)

        for card in deck[:amount]:
            deck.remove(card)

        return deck[:amount]

    def add_card(self, bot: Bot, user: types.User, amount: int = 1) -> str:
        self.users[user.id].cards.extend(self.pop_from_deck(self.deck, amount))

        if user.id == bot.id:
            answer = _("I take")
        else:
            answer = _("{user} receives").format(user=get_username(user))

        return answer + " " + ___("a card.", "{amount} cards.", amount).format(amount=amount)

    def update_turn(self, user_id):
        self.current_index = tuple(self.users).index(user_id)
        self.users[self.current_user_id].cards_played += 1
        self.users[self.current_user_id].cards.remove(self.current_card)
        self.deck.append(self.current_card)

        if len(self.users[self.current_user_id].cards) == 1:
            raise UnoOneCardException("The user has one card in UNO game")
        elif not self.users[self.current_user_id].cards:
            raise UnoNoCardsException("The user has run out of cards in UNO game")

    async def check_draw_black_card(self, state: FSMContext) -> str:
        for card in self.users[tuple(self.users)[self.current_index - 2]].cards:
            if card.color is self.deck[-2].color:
                self.current_index = self.prev_index
                answer = _("I see cards with matched color, not only black.")
                break
        else:
            self.current_special.drawn += 2

            if self.prev_user_id == state.bot.id:
                answer = _("Oh no. I checked {user} cards and don't see any cards with matched color, only black.")
            else:
                answer = _("Nope. {user} don't has any cards of the matched color.")

        user = await self.get_user(state, self.prev_user_id)
        answer = answer.format(user=get_username(user)), self.add_card(state.bot, user, self.current_special.drawn)
        self.current_special.drawn = 0

        return "\n".join(answer)

    def update_current_special(self):
        if self.current_card.emoji == UnoEmoji.reverse:
            return self.special_reverse()

        if self.current_card.emoji == UnoEmoji.draw:
            return self.special_draw()

        if self.current_card.emoji == UnoEmoji.skip:
            return self.special_skip()

    async def apply_current_special(self, state: FSMContext):
        self.current_special.skipped = self.current_special.passed = 0

        if self.current_special.drawn:
            answer = self.add_card(
                state.bot,
                user=await self.get_user(state, self.prev_user_id),
                amount=self.current_special.drawn
            )

            self.current_special.drawn = 0

            return answer

    def special_reverse(self) -> str:
        if len(self.users) > 2:
            user_id = self.current_user_id
            self.users = dict(reversed(self.users.items()))
            self.current_index = tuple(self.users).index(user_id)

            return choice(
                (
                    _("And vice versa!"),
                    _("A bit of a mess..."),
                )
            ) + "\n" + _("{user} changes the queue.")

        return self.special_skip()

    def special_skip(self) -> str:
        self.current_index = self.next_index
        self.current_special.skipped = self.current_user_id
        return choice(
            (
                _("{user} loses a turn?"),
                _("{user} risks missing a turn."),
            )
        )

    def special_draw(self) -> str:
        self.current_index = self.next_index
        self.current_special.drawn += 2

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
            self.current_special.drawn,
        ).format(amount=self.current_special.drawn)

    def special_color(self) -> str:
        if self.current_card.emoji == UnoEmoji.draw:
            self.current_special.drawn += 2

        return choice(
            (
                _("Finally, we will change the color.\nWhat will {user} choose?"),
                _("New color, new light.\nby {user}."),
            )
        )

    @staticmethod
    async def add_user(state: FSMContext, user_id: int, deck: list[UnoCard]) -> UnoUser:
        async def add_state():
            from .. import Game

            key = StorageKey(
                bot_id=state.key.bot_id,
                chat_id=user_id,
                user_id=user_id,
                destiny=state.key.destiny
            )

            await state.storage.set_state(state.bot, key, Game.uno)
            await state.storage.update_data(state.bot, key, {'uno_chat_id': state.key.chat_id})

        await add_state()
        return UnoUser(cards=UnoData.pop_from_deck(deck, 7))

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
        cards_played = self.users[user_id].cards_played

        del self.users[user_id]
        await remove_state()

        points = sum(sum(card.cost for card in user_data.cards) for user_data in self.users.values())

        if user_id in self.winners:
            points += self.winners[user_id].points
            cards_played += self.winners[user_id].cards_played

        self.winners[user_id] = UnoWinner(
            points=points,
            cards_played=cards_played,
        )

        if len(self.users) == 1:
            raise UnoNoUsersException("Only one user remained in UNO game")

    async def finish(self, state: FSMContext) -> str:
        for task in asyncio.all_tasks():
            if task.get_name().startswith('uno') and task is not asyncio.current_task():
                task.cancel()

        try:
            while self.users:
                await self.remove_user(state, tuple(self.users)[0])
        except UnoNoUsersException:
            await self.remove_user(state, tuple(self.users)[0])

        if self.settings.mode is not UnoMode.with_points or max(self.winners.values(), key=lambda i: i.points) >= 500:
            await state.clear()
            return _("<b>Game over.</b>")
        else:
            self.current_card = None

            for winner in self.winners:
                self.users[winner] = await self.add_user(state, winner, self.deck)

            self.current_index = -1

            return _("<b>Round over.</b>")
