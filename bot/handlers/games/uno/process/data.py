import asyncio
from random import choice, shuffle, randrange

from aiogram import types, html
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.base import StorageKey
from aiogram.utils.i18n import gettext as _, ngettext as ___
from pydantic import BaseModel

from bot.handlers import get_username
from .cards import UnoCard, UnoColors, UnoEmoji, get_deck
from ..settings import UnoSettings


class UnoUser(BaseModel):
    cards: list[UnoCard]
    cards_played: int = 0


class UnoWinner(BaseModel):
    points: int = 0
    cards_played: int = 0


class UnoStates(BaseModel):
    drawn: int = 0
    skipped: int = 0

    passed: int = 0
    bluffed: int = 0
    uno: int = 0


class UnoData(BaseModel):
    deck: list[UnoCard]
    users: dict[int, UnoUser]
    winners: dict[int, UnoWinner] = {}

    current_index: int
    current_card: UnoCard
    current_state: UnoStates = UnoStates()

    settings: UnoSettings
    timer_amount: int = 3

    @property
    def prev_index(self) -> int:
        return (self.current_index - 1) % len(self.users)

    @property
    def next_index(self) -> int:
        return (self.current_index + 1) % len(self.users)

    @property
    def prev_user_id(self) -> int:
        return tuple(self.users)[self.prev_index]

    @property
    def current_user_id(self) -> int:
        return tuple(self.users)[self.current_index]

    @property
    def next_user_id(self) -> int:
        return tuple(self.users)[self.next_index]

    @classmethod
    async def start(
            cls,
            state: FSMContext,
            user_ids: list[int],
            settings: UnoSettings,
            winners: dict[int, UnoWinner] = None
    ):
        deck = await get_deck(state.bot)
        users = {user_id: await cls.add_user(state, user_id, deck) for user_id in user_ids}
        current_index = randrange(len(users))

        current_card = deck[-1]
        while current_card.emoji == UnoEmoji.draw_4:
            current_card = choice(deck)

        winners = winners or {}

        from .. import Games
        await state.set_state(Games.uno)

        return cls(
            deck=deck,
            users=users,
            winners=winners,
            current_index=current_index,
            current_card=current_card,
            settings=settings,
        )

    @classmethod
    async def get(cls, state: FSMContext):
        data = await state.get_data()

        if 'uno' in data:
            return cls(**data['uno'])

    async def update(self, state: FSMContext):
        return await state.update_data(uno=self.dict())

    @staticmethod
    async def add_user(state: FSMContext, user_id: int, deck: list[UnoCard]) -> UnoUser:
        async def add_state():
            from .. import Games

            key = StorageKey(
                bot_id=state.key.bot_id,
                chat_id=user_id,
                user_id=user_id,
                destiny=state.key.destiny
            )

            await state.storage.set_state(state.bot, key, Games.uno)
            await state.storage.update_data(state.bot, key, {'uno_room_id': state.key.chat_id})

        await add_state()
        return UnoUser(cards=UnoData.pop_from_deck(deck, 7))

    async def get_user(self, state: FSMContext, user_id: int = None) -> types.User:
        member = await state.bot.get_chat_member(state.key.chat_id, user_id or self.current_user_id)
        return member.user

    async def remove_user(self, state: FSMContext, user_id: int):
        async def remove_state():
            key = StorageKey(
                bot_id=state.key.bot_id,
                chat_id=user_id,
                user_id=user_id,
                destiny=state.key.destiny,
            )

            await state.storage.set_state(state.bot, key)
            await state.storage.set_data(state.bot, key, {})

        await remove_state()

        cards_played = self.users[user_id].cards_played

        del self.users[user_id]
        points = sum(sum(card.cost for card in user_cards.cards) for user_cards in self.users.values())

        if user_id in self.winners:
            points += self.winners[user_id].points
            cards_played += self.winners[user_id].cards_played

        self.winners[user_id] = UnoWinner(points=points, cards_played=cards_played)

    def get_card(self, user_id, sticker: types.Sticker) -> UnoCard | None:
        for card in self.users[user_id].cards:
            if card.file_unique_id == sticker.file_unique_id:
                return card

    def filter_card(self, user_id: int, card: UnoCard | None) -> tuple[str | bool, str | bool]:
        accept, decline = False, False

        if not card:
            return accept, _("What a joke, this card is not from your hand, {user}.")

        if user_id == self.current_user_id:
            if self.current_state.drawn:
                if card.emoji == self.current_card.emoji:
                    accept = choice(
                        (
                            _("{user} doesn't want to take cards."),
                            _("What a heat, +2 to the queue!"),
                        )
                    )
                else:
                    decline = _("{user}, calm down and take the cards!")

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
            if self.current_state.passed:
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

            elif self.current_state.skipped:
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

    def update_turn(self, user_id: int):
        self.current_index = tuple(self.users).index(user_id)

        self.users[user_id].cards_played += 1
        self.users[user_id].cards.remove(self.current_card)

        self.deck.append(self.current_card)

    def update_uno(self, user: types.User):
        self.current_state.uno = user.id
        answer = _("{user} has one card left!").format(user=get_username(user))

        return answer

    def update_color(self) -> str:
        if self.current_card.emoji == UnoEmoji.draw_4:
            self.current_state.drawn += 2

        answer = choice(
            (
                _("Finally, we will change the color.\nWhat will {user} choose?"),
                _("New color, new light.\nby {user}."),
            )
        )

        return answer

    def update_draw(self):
        self.current_state.drawn += 2

        if self.current_card.emoji == UnoEmoji.draw_4:
            answer = self.update_bluff()
        else:
            answer = choice(
                (
                    _("How cruel!"),
                    _("What a surprise."),
                )
            )

        answer_draw = choice(
            (
                _("{user} is clearly taking revenge... +"),
                _("{user} sends a fiery hello and"),
            )
        )

        answer_amount = ___("a card!", "{amount} cards!", self.current_state.drawn)

        return f'{answer}\n{answer_draw} {answer_amount.format(amount=html.bold(self.current_state.drawn))}'

    def update_bluff(self) -> str | None:
        prev_card = self.deck[-1]

        for card in self.users[self.current_user_id].cards:
            if card.color == prev_card.color:
                self.current_state.bluffed = self.current_user_id
                break

        answer = choice(
            (
                _("Is this card legal?"),
                _("A wild card... one that can be thrown illegally!"),
                _("Will the next player dare to check such a turn..."),
            )
        )

        return answer

    def update_reverse(self) -> str:
        if len(self.users) == 2:
            return self.update_skip()

        user_id = self.current_user_id
        self.users = dict(reversed(self.users.items()))
        self.current_index = tuple(self.users).index(user_id)

        answer = choice(
            (
                _("And vice versa!"),
                _("A bit of a mess..."),
            )
        )

        answer_reverse = _("{user} changes the queue.")

        return f'{answer} {html.bold(answer_reverse)}'

    def update_skip(self) -> str:
        self.current_index = self.next_index
        self.current_state.skipped = self.current_user_id

        answer = choice(
            (
                _("{user} loses a turn?"),
                _("{user} risks missing a turn."),
                _("{user} can forget about the next turn."),
            )
        )

        return answer

    def update_state(self):
        self.current_state.passed = self.current_state.skipped = 0

        if self.current_card.emoji in (UnoEmoji.draw_2, UnoEmoji.draw_4):
            return self.update_draw()

        if self.current_card.emoji == UnoEmoji.reverse:
            return self.update_reverse()

        if self.current_card.emoji == UnoEmoji.skip:
            return self.update_skip()

    @staticmethod
    def pop_from_deck(deck, amount: int = 1):
        shuffle(deck)

        for card in deck[:amount]:
            deck.remove(card)
            yield card

    def pick_card(self, user: types.User, amount: int = 1) -> str:
        self.users[user.id].cards.extend(self.pop_from_deck(self.deck, amount))

        answer_pick = _("{user} receives").format(user=get_username(user))
        answer_amount = ___("a card.", "{amount} cards.", amount).format(amount=amount)

        return f'{answer_pick} {answer_amount}'

    async def play_draw(self, user: types.User) -> str:
        if not self.current_state.drawn:
            self.current_state.passed = self.current_user_id
            self.current_state.drawn = 1

        answer = self.pick_card(user, self.current_state.drawn)
        self.current_state.drawn = self.current_state.bluffed = 0

        return answer

    async def play_bluff(self, state: FSMContext):
        if self.current_state.bluffed:
            answer = _("Bluff! I see suitable cards, not only wilds.")
        else:
            self.current_state.bluffed = self.prev_user_id
            self.current_state.drawn += 2

            if self.current_state.bluffed == state.bot.id:
                answer = _("Ah, no. I decided to check you and there were no suitable cards =(")
            else:
                answer = choice(
                    (
                        _("Nope. It is not bluff."),
                        _("Shhh, this card was legal."),
                        _("I also thought that this card does not belong here. But only it is suitable...")
                    )
                )

        user = await self.get_user(state, self.current_state.bluffed)
        answer_pick = self.pick_card(user, self.current_state.drawn)

        self.current_state.drawn = self.current_state.bluffed = 0
        return f'{answer}\n{answer_pick}'

    async def finish(self, state: FSMContext):
        for task in asyncio.all_tasks():
            if task.get_name().startswith('uno') and task is not asyncio.current_task():
                task.cancel()

        while self.users:
            await self.remove_user(state, self.next_user_id)

        await state.clear()
