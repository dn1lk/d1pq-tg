from dataclasses import dataclass, field
from random import choice, sample
from typing import Generator

from aiogram import Bot, types

from .card import UnoCard
from .colors import UnoColors
from .emoji import UnoEmoji

STICKER_SET_NAME = 'uno_by_d1pq_bot'


@dataclass
class UnoDeck:
    _cards_in: list[UnoCard]
    _last_cards: list[UnoCard] = field(default_factory=list)

    def __post_init__(self):
        if not self._last_cards:
            self._last_cards.append(choice([card for card in self._cards_in if card.emoji is not UnoEmoji.DRAW_FOUR]))

    def __call__(self, count: int) -> Generator[UnoCard, None, None]:
        """Get cards from the deck"""

        for card in sample(self._cards_in, k=count):
            self._cards_in.remove(card)
            yield card

    def add(self, *cards: UnoCard):
        self._cards_in.extend(cards)

    def __getitem__(self, index: int):
        """Get last card by index"""

        return self._last_cards[index]

    def __setitem__(self, index: int, card: UnoCard):
        """Set last card by index"""

        assert -3 <= index <= 3
        self._last_cards[index] = card

    def __delitem__(self, card: UnoCard):
        """Remove card from the deck"""

        self._cards_in.remove(card)

    def __iter__(self):
        return self._cards_in.__iter__()

    def __len__(self) -> int:
        return len(self._last_cards)

    @property
    def last_card(self) -> UnoCard:
        return self[-1]

    @last_card.setter
    def last_card(self, card: UnoCard):
        """Add card to the deck"""

        self._cards_in.append(card)
        self._last_cards.append(card)

        if len(self) > 3:
            del self._last_cards[0]

        assert len(self) <= 3

    @classmethod
    async def setup(cls, bot: Bot) -> "UnoDeck":
        def get_cards(sticker_set: types.StickerSet):
            stickers = sticker_set.stickers
            colors = tuple(UnoColors)

            for enum, sticker in enumerate(stickers[:40]):
                yield UnoCard(
                    file_unique_id=sticker.file_unique_id,
                    file_id=sticker.file_id,
                    emoji=UnoEmoji(sticker.emoji),
                    color=colors[enum % 4],
                    cost=enum // 4
                )

            for enum, sticker in enumerate(stickers[40:-3]):
                yield UnoCard(
                    file_unique_id=sticker.file_unique_id,
                    file_id=sticker.file_id,
                    emoji=UnoEmoji(sticker.emoji),
                    color=colors[enum % 4],
                    cost=20
                )

            for sticker in stickers[-3:-1]:
                yield UnoCard(
                    file_unique_id=sticker.file_unique_id,
                    file_id=sticker.file_id,
                    emoji=UnoEmoji(sticker.emoji),
                    color=UnoColors.BLACK,
                    cost=50
                )

        cards_in = [*get_cards(await bot.get_sticker_set(STICKER_SET_NAME))]
        cards_in.extend(cards_in[-2:])  # double black cards
        cards_in.extend(cards_in[4:])  # double non-0 cards

        assert len(cards_in) == 108, 'Wrong len of stickers in sticker pack'

        return cls(cards_in)
