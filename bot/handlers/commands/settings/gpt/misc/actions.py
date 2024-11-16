from enum import Enum

from aiogram.utils.i18n import gettext as _


class GPTOptionsActions(str, Enum):
    MAX_TOKENS = "max_tokens"
    TEMPERATURE = "temperature"

    BACK = "back"

    @property
    def keyboard(self) -> str:
        match self:
            case self.MAX_TOKENS:
                keyboard = _("Change maximum tokens")
            case self.TEMPERATURE:
                keyboard = _("Change temperature")

            case self.BACK:
                keyboard = _("Back")

            case _:
                msg = f"{self.__class__.__name__}: unexpected value: {self}"
                raise TypeError(msg)

        return keyboard

    @property
    def description(self) -> str:
        match self:
            case self.MAX_TOKENS:
                description = _("the limit on the number of tokens used for single completion generation")
            case self.TEMPERATURE:
                description = _("affects creativity and randomness of responses")
            case _:
                msg = f"{self.__class__.__name__}: unexpected value: {self}"
                raise TypeError(msg)

        return description
