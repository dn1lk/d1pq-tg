from datetime import datetime, timedelta
from re import sub
from typing import Optional, Union

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


def text_check(text: str) -> str:
    if text:
        text = (text[0].upper() + text[1:]).strip()

        sub(r'[^!?:.()]$', '.', text)

        if text[-1] not in '!?:.()>':
            text += '.'

    return text


def date_check(date, message_id) -> int:
    if datetime.now(tz=date.tzinfo) - date > timedelta(seconds=15):
        return message_id


def setup():
    Message.answer = CustomMessage.answer
    Message.reply = CustomMessage.reply

    Message.answer_sticker = CustomMessage.answer_sticker
    Message.answer_voice = CustomMessage.answer_voice


class CustomMessage(Message):
    def answer(
            self,
            text: str,
            parse_mode: Optional[str] = UNSET,
            disable_web_page_preview: Optional[bool] = None,
            disable_notification: Optional[bool] = None,
            reply_markup: Optional[
                Union[InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove, ForceReply]
            ] = None,
    ) -> SendMessage:
        return SendMessage(
            chat_id=self.chat.id,
            text=text_check(text),
            parse_mode=parse_mode,
            disable_web_page_preview=disable_web_page_preview,
            disable_notification=disable_notification,
            reply_to_message_id=date_check(self.date, self.message_id),
            reply_markup=reply_markup,
        )

    def reply(
            self,
            text: str,
            parse_mode: Optional[str] = UNSET,
            disable_web_page_preview: Optional[bool] = None,
            disable_notification: Optional[bool] = None,
            allow_sending_without_reply: Optional[bool] = None,
            reply_markup: Optional[
                Union[InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove, ForceReply]
            ] = None,
    ) -> SendMessage:
        return SendMessage(
            chat_id=self.chat.id,
            text=text_check(text),
            parse_mode=parse_mode,
            disable_web_page_preview=disable_web_page_preview,
            disable_notification=disable_notification,
            reply_to_message_id=self.message_id,
            allow_sending_without_reply=allow_sending_without_reply,
            reply_markup=reply_markup,
        )

    def answer_sticker(
            self,
            sticker: Union[InputFile, str],
            disable_notification: Optional[bool] = None,
            reply_markup: Optional[
                Union[InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove, ForceReply]
            ] = None,
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
            voice: Union[InputFile, str],
            caption: Optional[str] = None,
            parse_mode: Optional[str] = UNSET,
            duration: Optional[int] = None,
            disable_notification: Optional[bool] = None,
            reply_markup: Optional[
                Union[InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove, ForceReply]
            ] = None,
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
