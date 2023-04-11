from dataclasses import dataclass

from .colors import UnoColors
from .emoji import UnoEmoji


@dataclass
class UnoCard:
    file_unique_id: str
    file_id: str
    emoji: UnoEmoji

    color: UnoColors
    cost: int

    def __add__(self, card: "UnoCard") -> int:
        return self.cost + card.cost

    def __eq__(self, card) -> bool:
        return self.file_unique_id == card.file_unique_id
