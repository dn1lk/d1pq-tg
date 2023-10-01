from dataclasses import dataclass, field
from random import randrange

from aiogram import Bot, types
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.base import StorageKey

from handlers.commands.play import PlayStates
from .deck import UnoCard, UnoDeck
from .. import errors


@dataclass
class UnoPlayerData:
    cards: list[UnoCard]
    is_me: bool

    cards_played: int = 0
    points: int = 0

    def add_card(self, *cards: UnoCard):
        self.cards.extend(cards)

    def get_card(self, sticker: types.Sticker) -> UnoCard:
        for card in self.cards:
            if card == sticker:
                return card

        raise errors.UnoInvalidSticker()

    def del_card(self, card: UnoCard):
        self.cards.remove(card)
        self.cards_played += 1

        if len(self.cards) == 1:
            raise errors.UnoOneCard()
        if len(self.cards) == 0:
            raise errors.UnoNoCards()

    @staticmethod
    def get_key(bot_id: int, player_id: int):
        return StorageKey(
            bot_id=bot_id,
            chat_id=player_id,
            user_id=player_id,
            destiny='uno_room'
        )

    @classmethod
    async def setup(cls, state: FSMContext, player_id: int, cards: list[UnoCard]) -> "UnoPlayerData":
        key = cls.get_key(state.key.bot_id, player_id)

        storage = state.storage
        await storage.set_state(key, PlayStates.UNO)
        await storage.set_data(key, {'0': state.key.chat_id})

        return cls(cards=cards, is_me=player_id == state.key.bot_id)

    @classmethod
    async def clear(cls, state: FSMContext, player_id: int):
        key = cls.get_key(state.key.bot_id, player_id)

        storage = state.storage
        await storage.set_state(key)
        await storage.set_data(key, {})


@dataclass
class UnoPlayers:
    playing: dict[int, UnoPlayerData]
    _current_index: int

    finished: dict[int, UnoPlayerData] = field(default_factory=dict)

    def __len__(self):
        """Get number of all players"""

        return len(self.playing | self.finished)

    def by_index(self, index: int) -> int:
        """Get player id by index"""

        return tuple(self.playing)[(self._current_index + index) % len(self.playing)]

    def __getitem__(self, player_id: int) -> UnoPlayerData:
        """Get player data by id"""

        return self.playing.get(player_id) or self.finished[player_id]

    def __setitem__(self, player_id: int, player_data: UnoPlayerData):
        """Add player"""

        if player_id in self.playing | self.finished:
            raise errors.UnoExistedPlayer()
        elif len(self) == 10:
            raise errors.UnoMaxPlayers()

        self.playing[player_id] = player_data

    @property
    def current_id(self) -> int:
        return self.by_index(0)

    @current_id.setter
    def current_id(self, player_id: int):
        self._current_index = tuple(self.playing).index(player_id)
        assert self.current_data == self.playing[player_id]

    @property
    def current_data(self) -> UnoPlayerData:
        return self.playing[self.current_id]

    async def kick_player(self, state: FSMContext, deck: UnoDeck, player_id: int):
        """Remove player, return cards and clear player data"""

        player_data = self.playing.pop(player_id)
        assert isinstance(player_data, UnoPlayerData)

        deck.add(*player_data.cards)
        await player_data.clear(state, player_id)

    def finish_player(self, player_id: int):
        """Remove player, add to finished and add points"""

        player_data = self.finished[player_id] = self.playing.pop(player_id)
        assert isinstance(player_data, UnoPlayerData)

        player_data.points += sum(sum(other_data.cards) for other_data in self.playing.values())

    async def get_user(self, bot: Bot, chat_id: int, player_id: int) -> types.User:
        player_data = self[player_id]
        assert isinstance(player_data, UnoPlayerData)

        if player_data.is_me:
            return await bot.me()

        member = await bot.get_chat_member(chat_id, player_id)
        return member.user

    @classmethod
    async def setup(
            cls,
            state: FSMContext,
            deck: UnoDeck,
            player_ids: list[int]
    ) -> "UnoPlayers":
        playing = {
            player_id: await UnoPlayerData.setup(state, player_id, list(deck(7)))
            for player_id in player_ids
        }

        current_index = randrange(len(player_ids))

        return cls(playing, current_index)

    def restart(self, deck: UnoDeck):
        """Return finished players, clear finished list and set cards for playing"""

        self.playing.update(self.finished)
        self.finished.clear()

        for player_data in self.playing.values():
            player_data.cards = list(deck(7))

        self._current_index = randrange(len(self.playing))

    async def clear(self, state: FSMContext):
        """Clear playing and finished players"""

        for player_id, player_data in (self.playing | self.finished).items():
            await player_data.clear(state, player_id)
