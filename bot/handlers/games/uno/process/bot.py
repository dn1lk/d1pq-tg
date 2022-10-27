import asyncio
from random import choice

from aiogram import types, exceptions
from aiogram.fsm.context import FSMContext
from aiogram.utils.chat_action import ChatActionSender
from aiogram.utils.i18n import gettext as _

from .data import UnoData
from ..settings import UnoDifficulty

UNO = "UNO!"


class UnoBot:
    def __init__(self, message: types.Message, state: FSMContext, data: UnoData):
        self.message: types.Message = message
        self.state: FSMContext = state

        self.data: UnoData = data

    def __str__(self):
        return f'uno:{self.message.chat.id}'

    def gen_color(self):
        cards = self.data.users[self.state.bot.id].cards

        if self.data.settings.difficulty is UnoDifficulty.hard:
            colors = [card.color for card in cards]
            self.data.current_card.color = max(set(colors), key=colors.count)
        else:
            self.data.current_card.color = choice(cards).color

        return _("I choice {color}.").format(color=self.data.current_card.color.word)

    def get_cards(self) -> tuple:
        def get():
            for card in self.data.users[bot_id].cards:
                accept, decline = self.data.filter_card(bot_id, card)
                if accept:
                    yield card, accept

        bot_id = self.state.bot.id

        if bot_id in self.data.users:
            yield from get()

    async def gen_turn(self, cards: tuple | None):
        async with ChatActionSender.choose_sticker(chat_id=self.message.chat.id):
            m = len(self.data.users) * self.data.settings.difficulty
            await asyncio.sleep(choice(range(1, 6)) / m)

            self.data: UnoData = await UnoData.get(self.state)

            try:
                if cards:
                    self.data.current_card, accept = choice(cards)
                    print(accept)
                    self.message = await self.message.answer_sticker(self.data.current_card.file_id)

                    try:
                        answer = choice(
                            (
                                _("My move is made."),
                                _("Expected? But I don't care."),
                                _("BA-DUM-TSS!"),
                                _(
                                    "On a scale of 10, rate the quality of this move.\n"
                                    "Where 0 is very good, 10 is excellent."
                                ),
                                _("I still have cards in my hand."),
                                _("Curious, but I know all the hands in the game... I dealt them."),
                                _("Maybe I can even win this game!"),
                                _("Oh, I don't envy the next player..."),
                                _("Br-b. Ah. Yes. No. ..."),
                                _("Oh-oh, this card fell into this chat by itself..."),
                            )
                        )

                        from .core import pre
                        await pre(self.message, self.state, self.data, answer)

                    except asyncio.CancelledError:
                        await self.message.delete()

                        self.data: UnoData = await UnoData.get(self.state)

                        answer = self.data.pick_card(self.message.from_user)
                        await self.data.update(self.state)

                        await self.message.answer(answer)

                else:
                    from .core import proceed_pass
                    await proceed_pass(self.message, self.state, self.data)

            except exceptions.TelegramRetryAfter as retry:
                await asyncio.sleep(retry.retry_after)
                self.message = await retry.method

    async def gen_uno(self):
        async with ChatActionSender.typing(chat_id=self.message.chat.id):
            try:
                m = len(self.data.users) * self.data.settings.difficulty
                user = await self.state.bot.get_me()

                if self.message.entities[0].user.id == self.state.bot.id:
                    timeout = range(0, 4)
                else:
                    timeout = range(1, 8)

                await asyncio.sleep(choice(timeout) / m)

            except asyncio.CancelledError:
                if self.message.reply_markup:
                    await self.message.delete_reply_markup()

            try:
                self.data: UnoData = await UnoData.get(self.state)

                from .core import proceed_uno
                self.message = await proceed_uno(self.message, self.state, self.data, user)

            except exceptions.TelegramRetryAfter as retry:
                await asyncio.sleep(retry.retry_after)
                self.message = await retry.method

    async def gen_poll(self, user: types.User):
        try:
            await asyncio.sleep(60)

        except asyncio.CancelledError:
            poll = await self.state.bot.stop_poll(self.message.chat.id, self.message.message_id)
            data_uno: UnoData = await UnoData.get(self.state)

            if poll.options[0].voter_count > poll.options[1].voter_count and user.id in data_uno.users:
                from .core import kick_for_idle
                await kick_for_idle(self.message, self.state, data_uno, user)

        finally:
            await self.message.delete()
