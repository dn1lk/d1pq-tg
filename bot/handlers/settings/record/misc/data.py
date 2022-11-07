from enum import Enum

from aiogram.utils.i18n import gettext as _

from bot.utils.database.context import DataBaseContext


class RecordData(int, Enum):
    messages = 1
    members = 2

    @property
    def word(self):
        words = {
            self.messages: _("Messages"),
            self.members: _("Members"),
        }

        return words.get(self)

    async def switch(self, dp: DataBaseContext) -> int:
        item = await dp.get_data(self.name)

        switches = {
            self.messages: item != ['disabled'],
            self.members: item,
        }

        return 1 if switches.get(self) else 0
