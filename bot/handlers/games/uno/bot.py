import asyncio
from random import choice

from aiogram import Bot, types, exceptions
from aiogram.fsm.context import FSMContext
from aiogram.utils.chat_action import ChatActionSender
from aiogram.utils.i18n import gettext as _

from bot.handlers import get_username
from . import UNO
from .data import UnoData
from .exceptions import UnoNoUsersException
from .process import pre, finish, skip


class UnoBot:
    def __init__(self, message: types.Message, bot: Bot, data: UnoData):
        self.message: types.Message = message
        self.bot: Bot = bot

        self.data: UnoData = data

    def __str__(self):
        return 'uno' + ':' + str(self.message.chat.id) + ':' + 'bot'

    def get_color(self):
        self.data.special_color()
        cards = self.data.users[self.bot.id].cards

        if self.data.bot_speed > 0.5:
            colors = tuple(card.color for card in cards)
            self.data.current_card.color = max(set(colors), key=colors.count)
        else:
            self.data.current_card.color = choice(cards).color

        return _("I choice {emoji} {color}.").format(
            emoji=self.data.current_card.color.value,
            color=self.data.current_card.color.name,
        )

    def get_cards(self) -> tuple:
        def get():
            for card in self.data.users[self.bot.id].cards:
                accept, decline = self.data.filter_card(self.bot.id, card)
                if accept:
                    yield card, accept

        if self.bot.id in self.data.users:
            return tuple(get())

    async def gen(self, state: FSMContext, cards: tuple | None):
        async with ChatActionSender.choose_sticker(chat_id=self.message.chat.id):
            await asyncio.sleep(choice(range(1, 6)) / len(self.data.users) / self.data.bot_speed)
            self.data: UnoData = UnoData(**(await state.get_data())['uno'])

            try:
                if cards:
                    self.data.current_card, accept = choice(cards)
                    self.message = await self.message.answer_sticker(self.data.current_card.file_id)

                    try:
                        await pre(
                            self.message,
                            self.data,
                            state,
                            choice(
                                (
                                    _("My move is made."),
                                    _("Expected? But I don't care."),
                                    _("BA-DUM-TSS!"),
                                    _(
                                        "On a scale of 10, rate the quality of this move.\n"
                                        "Where 0 is very good, 10 is excellent"
                                    ),
                                    _("I still have cards in my deck."),
                                    _("Curious, but I know all the cards in the game... I dealt them."),
                                    _("Maybe I can even win this game!"),
                                    _("Oh, I don't envy the next player..."),
                                    _("Br-b. Ah. Yes. No. ..."),
                                    _("Oh-oh, this card fell into this chat by itself..."),
                                )
                            )
                        )

                    except UnoNoUsersException:
                        await finish(self.message, self.data, state)
                else:
                    await skip(self.message, self.data, state)

            except exceptions.TelegramRetryAfter as retry:
                await asyncio.sleep(retry.retry_after)
                self.message = await retry.method

    async def uno(self, _):
        try:
            async with ChatActionSender.typing(chat_id=self.message.chat.id):
                await asyncio.sleep(choice(range(0, 4)) / len(self.data.users) / self.data.bot_speed)
                await self.message.edit_text(str(UNO))
        except asyncio.CancelledError:
            await self.message.delete_reply_markup()

    async def uno_user(self, state: FSMContext):
        try:
            async with ChatActionSender.typing(chat_id=self.message.chat.id):
                await asyncio.sleep(choice(range(1, 8)) / len(self.data.users) / self.data.bot_speed)
                self.data: UnoData = UnoData(**(await state.get_data())['uno'])

                await self.data.add_card(self.bot, self.message.entities[0].user, 2)
                await state.update_data(uno=self.data.dict())

                await self.message.edit_text(get_username(self.message.entities[0].user) + ", " + str(UNO))
        except asyncio.CancelledError:
            await self.message.delete_reply_markup()
