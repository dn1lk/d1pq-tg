from enum import Enum

from aiogram.utils.i18n import gettext as _


class SettingsActions(str, Enum):
    COMMAND = "command"
    LOCALE = "locale"
    CHANCE = "chance"
    ACCURACY = "accuracy"
    GPT = "gpt"
    RECORD = "record"

    BACK = "back"

    @property
    def keyboard(self) -> str:
        match self:
            case self.COMMAND:
                keyboard = _("Add command")
            case self.LOCALE:
                keyboard = _("Change language")
            case self.CHANCE:
                keyboard = _("Change generation chance")
            case self.ACCURACY:
                keyboard = _("Change generation accuracy")
            case self.GPT:
                keyboard = _("Change GPT options")
            case self.RECORD:
                keyboard = _("Change record policy")

            case self.BACK:
                keyboard = _("Back")

            case _:
                msg = f"{self.__class__.__name__}: unexpected value: {self}"
                raise TypeError(msg)

        return keyboard
