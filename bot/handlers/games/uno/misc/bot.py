import asyncio
from random import choice, random

from aiogram import types, exceptions
from aiogram.fsm.context import FSMContext
from aiogram.utils.chat_action import ChatActionSender
from aiogram.utils.i18n import gettext as _

from .cards import UnoColors
from .data import UnoData
from ..settings import UnoDifficulty

UNO = "UNO!"


class UnoBot:
    def __init__(self, message: types.Message, state: FSMContext, data: UnoData):
        self.message: types.Message = message
        self.state: FSMContext = state

        self.data: UnoData = data

    def get_cards(self):
        cards = self.data.users.get(self.state.bot.id, [])

        for card in cards:
            accept, decline = self.data.filter_card(self.state.bot.id, card)
            if accept:
                yield card, accept

    async def gen_turn(self, cards: tuple | None):
        async with ChatActionSender.choose_sticker(chat_id=self.message.chat.id):
            m = len(self.data.users) * self.data.settings.difficulty
            await asyncio.sleep(choice(range(1, 6)) / m)

            if cards:
                self.data.current_card, accept = choice(cards)

                try:
                    self.message = await self.state.bot.send_sticker(
                        self.state.key.chat_id,
                        self.data.current_card.file_id,
                    )

                except exceptions.TelegramRetryAfter as retry:
                    await asyncio.sleep(retry.retry_after)
                    self.message = await retry.method

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

                    self.data.update_turn(self.message.from_user.id)
                    await self.proceed_turn(answer)

                except asyncio.CancelledError:
                    await self.message.delete()

                    self.data: UnoData = await UnoData.get_data(self.state)

                    answer = self.data.pick_card(self.message.from_user)
                    await self.data.set_data(self.state)

                    await self.message.answer(answer)

            else:
                await self.proceed_pass()

    async def proceed_turn(self, answer: str = ""):
        answer = self.data.update_state() or answer

        if self.data.current_card.color is UnoColors.black:
            await self.gen_color()

        elif self.data.current_state.seven:
            await self.gen_seven()

        from .process import proceed_turn
        await proceed_turn(self.message, self.state, self.data, answer)

    async def proceed_pass(self):
        if self.data.current_state.bluffed:
            m = self.data.settings.difficulty
            n = 0.5

            if self.data.settings.difficulty is UnoDifficulty.normal:
                m /= len(self.data.users[self.data.prev_user_id]) or n
            elif self.data.settings.difficulty is UnoDifficulty.hard:
                m /= len(
                    [
                        card for card in self.data.users[self.data.prev_user_id] if
                        card.color is self.data.deck[-2].color
                    ]
                ) or n

            if random() < 1 / m:
                answer = await self.data.play_bluff(self.state)

                from .process import next_turn
                return await next_turn(self.message, self.state, self.data, answer)

        self.data.current_state.passed = self.state.bot.id
        answer = self.data.play_draw(self.data.current_state.passed)

        from .process import next_turn
        await next_turn(self.message, self.state, self.data, answer)

    async def gen_color(self):
        cards = self.data.users[self.state.bot.id]

        if self.data.settings.difficulty is UnoDifficulty.hard:
            colors = [card.color for card in cards]
            self.data.current_card.color = max(set(colors), key=colors.count)
        else:
            self.data.current_card.color = choice(cards).color

        await self.message.answer(_("I choice {color}.").format(color=self.data.current_card.color.word))

    async def gen_seven(self):
        seven_user_id = choice([user_id for user_id in self.data.users if user_id != self.state.bot.id])
        seven_user = await self.data.get_user(self.state, seven_user_id)

        await self.message.answer(self.data.play_seven(self.message.from_user, seven_user))

    async def gen_uno(self):
        try:
            async with ChatActionSender.typing(chat_id=self.message.chat.id):
                m = len(self.data.users) * self.data.settings.difficulty

                if self.message.entities[0].user.id == self.state.bot.id:
                    timeout = range(0, 4)
                else:
                    timeout = range(1, 8)

                await asyncio.sleep(choice(timeout) / m)

                user = await self.state.bot.me()
                self.data: UnoData = await UnoData.get_data(self.state)

                from .process import proceed_uno
                await proceed_uno(self.message, self.state, self.data, user)

        except exceptions.TelegramRetryAfter as retry:
            await asyncio.sleep(retry.retry_after)
            await retry.method

        finally:
            await self.message.delete_reply_markup()

    @staticmethod
    async def gen_poll(message: types.Message, state: FSMContext, user: types.User):
        poll = await state.bot.stop_poll(state.key.chat_id, message.message_id)
        data_uno: UnoData = await UnoData.get_data(state)

        if poll.options[0].voter_count > poll.options[1].voter_count and user.id in data_uno.users:
            from .process import kick_for_idle
            await kick_for_idle(message, state, data_uno, user)

        await message.delete()
