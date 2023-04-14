from dataclasses import dataclass, field
from random import randrange

from aiogram import Bot, types
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.base import StorageKey

from bot.handlers.commands.play import PlayStates
from .deck import UnoCard, UnoDeck
from .. import errors


@dataclass
class UnoPlayer:
    _id: int

    cards: list[UnoCard]
    cards_played: int = 0

    points: int = 0
    is_me: bool = False

    def __eq__(self, user_id: int) -> bool:
        return self._id == user_id

    def get_card(self, sticker: types.Sticker) -> UnoCard:
        for card in self.cards:
            if card == sticker:
                return card

        raise errors.UnoInvalidSticker()

    def add_card(self, *cards: UnoCard):
        self.cards.extend(cards)

    def remove_card(self, card: UnoCard):
        self.cards.remove(card)
        self.cards_played += 1

    async def get_user(self, bot: Bot, chat_id: int) -> types.User:
        if self.is_me:
            return await bot.me()

        member = await bot.get_chat_member(chat_id, self._id)
        return member.user

    @staticmethod
    def get_key(bot_id: int, player_id: int):
        return StorageKey(
            bot_id=bot_id,
            chat_id=player_id,
            user_id=player_id,
            destiny='uno_room'
        )

    @classmethod
    async def setup(cls, state: FSMContext, user_id: int, cards: list[UnoCard]) -> "UnoPlayer":
        player = cls(user_id, cards, is_me=user_id == state.key.bot_id)
        key = cls.get_key(state.key.bot_id, user_id)

        storage = state.storage
        await storage.set_state(state.bot, key, PlayStates.UNO)
        await storage.set_data(state.bot, key, {'0': state.key.chat_id})

        return player

    async def clear(self, state: FSMContext):
        key = self.get_key(state.key.bot_id, self._id)

        storage = state.storage
        await storage.set_state(state.bot, key)
        await storage.set_data(state.bot, key, {})


@dataclass
class UnoPlayers:
    _playing: list[UnoPlayer]
    _current_index: int = None

    finished: set[UnoPlayer] = field(default_factory=set)

    def __post_init__(self):
        if self._current_index is None:
            self._current_index = randrange(len(self._playing))

    def __len__(self):
        """Get number of players"""

        return len(self._playing)

    def __iter__(self):
        """Iter players"""

        return self._playing.__iter__()

    def __call__(self, user_id: int) -> UnoPlayer | None:
        """Get player by id"""

        for player in self:
            if player == user_id:
                return player

    def __getitem__(self, index: int) -> UnoPlayer:
        """Get player by index"""

        return self._playing[(self._current_index + index) % len(self)]

    @property
    def current_player(self) -> UnoPlayer:
        return self._playing[self._current_index]

    @current_player.setter
    def current_player(self, player: UnoPlayer):
        self._current_index = self._playing.index(player)

    async def add_player(self, state: FSMContext, user_id: int, cards: list[UnoCard]):
        """Add player"""

        if self(user_id):
            raise errors.UnoExistedPlayer()
        elif len(self) == 10:
            raise errors.UnoMaxPlayers()

        player = await UnoPlayer.setup(state, user_id, cards)
        self._playing.append(player)

    async def kick_player(self, state: FSMContext, deck: UnoDeck, player: UnoPlayer):
        """Remove player and clear player data"""

        deck.cards_in.extend(player.cards)
        self._playing.remove(player)
        self.finished.add(player)

        await player.clear(state)

    def finish_player(self, player: UnoPlayer):
        """Remove player and add to finishers"""

        self._playing.remove(player)

        player.points += sum(sum(player.cards) for player in self._playing)
        self.finished.add(player)

    @classmethod
    async def setup(cls, state: FSMContext, deck: UnoDeck, *user_ids: int) -> "UnoPlayers":
        return cls([await UnoPlayer.setup(state, user_id, list(deck(7))) for user_id in user_ids])

    def restart(self, deck: UnoDeck):
        for player in self._playing:
            self.finish_player(player)

        self._playing = list(self.finished)

        for player in self._playing:
            player.cards = list(deck(7))

    async def clear(self, state: FSMContext):
        for player in self._playing.copy():
            self.finish_player(player)

        for player in self.finished:
            await player.clear(state)
