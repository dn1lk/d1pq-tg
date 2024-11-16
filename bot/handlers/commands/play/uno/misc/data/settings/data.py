from dataclasses import dataclass
from typing import Self

from aiogram import types

from .additions import UnoAdd, UnoAddState
from .difficulties import UnoDifficulty
from .modes import UnoMode


@dataclass(frozen=True)
class UnoSettings:
    difficulty: UnoDifficulty
    mode: UnoMode

    stacking: UnoAddState
    seven_0: UnoAddState
    jump_in: UnoAddState

    @classmethod
    def extract(cls, message: types.Message) -> Self:
        return cls(
            difficulty=UnoDifficulty.extract(message),
            mode=UnoMode.extract(message),
            stacking=UnoAdd.STACKING.extract(message),
            seven_0=UnoAdd.SEVEN_0.extract(message),
            jump_in=UnoAdd.JUMP_IN.extract(message),
        )
