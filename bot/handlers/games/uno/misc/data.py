from enum import IntEnum, EnumMeta
from random import choice, randrange, choices

from aiogram import types, html
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.base import StorageKey
from aiogram.utils.i18n import gettext as _, ngettext as ___
from pydantic import BaseModel

from bot.handlers import get_username
from .cards import UnoCard, UnoColors, UnoEmoji, get_deck
from ... import GamesData


class UnoSettingsMeta(EnumMeta):
    def meta_extract(cls, message: types.Message, index: int):
        enum_word = UnoSettings.get(message.entities)[index].extract_from(message.text)

        for enum in cls:
            if enum.word == enum_word:
                return enum

    def next(cls, current_enum: IntEnum):
        tuple_cls = tuple(cls)
        return tuple_cls[(tuple_cls.index(current_enum) + 1) % len(cls)]


class UnoDifficulty(IntEnum, metaclass=UnoSettingsMeta):
    EASY = 3
    NORMAL = 2
    HARD = 1

    @property
    def word(self) -> str:
        match self:
            case self.EASY:
                return _('slowpoke')
            case self.NORMAL:
                return _('common man')
            case _:
                return _('genius')

    @classmethod
    def extract(cls, message: types.Message) -> "UnoDifficulty":
        return cls.meta_extract(message, 0)


class UnoMode(IntEnum, metaclass=UnoSettingsMeta):
    FAST = 0
    WITH_POINTS = 1

    @property
    def word(self) -> str:
        if self is self.FAST:
            return _('fast')
        return _('with points')

    @classmethod
    def extract(cls, message: types.Message) -> "UnoMode":
        return cls.meta_extract(message, 1)


class UnoAdd(IntEnum, metaclass=UnoSettingsMeta):
    OFF = 0
    ON = 1

    @property
    def word(self) -> str:
        if self is self.OFF:
            return _("disabled")
        return _("enabled")

    @classmethod
    def extract(cls, message: types.Message, n: int) -> "UnoAdd":
        return cls.meta_extract(message, 2 + n)

    @property
    def switcher(self) -> str:
        if self is self.OFF:
            return _("Enable")
        return _("Disable")

    @staticmethod
    def get_names():
        return (
            _('Stacking'),
            _('Seven-O'),
            _('Jump-in'),
        )


class UnoSettings(BaseModel):
    difficulty: UnoDifficulty
    mode: UnoMode

    stacking: UnoAdd
    seven_0: UnoAdd
    jump_in: UnoAdd

    @classmethod
    def extract(cls, message: types.Message) -> "UnoSettings":
        return cls(
            difficulty=UnoDifficulty.extract(message),
            mode=UnoMode.extract(message),
            stacking=UnoAdd.extract(message, 0),
            seven_0=UnoAdd.extract(message, 1),
            jump_in=UnoAdd.extract(message, 2),
        )

    @staticmethod
    def get(entities: list[types.MessageEntity]) -> list[types.MessageEntity]:
        return [entity for entity in entities if entity.type == 'bold'][1:-1]


class UnoStates(BaseModel):
    skipped: int = 0
    drawn: int = 0

    bluffed: int = 0
    passed: int = 0

    seven: int = 0
    uno: int = 0


class UnoStats(BaseModel):
    points: int = 0
    cards_played: int = 0


