import asyncio
from random import choice, random, randint

from aiogram import types, exceptions
from aiogram.fsm.context import FSMContext
from aiogram.utils.chat_action import ChatActionSender
from aiogram.utils.i18n import gettext as _

from .cards import UnoColors, UnoEmoji
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
            m = self.data.settings.difficulty / len(self.data.users)
            await asyncio.sleep(randint(1, 4) * m)

            if cards:
                self.data.current_card, accept = choice(cards)

                if self.data.current_user_id != self.state.bot.id:
                    await self.message.delete()

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

                    answer = self.data.pick_card(self.state.bot.id)
                    await self.data.set_data(self.state)

                    await self.message.answer(answer)

            else:
                await self.proceed_pass()

    async def proceed_turn(self, answer: str = ""):
        answer = self.data.update_state() or answer

        if self.data.current_card.color is UnoColors.BLACK:
            await self.gen_color()

        elif self.data.current_state.seven:
            await self.gen_seven()

        from .process import proceed_turn
        await proceed_turn(self.message, self.state, self.data, answer)

    async def proceed_pass(self):
        from .process import next_turn

        if self.data.current_card.emoji == UnoEmoji.DRAW_FOUR:
            m = self.data.settings.difficulty
            cards = self.data.users[self.data.prev_user_id]

            if self.data.settings.difficulty is UnoDifficulty.HARD:
                m *= len([card for card in cards if card.color is self.data.deck[-2].color]) / 4
            else:
                m *= len(cards) / 6

            if random() < 1 / (m or 5):
                answer = await self.data.play_bluff(self.state)
                return await next_turn(self.message, self.state, self.data, answer)

        answer = self.data.play_draw(self.state.bot.id)
        await next_turn(self.message, self.state, self.data, answer)

    async def gen_color(self):
        cards = self.data.users[self.state.bot.id]

        if not cards:
            self.data.current_card.color = choice(tuple(UnoColors.get_colors(exclude={UnoColors.BLACK})))

        elif self.data.settings.difficulty is UnoDifficulty.HARD:
            colors = [card.color for card in cards]
            self.data.current_card.color = max(set(colors), key=colors.count)

        else:
            self.data.current_card.color = choice(cards).color

        await self.message.answer(_("I choice {color}.").format(color=self.data.current_card.color.word))

    async def gen_seven(self):
        seven_user_id = choice([user_id for user_id in self.data.users if user_id != self.state.bot.id])
        seven_user = await self.data.get_user(self.state, seven_user_id)

        await self.message.answer(self.data.play_seven(self.message.from_user, seven_user))

    @staticmethod
    async def gen_uno(message: types.Message, state: FSMContext, data: UnoData):
        try:
            async with ChatActionSender.typing(chat_id=message.chat.id):
                m = data.settings.difficulty / len(data.users)

                if message.entities[0].user.id == state.bot.id:
                    timeout = 0, 4
                else:
                    timeout = 2, 6

                await asyncio.sleep(randint(*timeout) * m)

                user = await state.bot.me()
                data: UnoData = await UnoData.get_data(state)

                from .process import proceed_uno
                await proceed_uno(message, state, data, user)

        except exceptions.TelegramRetryAfter as retry:
            await asyncio.sleep(retry.retry_after)
            await retry.method

        finally:
            await message.delete_reply_markup()

    @staticmethod
    async def gen_poll(message: types.Message, state: FSMContext, user: types.User):
        poll = await state.bot.stop_poll(state.key.chat_id, message.message_id)
        data_uno: UnoData = await UnoData.get_data(state)

        if poll.options[0].voter_count > poll.options[1].voter_count and user.id in data_uno.users:
            from .process import kick_for_idle
            await kick_for_idle(message, state, data_uno, user)

        await message.delete()
