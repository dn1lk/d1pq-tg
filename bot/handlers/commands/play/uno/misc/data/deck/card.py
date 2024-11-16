from dataclasses import dataclass, replace
from typing import Self

from .colors import UnoColors
from .emoji import UnoEmoji


@dataclass(frozen=True)
class UnoCard:
    file_unique_id: str
    file_id: str
    emoji: UnoEmoji

    color: UnoColors
    cost: int

    def __str__(self) -> str:
        return f"{self.__class__.__name__}(emoji={self.emoji.value}, color={self.color.value})"

    def __add__(self, card: Self) -> int:
        return self.cost + card.cost

    def __radd__(self, cost: int) -> int:
        return self.cost + cost

    def __eq__(self, card: Self) -> bool:  # type: ignore[override]
        return self.file_unique_id == card.file_unique_id

    def replace(self, **kwargs) -> Self:
        """Create UnoCard with another parameter"""

        return replace(self, **kwargs)
