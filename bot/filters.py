from aiogram import Bot, types
from aiogram.filters import *


class LevenshteinFilter(BaseFilter):
    def __init__(self, *lev, ignore_case: bool = True):
        self.lev: tuple = lev
        self.ignore_case: bool = ignore_case

    async def __call__(self, obj: types.Message | types.InlineQuery | types.Poll) -> bool:
        match obj:
            case types.Message():
                text = obj.text or obj.caption or (obj.poll.question if obj.poll else None)
            case types.InlineQuery():
                text = obj.query
            case types.Poll():
                text = obj.question
            case _:
                raise TypeError('LevenshteinFilter: incorrect event type')

        if text is None:
            return False

        if self.ignore_case:
            text = text.lower()

        from Levenshtein import ratio
        return any(ratio(i, t) > 0.7 for i in self.lev for t in text.split())


class AdminFilter(BaseFilter):
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

        if obj.from_user.id in (chat_id, owner_id):
            return self.is_admin
        if any(obj.from_user.id == member.user.id for member in await bot.get_chat_administrators(chat_id)):
            return self.is_admin
        return not self.is_admin
