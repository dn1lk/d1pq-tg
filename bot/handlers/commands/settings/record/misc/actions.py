from enum import Enum

from aiogram.utils.i18n import gettext as _

from bot.utils import database


class RecordActions(str, Enum):
    MESSAGES = 'messages'
    MEMBERS = 'members'

    DELETE = 'delete'

    @property
    def keyboard(self) -> str:
        match self:
            case self.MESSAGES:
                return _("Messages")
            case self.MEMBERS:
                return _("Members")
            case self.DELETE:
                return _('Delete all records')

        raise TypeError(f'RecordData: unexpected record data: {self}')

    @property
    def description(self) -> str:
        match self:
            case self.MESSAGES:
                return _("for more accurate and relevant message generation")
            case self.MEMBERS:
                return _("to execute /who command")

        raise TypeError(f'RecordData: unexpected record data: {self}')

    async def switch(self, dp: database.SQLContext, chat_id: int) -> bool:
        item = await dp[self.value].get(chat_id)

        match self:
            case self.MESSAGES:
                return item != ['disabled']
            case self.MEMBERS:
                return item is not None

        raise TypeError(f'RecordData: unexpected record data: {self}')
