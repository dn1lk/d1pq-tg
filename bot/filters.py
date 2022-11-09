from typing import Union

from aiogram import Bot, types, filters


class LevenshteinFilter(filters.BaseFilter):
    def __init__(self, lev: set[str], lev_ignore_case: bool = True):
        self.lev: set[str] = lev
        self.ignore_case: bool = lev_ignore_case

    @staticmethod
    def lev_distance(lev: str, text: str):
        if lev == text:
            return 0

        rows = len(lev) + 1
        cols = len(text) + 1

        if not lev:
            return cols - 1
        if not text:
            return rows - 1

        cur = range(cols)
        for row in range(1, rows):
            prev, cur = cur, [row] + [0] * (cols - 1)
            for col in range(1, cols):
                deletion = prev[col] + 1
                insertion = cur[col - 1] + 1
                edit = prev[col - 1] + (0 if lev[row - 1] == text[col - 1] else 1)
                cur[col] = min(edit, deletion, insertion)

        return cur[-1]

    async def __call__(self, obj: Union[types.Message, types.InlineQuery, types.Poll]) -> bool:
        match obj:
            case types.Message:
                text = obj.text or obj.caption
                if not text and obj.poll:
                    text = obj.poll.question
            case types.InlineQuery:
                text = obj.query
            case types.Poll:
                text = obj.question
            case _:
                return False

        if not text:
            return False

        if self.ignore_case:
            text = text.lower()

        return any(self.lev_distance(lev, text) <= len(lev) / 3 for lev in self.lev)


class AdminFilter(filters.BaseFilter):
    def __init__(self, is_admin: bool = True) -> None:
        self.is_admin: bool = is_admin

    async def __call__(self, obj: Union[types.Message, types.CallbackQuery], bot: Bot, owner_id: int) -> bool:
        match obj:
            case types.Message:
                chat_id = obj.chat.id
            case types.CallbackQuery:
                chat_id = obj.message.chat.id
            case _:
                return False

        if obj.from_user.id in (chat_id, owner_id) or
                obj.from_user.id in (member.user.id for member in await bot.get_chat_administrators(chat_id)):
            return self.is_admin

        return not self.is_admin
