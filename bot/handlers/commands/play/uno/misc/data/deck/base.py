from dataclasses import dataclass, field
from random import choice, sample
from typing import Generator

from aiogram import Bot, types

from .card import UnoCard
from .colors import UnoColors
from .emoji import UnoEmoji


@dataclass
class UnoDeck:
    cards_in: list[UnoCard]
    last_cards: list[UnoCard] = field(default_factory=list)

    def __post_init__(self):
        if not self.last_cards:
            self.last_cards.append(choice([card for card in self.cards_in if card.emoji is not UnoEmoji.DRAW_FOUR]))

    def __getitem__(self, count: int) -> Generator[UnoCard, None, None]:
        """Get cards from the deck"""

        for card in sample(self.cards_in, k=count):
            self.cards_in.remove(card)
            yield card

    def __delitem__(self, card: UnoCard):
        """Remove card from the deck"""

        self.cards_in.remove(card)

    @property
    def last_card(self) -> UnoCard:
        return self.last_cards[-1]

    @last_card.setter
    def last_card(self, card: UnoCard):
        """Add card to the deck"""

        self.cards_in.append(card)
        self.last_cards.append(card)

        if len(self.last_cards) > 3:
            self.last_cards = self.last_cards[-3:]

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

        cards_in = list(get_cards(await bot.get_sticker_set('uno_by_d1pq_bot')))
        cards_in.extend(cards_in[-2:])
        cards_in.extend(cards_in[4:])

        return cls(cards_in)
