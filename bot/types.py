from datetime import datetime, timedelta
from aiogram import types, html


class CustomMessage(types.Message):
    def date_check(self):
        return datetime.now(tz=self.date.tzinfo) - self.date > timedelta(seconds=15)

    def answer(self, **kwargs):
        if self.date_check():
            return super().reply(**kwargs)
        return super().answer(**kwargs)

    def answer_sticker(self, **kwargs):
        if self.date_check():
            return super().reply_sticker(**kwargs)
        return super().answer_sticker(**kwargs)

    def answer_voice(self, **kwargs):
        if self.date_check():
            return super().reply_voice(**kwargs)
        return super().answer_voice(**kwargs)


class CustomUser(types.User):
    def __str__(self):
        return self.mention_html(self.first_name)


class CustomChat(types.Chat):
    def __str__(self):
        return html.quote(self.title)


def setup():
    types.Message = CustomMessage
    types.User = CustomUser
    types.Chat = CustomChat
