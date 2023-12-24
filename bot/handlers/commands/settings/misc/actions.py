from enum import Enum

from aiogram.utils.i18n import gettext as _


class SettingsActions(str, Enum):
    COMMAND = 'command'
    LOCALE = 'locale'
    CHANCE = 'chance'
    ACCURACY = 'accuracy'
    GPT = 'gpt'
    RECORD = 'record'

    BACK = 'back'

    @property
    def keyboard(self) -> str:
        match self:
            case self.COMMAND:
                return _('Add command')
            case self.LOCALE:
                return _('Change language')
            case self.CHANCE:
                return _('Change generation chance')
            case self.ACCURACY:
                return _('Change generation accuracy')
            case self.GPT:
                return _('Change GPT options')
            case self.RECORD:
                return _('Change record policy')

            case self.BACK:
                return _("Back")

        raise TypeError(f"SettingsActions: unexpected settings action: {self}")
