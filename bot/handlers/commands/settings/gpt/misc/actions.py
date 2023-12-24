from enum import Enum

from aiogram.utils.i18n import gettext as _


class GPTOptionsActions(str, Enum):
    MAX_TOKENS = 'max_tokens'
    TEMPERATURE = 'temperature'

    BACK = 'back'

    @property
    def keyboard(self) -> str:
        match self:
            case self.MAX_TOKENS:
                return _('Change maximum tokens')
            case self.TEMPERATURE:
                return _('Change temperature')

            case self.BACK:
                return _("Back")

        raise TypeError(f"GPTOptionsActions: unexpected settings action: {self}")

    @property
    def description(self) -> str:
        match self:
            case self.MAX_TOKENS:
                return _("the limit on the number of tokens used for single completion generation")
            case self.TEMPERATURE:
                return _("affects creativity and randomness of responses")

        raise TypeError(f'GPTOptionsActions: unexpected settings action: {self}')
