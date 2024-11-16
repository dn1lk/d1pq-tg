from collections.abc import Callable
from datetime import datetime, timedelta, timezone
from functools import wraps

from aiogram.types import Message


def _wrapper(answer_func: Callable, reply_func: Callable):
    @wraps(answer_func)
    def wrapped(self: Message, *args, **kwargs):
        offset = self.date.tzinfo.utcoffset(self.date)
        if offset and datetime.now(tz=timezone(offset)) - self.date > timedelta(seconds=15):
            return reply_func(self, *args, **kwargs)

        return answer_func(self, *args, **kwargs)

    return wrapped


def setup() -> None:
    Message.answer = _wrapper(Message.answer, Message.reply)
    Message.answer_sticker = _wrapper(Message.answer_sticker, Message.reply_sticker)
    Message.answer_poll = _wrapper(Message.answer_poll, Message.reply_poll)
