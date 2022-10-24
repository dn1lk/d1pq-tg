import asyncio
from random import choice

from aiogram import Bot, types, exceptions
from aiogram.fsm.context import FSMContext
from aiogram.utils.chat_action import ChatActionSender
from aiogram.utils.i18n import gettext as _

from bot.handlers import get_username
from .core import pre, finish, pass_turn
from .data import UnoData
from .exceptions import UnoNoUsersException
from ..settings import UnoDifficulty

UNO = "UNO!"


class UnoBot:
    def __init__(self, message: types.Message, bot: Bot, data: UnoData):
        self.message: types.Message = message
        self.bot: Bot = bot

        self.data: UnoData = data

    def __str__(self):
        return f'uno:{self.message.chat.id}:bot'

    def get_color(self):
        cards = self.data.users[self.bot.id].cards

        if self.data.settings.difficulty is UnoDifficulty.hard:
            colors = tuple(card.color for card in cards)
            self.data.current_card.color = max(set(colors), key=colors.count)
        else:
            self.data.current_card.color = choice(cards).color

        self.data.special_color()

        return _("I choice {color}.").format(color=self.data.current_card.color.word)

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
            await asyncio.sleep(choice(range(1, 6)) / len(self.data.users) * self.data.settings.difficulty.value)
            self.data: UnoData = UnoData(**(await state.get_data())['uno'])

            try:
                if cards:
                    self.data.current_card, accept = choice(cards)
                    print(accept)
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
                                    _("I still have cards in my hand."),
                                    _("Curious, but I know all the hands in the game... I dealt them."),
                                    _("Maybe I can even win this game!"),
                                    _("Oh, I don't envy the next player..."),
                                    _("Br-b. Ah. Yes. No. ..."),
                                    _("Oh-oh, this card fell into this chat by itself..."),
                                )
                            )
                        )

                    except UnoNoUsersException:
                        await finish(self.message, self.data, state)
                    except asyncio.CancelledError:
                        self.data = UnoData(**(await state.get_data())['uno'])

                        await self.message.delete()
                        await self.message.answer(self.data.add_card(self.bot, self.message.from_user))

                        await state.update_data(uno=self.data.dict())
                else:
                    await pass_turn(self.message, self.data, state)

            except exceptions.TelegramRetryAfter as retry:
                await asyncio.sleep(retry.retry_after)
                self.message = await retry.method

    async def uno(self, _):
        try:
            async with ChatActionSender.typing(chat_id=self.message.chat.id):
                await asyncio.sleep(choice(range(0, 4)) / len(self.data.users) * self.data.settings.difficulty.value)
                await self.message.edit_text(str(UNO))
        except asyncio.CancelledError:
            await self.message.delete_reply_markup()

    async def uno_user(self, state: FSMContext):
        try:
            async with ChatActionSender.typing(chat_id=self.message.chat.id):
                await asyncio.sleep(choice(range(1, 8)) / len(self.data.users) * self.data.settings.difficulty.value)
                self.data: UnoData = UnoData(**(await state.get_data())['uno'])

                self.data.add_card(self.bot, self.message.entities[0].user, 2)
                await state.update_data(uno=self.data.dict())

                await self.message.edit_text(get_username(self.message.entities[0].user) + ", " + str(UNO))
        except asyncio.CancelledError:
            await self.message.delete_reply_markup()
