from enum import Enum

from aiogram.utils.i18n import gettext as _


class RecordActions(str, Enum):
    MESSAGES = 'messages'
    STICKERS = 'stickers'
    MEMBERS = 'members'

    DELETE = 'delete'

    @property
    def keyboard(self) -> str:
        match self:
            case self.MESSAGES:
                return _("Messages")
            case self.STICKERS:
                return _("Stickers")
            case self.MEMBERS:
                return _("Members")
            case self.DELETE:
                return _('Delete all records')

        raise TypeError(f'RecordData: unexpected record data: {self}')

    @property
    def description(self) -> str:
        match self:
            case self.MESSAGES:
                return _("to generate messages")
            case self.STICKERS:
                return _("to generate stickers")
            case self.MEMBERS:
                return _("to execute /who command")

        raise TypeError(f'RecordData: unexpected record data: {self}')
