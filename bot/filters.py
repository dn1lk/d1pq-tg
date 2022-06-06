from typing import Union, Sequence

from aiogram import Bot, types, filters


class LevenshteinFilter(filters.BaseFilter):
    lev: Union[Sequence[filters.text.TextType], filters.text.TextType]
    lev_ignore_case: bool = True

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
        if isinstance(obj, types.Message):
            text = obj.text or obj.caption
            if not text and obj.poll:
                text = obj.poll.question
        elif isinstance(obj, types.InlineQuery):
            text = obj.query
        elif isinstance(obj, types.Poll):
            text = obj.question
        else:
            return False

        if not text:
            return False

        if self.lev_ignore_case:
            text = text.lower()

        return any(self.lev_distance(lev, text) <= len(lev) / 3 for lev in self.lev)


class AdminFilter(filters.BaseFilter):
    is_admin: bool = True

    async def __call__(self, obj: Union[types.Message, types.CallbackQuery], bot: Bot) -> bool:
        if isinstance(obj, types.Message):
            chat_id = obj.chat.id
        elif isinstance(obj, types.CallbackQuery):
            chat_id = obj.message.chat.id
        else:
            return False

        if obj.from_user.id in (chat_id, bot.owner_id) or \
                obj.from_user.id in map(lambda user: user.user.id, await bot.get_chat_administrators(chat_id)):
            return self.is_admin
        else:
            return not self.is_admin
