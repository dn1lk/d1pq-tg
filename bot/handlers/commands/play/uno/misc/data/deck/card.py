from dataclasses import dataclass, replace

from .colors import UnoColors
from .emoji import UnoEmoji


@dataclass(frozen=True)
class UnoCard:
    file_unique_id: str
    file_id: str
    emoji: UnoEmoji

    color: UnoColors
    cost: int

    def __iadd__(self, card: "UnoCard"):
        self.cost += card.cost

    def __eq__(self, card) -> bool:
        return self.file_unique_id == card.file_unique_id

    def replace_color(self, color: UnoColors) -> "UnoCard":
        return replace(self, color=color)
