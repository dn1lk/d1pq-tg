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


class UnoBot:
    def __init__(self, message: types.Message, bot: Bot, data: UnoData):
        self.message: types.Message = message
        self.bot: Bot = bot

        self.data: UnoData = data

    def __str__(self):
        return 'uno' + ':' + str(self.message.chat.id) + ':' + 'bot'

    def get_color(self):
        self.data.current_card.color = choice(self.data.users[self.bot.id]).color
        return _("I choice {emoji} {color}.").format(
            emoji=self.data.current_card.color.value,
            color=self.data.current_card.color.get_color_name(),
        )

    def get_cards(self) -> tuple:
        def get():
            for card in self.data.users[self.bot.id]:
                card, accept, decline = self.data.card_filter(self.bot.id, card)
                if accept:
                    yield card, accept

        if self.bot.id in self.data.users:
            return tuple(get())

    async def gen(self, state: FSMContext, cards: tuple | None):
        async with ChatActionSender.choose_sticker(chat_id=self.message.chat.id):
            await asyncio.sleep(choice(range(1, 6)) / len(self.data.users))

            from .action import UnoAction

            action_uno = UnoAction(self.message, state, self.data)

            if cards:
                action_uno.data.current_card, accept = choice(cards)
                try:
                    action_uno.message = await action_uno.message.answer_sticker(action_uno.data.current_card.file_id)
                except exceptions.TelegramRetryAfter as retry:
                    await asyncio.sleep(retry.retry_after)
                    action_uno.message = await retry.method

                try:
                    await action_uno.prepare(
                        action_uno.data.current_card,
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
                except ValueError:
                    return await action_uno.message.delete()
                except UnoNoUsersException:
                    await action_uno.end()
            else:
                await action_uno.skip()

    async def uno(self, state: FSMContext):
        async with ChatActionSender.typing(chat_id=self.message.chat.id):
            await asyncio.sleep(choice(range(0, 4)) / len(self.data.users))

            await self.message.answer(str(UNO), reply_markup=types.ReplyKeyboardRemove())

            await state.update_data(uno=self.data.dict())

    async def uno_user(self, state: FSMContext):
        await asyncio.sleep(choice(range(2, 8)) / len(self.data.users))

        await self.data.add_card(self.bot, self.message.chat.id, self.message.from_user.id, 2)
        await self.message.answer(
            get_username(self.message.from_user) + ", " + str(UNO),
            reply_markup=types.ReplyKeyboardRemove())

        await state.update_data(uno=self.data.dict())
