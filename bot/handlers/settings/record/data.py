from enum import Enum, auto

from aiogram.utils.i18n import gettext as _

from ....utils import database


class RecordData(Enum):
    def _generate_next_value_(name, *args):
        return name.lower()

    MESSAGES = auto()
    MEMBERS = auto()

    DELETE = auto()

    @property
    def word(self) -> str | None:
        match self:
            case self.MESSAGES:
                return _("Messages")
            case self.MEMBERS:
                return _("Members")
            case _:
                return _('Delete all records')

    async def switch(self, dp: database.SQLContext, chat_id: int) -> int:
        item = await dp[self.name.lower()].get(chat_id)

        match self:
            case self.MESSAGES:
                return int(item != ['disabled'])
            case self.MEMBERS:
                return int(item is not None)