class UnoData(GamesData):
    deck: list[UnoCard]
    users: dict[int, list[UnoCard]]
    stats: dict[int, UnoStats] = {}

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
        try:
            return tuple(self.users)[self.current_index]
        except IndexError:
            return tuple(self.users)[0]

    @property
    def next_user_id(self) -> int:
        return tuple(self.users)[self.next_index]

    @classmethod
    async def start(
            cls,
            state: FSMContext,
            user_ids: list[int],
            settings: UnoSettings,
            stats: dict[int, UnoStats] = None
    ):
        deck = await get_deck(state.bot)
        users = {user_id: await cls.add_user(state, user_id, deck) for user_id in user_ids}
        current_index = randrange(len(users))

        current_card = deck[-1]
        while current_card.color is UnoColors.BLACK:
            current_card = choice(deck)

        from ... import Games
        await state.set_state(Games.UNO)

        return cls(
            deck=deck,
            users=users,
            stats=stats,
            current_index=current_index,
            current_card=current_card,
            settings=settings,
        )

    @staticmethod
    async def add_user(state: FSMContext, user_id: int, deck: list[UnoCard]) -> list[UnoCard]:
        from ... import Games

        key = StorageKey(
            bot_id=state.key.bot_id,
            chat_id=user_id,
            user_id=user_id,
            destiny='uno_room'
        )

        await state.storage.set_state(state.bot, key, Games.UNO)
        await state.storage.set_data(state.bot, key, {'0': state.key.chat_id})

        return list(UnoData.pop_from_deck(deck, 7))

    async def get_user(self, state: FSMContext, user_id: int = None) -> types.User:
        user_id = user_id or self.current_user_id

        if user_id == state.bot.id:
            return await state.bot.me()

        member = await state.bot.get_chat_member(state.key.chat_id, user_id)
        return member.user

    async def remove_user(self, state: FSMContext, user_id: int):
        async def remove_state():
            key = StorageKey(
                bot_id=state.key.bot_id,
                chat_id=user_id,
                user_id=user_id,
                destiny='uno_room',
            )

            await state.storage.set_state(state.bot, key)
            await state.storage.set_data(state.bot, key, {})

        await remove_state()

        self.current_index = self.prev_index if self.current_index != 0 else len(self.users) - 1

        del self.users[user_id]

        self.stats.setdefault(user_id, UnoStats()).points += sum(
            sum(card.cost for card in user_cards) for user_cards in self.users.values()
        )

    def get_card(self, user_id, sticker: types.Sticker) -> UnoCard | None:
        for card in self.users[user_id]:
            if card.file_unique_id == sticker.file_unique_id:
                return card

    def filter_card(self, user_id: int, card: UnoCard | None) -> tuple[str | bool, str | bool]:
        accept, decline = False, False

        if not card:
            return accept, _("What a joke, this card is not from your hand, {user}.")

        match user_id:
            case self.current_user_id:
                if self.current_state.drawn:
                    if self.settings.stacking and card.emoji == self.current_card.emoji:
                        accept = choice(
                            (
                                _("{user} doesn't want to take cards."),
                                _("What a heat, +cards to the queue!"),
                            )
                        )
                    else:
                        decline = _("{user}, calm down and take the cards!")

                elif card.color is UnoColors.BLACK:
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

            case self.current_state.passed:
                if card is self.users[user_id][-1] and \
                        (card.emoji == self.current_card.emoji or card.color is self.current_card.color):
                    accept = choice(
                        (
                            _("{user}, you're in luck!"),
                            _("{user}, is that honest?"),
                        )
                    )
                else:
                    decline = _("No, this card is wrong. Take another one!")

            case self.current_state.skipped:
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

            case self.prev_user_id:
                if card.emoji == self.current_card.emoji:
                    accept = choice(
                        (
                            _("{user} keeps throwing cards..."),
                            _("{user}, will anyone stop you?"),
                        )
                    )
                else:
                    decline = _("{user}, you have already made your turn.")

            case _ if self.settings.jump_in and card.file_unique_id == self.current_card.file_unique_id:
                accept = choice(
                    (
                        _("We've been interrupted!"),
                        _("I bet {user} will win this game!"),
                        _("Suddenly, {user}."),
                    )
                )

            case _:
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

        self.stats.setdefault(user_id, UnoStats()).cards_played += 1
        self.users[user_id].remove(self.current_card)
        self.deck.append(self.current_card.copy())

    @staticmethod
    def update_uno(user: types.User) -> str:
        return _("{user} has one card left!").format(user=get_username(user))

    def update_null(self) -> str:
        cards = list(self.users.values())
        cards.append(cards.pop(0))

        self.users = dict(zip(self.users.keys(), cards))
        return _("We have exchanged cards with next neighbors!")

    def update_seven(self) -> str | None:
        if len(self.users) == 2:
            return self.update_null()

        self.current_state.seven = self.current_user_id

    def update_draw(self) -> str:
        if self.current_card.emoji == UnoEmoji.DRAW_FOUR:
            self.current_state.drawn += 4
            answer = self.update_bluff()
        else:
            self.current_state.drawn += 2
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

    def update_bluff(self) -> str:
        prev_card = self.deck[-2]

        for card in self.users[self.current_user_id]:
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

        return f'{answer} {html.bold(_("{user} changes the queue."))}'

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

        match self.current_card.emoji:
            case UnoEmoji.NULL if self.settings.seven_0 and self.users[self.current_user_id]:
                return self.update_null()
            case UnoEmoji.SEVEN if self.settings.seven_0 and self.users[self.current_user_id]:
                return self.update_seven()

            case UnoEmoji.DRAW_TWO | UnoEmoji.DRAW_FOUR:
                return self.update_draw()

            case UnoEmoji.REVERSE:
                return self.update_reverse()

            case UnoEmoji.SKIP:
                return self.update_skip()

    @staticmethod
    def pop_from_deck(deck: list[UnoCard], amount: int = 1):
        cards = choices(deck, k=amount)

        for card in cards:
            try:
                deck.remove(card)
            except ValueError:
                pass

            yield card

    def pick_card(self, user: types.User | int, amount: int = 1) -> str:
        if isinstance(user, int):
            user_id = user
            answer_pick = _("I receive")
        else:
            user_id = user.id
            answer_pick = _("{user} receives").format(user=get_username(user))

        self.users[user_id].extend(self.pop_from_deck(self.deck, amount))
        return f'{answer_pick} {___("a card.", "{amount} cards.", amount).format(amount=amount)}'

    def play_seven(self, user: types.User | int, seven_user: types.User):
        if isinstance(user, int):
            answer = _("I exchange")
        else:
            answer = _("{user} exchanges").format(user=get_username(user))

        self.users.update(
            {
                self.current_state.seven: self.users[seven_user.id],
                seven_user.id: self.users[self.current_state.seven],
            }
        )

        self.current_state.seven = 0
        return f'{answer} {_("cards with player {seven_user}.").format(seven_user=get_username(seven_user))}'

    def play_draw(self, user: types.User | int) -> str:
        if not self.current_state.drawn:
            self.current_state.passed = self.current_user_id
            self.current_state.drawn = 1

        answer = self.pick_card(user, self.current_state.drawn)
        self.current_state.drawn = self.current_state.bluffed = 0

        return answer

    async def play_bluff(self, state: FSMContext):
        if self.current_state.bluffed:
            if self.current_state.bluffed == state.bot.id:
                answer = _("Yes, it was a bluff hehe.")
            else:
                answer = _("Bluff! I see suitable cards, not only wilds.")
        else:
            self.current_state.bluffed = self.current_user_id
            self.current_state.drawn += 2

            if self.current_state.bluffed == state.bot.id:
                answer = _("Ah, no. There were no suitable cards =(")
            else:
                answer = choice(
                    (
                        _("Nope. It is not a bluff."),
                        _("Shhh, this card was legal."),
                        _("This card is suitable.")
                    )
                )

        if self.current_state.bluffed == state.bot.id:
            user = state.bot.id
        else:
            user = await self.get_user(state, self.current_state.bluffed)

        return f'{answer} {self.play_draw(user)}'

    async def finish(self, state: FSMContext):
        while self.users:
            await self.remove_user(state, self.next_user_id)

        await state.clear()
