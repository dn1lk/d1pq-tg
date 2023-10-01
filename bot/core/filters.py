from aiogram import Bot, types
from aiogram.filters import *

from handlers.commands.settings.commands.misc.filter import CustomCommand

Command = CustomCommand


class Levenshtein(BaseFilter):
    def __init__(self, *lev, ignore_case: bool = True):
        self.lev: tuple = lev
        self.ignore_case: bool = ignore_case

    async def __call__(self, event: types.Message) -> bool:
        text = event.text or event.caption or (event.poll.question if event.poll else None)

        if text is None:
            return False

        if self.ignore_case:
            text = text.lower()

        text = text.split()

        from Levenshtein import ratio
        return any(ratio(i, t) > 0.7 for i in self.lev for t in text)


class IsAdmin(BaseFilter):
    def __init__(self, is_admin: bool = True):
        self.is_admin: bool = is_admin

    async def __call__(self, obj: types.Message | types.CallbackQuery, bot: Bot, owner_id: int) -> bool:
        match obj:
            case types.Message():
                chat_id = obj.chat.id
            case types.CallbackQuery():
                chat_id = obj.message.chat.id
            case _:
                raise TypeError('AdminFilter: incorrect event type')

        if (
                obj.from_user.id in (chat_id, owner_id)
                or any(obj.from_user.id == member.user.id for member in await bot.get_chat_administrators(chat_id))
        ):
            return self.is_admin
        return not self.is_admin


class IsMentioned(BaseFilter):
    async def __call__(self, obj: types.Message, bot: Bot, owner_id: int) -> bool:
        if obj.entities:
            for entity in obj.entities:
                if entity.user and entity.user.id == bot.id:
                    return True
        return False
