from datetime import datetime, timedelta

from aiogram.methods import SendMessage, SendVoice, SendSticker
from aiogram.types import (
    Message,
    ForceReply,
    ReplyKeyboardRemove,
    ReplyKeyboardMarkup,
    InlineKeyboardMarkup,
    UNSET,
    InputFile,
)


def date_check(date, message_id) -> int:
    if datetime.now(tz=date.tzinfo) - date > timedelta(seconds=15):
        return message_id


class CustomMessage(Message):
    def answer(
            self,
            text: str,
            parse_mode: str = UNSET,
            disable_web_page_preview: bool = None,
            disable_notification: bool = None,
            reply_markup: InlineKeyboardMarkup | ReplyKeyboardMarkup | ReplyKeyboardRemove | ForceReply = None,
    ) -> SendMessage:
        return SendMessage(
            chat_id=self.chat.id,
            text=text,
            parse_mode=parse_mode,
            disable_web_page_preview=disable_web_page_preview,
            disable_notification=disable_notification,
            reply_to_message_id=date_check(self.date, self.message_id),
            reply_markup=reply_markup,
        )

    def answer_sticker(
            self,
            sticker: InputFile | str,
            disable_notification: bool = None,
            reply_markup: InlineKeyboardMarkup | ReplyKeyboardMarkup | ReplyKeyboardRemove | ForceReply = None,
    ) -> SendSticker:
        return SendSticker(
            chat_id=self.chat.id,
            sticker=sticker,
            disable_notification=disable_notification,
            reply_to_message_id=date_check(self.date, self.message_id),
            reply_markup=reply_markup,
        )

    def answer_voice(
            self,
            voice: InputFile | str,
            caption: str = None,
            parse_mode: str = UNSET,
            duration: int = None,
            disable_notification: bool = None,
            reply_markup: InlineKeyboardMarkup | ReplyKeyboardMarkup | ReplyKeyboardRemove | ForceReply = None,
    ) -> SendVoice:
        return SendVoice(
            chat_id=self.chat.id,
            voice=voice,
            caption=caption,
            parse_mode=parse_mode,
            duration=duration,
            disable_notification=disable_notification,
            reply_to_message_id=date_check(self.date, self.message_id),
            reply_markup=reply_markup,
        )


def setup():
    Message.answer = CustomMessage.answer
    Message.answer_sticker = CustomMessage.answer_sticker
    Message.answer_voice = CustomMessage.answer_voice
