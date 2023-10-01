from datetime import datetime, timedelta, timezone

from aiogram.types import Message


def wrapper(answer_func, reply_func):
    def wrapped(self: Message, *args, **kwargs):
        if datetime.now(tz=timezone(self.date.tzinfo.utcoffset(self.date))) - self.date > timedelta(seconds=15):
            return reply_func(self, *args, **kwargs)
        return answer_func(self, *args, **kwargs)

    return wrapped


def setup():
    Message.answer = wrapper(Message.answer, Message.reply)
    Message.answer_sticker = wrapper(Message.answer_sticker, Message.reply_sticker)
    Message.answer_poll = wrapper(Message.answer_poll, Message.reply_poll)
