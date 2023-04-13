from datetime import datetime, timedelta

from aiogram.types import Message


def date_check(date: datetime):
    return datetime.now(tz=date.tzinfo) - date > timedelta(seconds=15)


def wrapper(answer_func, reply_func):
    def wrapped(self: Message, *args, **kwargs):
        if date_check(self.date):
            return reply_func(self, *args, **kwargs)
        return answer_func(self, *args, **kwargs)

    return wrapped


def setup():
    Message.answer = wrapper(Message.answer, Message.reply)
    Message.answer_sticker = wrapper(Message.answer_sticker, Message.reply_sticker)
    Message.answer_poll = wrapper(Message.answer_poll, Message.reply_poll)
