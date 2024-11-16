from enum import Enum

from aiogram.utils.i18n import gettext as _


class RecordActions(str, Enum):
    MESSAGES = "messages"
    STICKERS = "stickers"
    MEMBERS = "members"

    DELETE = "delete"

    @property
    def keyboard(self) -> str:
        match self:
            case self.MESSAGES:
                keyboard = _("Messages")
            case self.STICKERS:
                keyboard = _("Stickers")
            case self.MEMBERS:
                keyboard = _("Members")
            case self.DELETE:
                keyboard = _("Delete all records")
            case _:
                msg = f"{self.__class__.__name__}: unexpected value: {self}"
                raise TypeError(msg)

        return keyboard

    @property
    def description(self) -> str:
        match self:
            case self.MESSAGES:
                description = _("to generate messages")
            case self.STICKERS:
                description = _("to generate stickers")
            case self.MEMBERS:
                description = _("to execute /who command")
            case _:
                msg = f"{self.__class__.__name__}: unexpected value: {self}"
                raise TypeError(msg)

        return description
