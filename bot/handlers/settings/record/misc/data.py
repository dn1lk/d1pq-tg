from enum import Enum, auto

from aiogram.utils.i18n import gettext as _

from bot.utils.database.context import DataBaseContext


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
            case self.DELETE:
                return _('Delete all records')

    async def switch(self, dp: DataBaseContext) -> int | None:
        item = await dp.get_data(self.name.lower())

        match self:
            case self.MESSAGES:
                return int(item != ['disabled'])
            case self.MEMBERS:
                return int(item)
