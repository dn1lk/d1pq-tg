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
    player_id: int

    cards: list[UnoCard]
    cards_played: int = 0

    points: int = 0
    is_me: bool = False

    def __eq__(self, user_id: int) -> bool:
        return self.player_id == user_id

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

    @property
    def card_values(self) -> int:
        return sum(card for card in self.cards)

    async def get_user(self, bot: Bot, chat_id: int) -> types.User:
        if self.player_id == bot.id:
            return await bot.me()

        member = await bot.get_chat_member(chat_id, self.player_id)
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
        key = self.get_key(state.key.bot_id, self.player_id)

        storage = state.storage
        await storage.set_state(state.bot, key)
        await storage.set_data(state.bot, key, {})


@dataclass
class UnoPlayers:
    _players_in: list[UnoPlayer]
    _current_index: int = None

    players_finished: list[UnoPlayer] = field(default_factory=list)

    def __post_init__(self):
        if self._current_index is None:
            self._current_index = randrange(len(self._players_in))

    def __len__(self):
        """Get number of players"""

        return len(self._players_in)

    def __iter__(self):
        """Iter players"""

        return self._players_in.__iter__()

    def __getitem__(self, user_id: int) -> UnoPlayer | None:
        """Get player"""

        for player in self._players_in:
            if player == user_id:
                return player

    async def add_player(self, state: FSMContext, user_id: int, cards: list[UnoCard]):
        """Add player"""

        if self[user_id]:
            raise errors.UnoExistedPlayer()
        elif len(self) == 10:
            raise errors.UnoMaxPlayers()

        player = await UnoPlayer.setup(state, user_id, cards)
        self._players_in.append(player)

    async def kick_player(self, state: FSMContext, deck: UnoDeck, player: UnoPlayer):
        """Remove player and clear him data"""

        deck.cards_in.extend(player.cards)
        self._players_in.remove(player)

        await player.clear(state)

    def finish_player(self, deck: UnoDeck, player: UnoPlayer):
        """Remove player and add to finishers"""

        deck.cards_in.extend(player.cards)
        self._players_in.remove(player)

        player.points += sum(player.card_values for player in self._players_in)
        self.players_finished.append(player)

    def __rshift__(self, number: int) -> UnoPlayer:
        """Next player by number"""

        return self._players_in[(self._current_index + number) % len(self._players_in)]

    def __lshift__(self, number: int) -> UnoPlayer:
        """Previous player by number"""

        return self._players_in[(self._current_index - number) % len(self._players_in)]

    @property
    def current_player(self) -> UnoPlayer:
        return self._players_in[self._current_index]

    @current_player.setter
    def current_player(self, player: UnoPlayer):
        self._current_index = self._players_in.index(player)

    @classmethod
    async def setup(cls, state: FSMContext, deck: UnoDeck, *user_ids: int) -> "UnoPlayers":
        return cls([await UnoPlayer.setup(state, user_id, list(deck[7])) for user_id in user_ids])

    def restart(self, deck: UnoDeck):
        for player in self._players_in.copy():
            self.finish_player(deck, player)

        deck.cards_in.extend(sum([player.cards for player in self._players_in], []))

        for player in self._players_in:
            player.cards = list(deck[7])

    async def clear(self, state: FSMContext, deck: UnoDeck):
        for player in self._players_in.copy():
            self.finish_player(deck, player)

        for player in self.players_finished:
            await player.clear(state)
