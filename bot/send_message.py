from datetime import datetime, timedelta

from aiogram.types import Message


def message_date_check(answer, reply):
    async def wrapper(self, *args, **kwargs):
        if datetime.now(tz=self.date.tzinfo) - self.date > timedelta(seconds=15):
            return await reply(self, *args, **kwargs)
        return await answer(self, *args, **kwargs)

    return wrapper


def setup():
    Message.answer = message_date_check(Message.answer, Message.reply)
    Message.answer_sticker = message_date_check(Message.answer_sticker, Message.reply_sticker)
    Message.answer_voice = message_date_check(Message.answer_voice, Message.reply_voice)
